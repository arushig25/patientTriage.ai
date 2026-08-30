"""
test_gap4_data_protection.py
-----------------------------
Unit test suite for Gap 4 -- Data Protection Is a Caption, Not a Mechanism.

Covers:
  - Encryption at rest (patients.csv and the audit log are never
    plaintext on disk; a locally-managed key round-trips correctly).
  - Pseudonymization (deterministic per patient_id, not reversible
    without the key, and re-linkable only through the RBAC-gated path).
  - Role-based access control (correct/incorrect/no password).
  - ACCESS event logging as its own event type.
  - Data-minimization documentation covers every collected field.

Each test runs in a fresh temp working directory so it never touches
(or is affected by) a real data/ folder from another test or a prior
`streamlit run`.
"""

import json
import os

import pytest

from patient_triage.security import audit
from patient_triage.security import privacy


@pytest.fixture(autouse=True)
def isolated_data_dir(tmp_path, monkeypatch):
    """Run every test with cwd pointed at an empty temp dir, so
    data/.privacy_key, data/audit_log.jsonl.enc, etc. never collide
    with a real run or with each other."""
    monkeypatch.chdir(tmp_path)
    yield


# ==============================================================================
# Encryption at rest
# ==============================================================================

class TestEncryptionAtRest:

    def test_key_is_generated_once_and_reused(self):
        k1 = privacy.get_or_create_key()
        k2 = privacy.get_or_create_key()
        assert k1 == k2
        assert os.path.exists(privacy.KEY_PATH)

    def test_write_encrypted_file_is_not_plaintext_on_disk(self):
        privacy.write_encrypted("data/secret.txt", "patient-identifying content")
        with open("data/secret.txt", "rb") as f:
            raw = f.read()
        assert b"patient-identifying" not in raw

    def test_write_then_read_encrypted_round_trips(self):
        privacy.write_encrypted("data/secret.txt", "hello world")
        assert privacy.read_encrypted("data/secret.txt") == "hello world"

    def test_read_encrypted_missing_file_returns_empty_string(self):
        assert privacy.read_encrypted("data/does_not_exist.enc") == ""

    def test_patients_csv_is_encrypted_at_rest(self):
        from patient_triage.data.simulator import write_csv, read_csv_decrypted
        path = write_csv("data/patients.csv")
        with open(path, "rb") as f:
            raw = f.read()
        assert b"patient_id" not in raw          # header not visible in plaintext
        assert b"A. Rivera" not in raw            # a real name not visible in plaintext
        rows = read_csv_decrypted(path)
        assert rows[0]["patient_id"] == "P01"
        assert rows[0]["name"] == "A. Rivera"

    def test_audit_log_file_is_encrypted_at_rest(self):
        audit.log_event("SCORE", "P01", {"acuity": 3})
        with open(audit.LOG_PATH, "rb") as f:
            raw = f.read()
        assert b"P01" not in raw                 # patient_id not visible in plaintext
        assert b"SCORE" not in raw                # event_type not visible in plaintext
        entries = audit.read_log()
        assert entries[0]["event_type"] == "SCORE"


# ==============================================================================
# Pseudonymization
# ==============================================================================

class TestPseudonymization:

    def test_same_patient_id_always_maps_to_same_token(self):
        assert privacy.pseudonymize("P07") == privacy.pseudonymize("P07")

    def test_different_patient_ids_map_to_different_tokens(self):
        assert privacy.pseudonymize("P07") != privacy.pseudonymize("P08")

    def test_token_does_not_contain_raw_patient_id(self):
        token = privacy.pseudonymize("P07")
        assert "P07" not in token

    def test_audit_log_stores_pseudonym_not_raw_patient_id(self):
        audit.log_event("SCORE", "P07", {"acuity": 2})
        entry = audit.read_log()[0]
        assert entry["patient_id"] != "P07"
        assert entry["patient_id"] == privacy.pseudonymize("P07")

    def test_system_subject_is_never_pseudonymized(self):
        audit.log_event("SURGE_MODE_ON", "SYSTEM", {"surge_factor": 3.0})
        entry = audit.read_log()[0]
        assert entry["patient_id"] == "SYSTEM"


# ==============================================================================
# Role-based access control + identity re-link
# ==============================================================================

class TestRBAC:

    def test_correct_password_grants_access(self):
        assert privacy.check_role_access("Clinical Lead", "triage-lead-2026") is True

    def test_wrong_password_denies_access(self):
        assert privacy.check_role_access("Clinical Lead", "wrong-password") is False

    def test_empty_password_denies_access(self):
        assert privacy.check_role_access("Clinical Lead", "") is False

    def test_role_with_no_restriction_passes_through(self):
        assert privacy.check_role_access("Triage Nurse", "") is True

    def test_resolve_identity_succeeds_with_correct_password(self):
        audit.log_event("SCORE", "P07", {"acuity": 2})
        token = audit.read_log()[0]["patient_id"]
        assert audit.resolve_identity(token, "Clinical Lead", "triage-lead-2026") == "P07"

    def test_resolve_identity_fails_closed_with_wrong_password(self):
        audit.log_event("SCORE", "P07", {"acuity": 2})
        token = audit.read_log()[0]["patient_id"]
        resolved = audit.resolve_identity(token, "Clinical Lead", "wrong-password")
        assert resolved == token   # unchanged, not the real patient_id
        assert resolved != "P07"


# ==============================================================================
# ACCESS event logging
# ==============================================================================

class TestAccessLogging:

    def test_access_event_is_its_own_event_type(self):
        audit.log_event("ACCESS", "P01", {"fields": ["name", "vitals"],
                                               "viewer_role": "Triage Nurse"})
        entries = audit.read_log()
        assert entries[0]["event_type"] == "ACCESS"
        assert entries[0]["payload"]["fields"] == ["name", "vitals"]

    def test_should_log_access_only_fires_on_patient_change(self):
        state = {}
        assert audit.should_log_access(state, "P01") is True
        assert audit.should_log_access(state, "P01") is False   # same patient, rerun
        assert audit.should_log_access(state, "P02") is True    # different patient


# ==============================================================================
# Data minimization documentation
# ==============================================================================

class TestDataMinimization:

    def test_every_collected_field_has_a_minimization_entry(self):
        for field in ("patient_id", "name", "age", "vitals", "complaint",
                       "history", "audit_log"):
            assert field in privacy.FIELD_MINIMIZATION
            purpose, retention = privacy.FIELD_MINIMIZATION[field]
            assert purpose and retention
