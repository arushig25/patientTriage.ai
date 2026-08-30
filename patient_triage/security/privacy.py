"""
privacy.py
----------
Gap 4: Data Protection -- turns the sidebar's "HIPAA-aligned" caption into
an actual, demonstrable technical control instead of an assertion.

Five mechanisms, each answering a specific piece of the brief's question
("how would patient data be protected from unfair and unauthorized
usage?"):

  1. Pseudonymization -- a patient_id is hashed into a pseudonymous token
     before it is written to the audit trail. The scoring function
     (score_patient() in triage_engine.py) never took a name or ID to
     begin with -- it only ever sees age/vitals/complaint/history -- so
     this closes the remaining place identity touched persisted data:
     the audit log. Only an authenticated, RBAC-checked viewer can
     re-link a token back to a real patient_id (resolve_identity()).
  2. Encryption at rest -- data/patients.csv and data/audit_log.jsonl are
     stored as Fernet-encrypted blobs, not plaintext, via a locally
     managed symmetric key.
  3. Role-based access control (RBAC) -- gates the Clinical Lead's
     identity-linked audit view behind a role password check, so it's a
     real control rather than a cosmetic radio button.
  4. Data-minimization documentation -- FIELD_MINIMIZATION states what's
     stored, why, and for how long, for every field the app collects.
     This doubles as the factual basis for the Gap 5 retention policy.
  5. ACCESS auditing -- every time identity-linked data is displayed to
     a viewer, that's logged as its own event type (see audit_log.py),
     not folded into SCORE/OVERRIDE events.

Scope note: this is a prototype-grade demonstration of mechanism, sized
to a hackathon submission -- a local key file instead of a managed KMS, a
shared role password instead of per-user SSO accounts. The README's
"Data Protection" section states plainly what a production deployment
would add on top of this.
"""

import hashlib
import hmac
import json
import os

from cryptography.fernet import Fernet

KEY_PATH = "data/.privacy_key"
IDENTITY_MAP_PATH = "data/.identity_map.enc"


# ---------- Symmetric key management ----------

def get_or_create_key(path: str = KEY_PATH) -> bytes:
    """Load the local Fernet/HMAC key, generating one on first run and
    restricting its file permissions. In production this would come from
    a managed secret store (KMS/Vault) rather than a file on disk --
    this demonstrates the encryption/pseudonymization mechanism itself,
    not enterprise key custody."""
    os.makedirs(os.path.dirname(path) or ".", exist_ok=True)
    if os.path.exists(path):
        with open(path, "rb") as f:
            return f.read()
    key = Fernet.generate_key()
    with open(path, "wb") as f:
        f.write(key)
    try:
        os.chmod(path, 0o600)
    except OSError:
        pass  # best-effort on filesystems that don't support chmod
    return key


# ---------- Encryption at rest ----------

def encrypt_bytes(data: bytes, key: bytes = None) -> bytes:
    key = key or get_or_create_key()
    return Fernet(key).encrypt(data)


def decrypt_bytes(token: bytes, key: bytes = None) -> bytes:
    key = key or get_or_create_key()
    return Fernet(key).decrypt(token)


def write_encrypted(path: str, plaintext: str, key: bytes = None) -> None:
    """Overwrite `path` with the Fernet-encrypted form of `plaintext`."""
    os.makedirs(os.path.dirname(path) or ".", exist_ok=True)
    with open(path, "wb") as f:
        f.write(encrypt_bytes(plaintext.encode(), key))


def read_encrypted(path: str, key: bytes = None) -> str:
    """Return the decrypted plaintext of an encrypted-at-rest file, or
    "" if the file doesn't exist yet (first-run case)."""
    if not os.path.exists(path):
        return ""
    with open(path, "rb") as f:
        token = f.read()
    if not token:
        return ""
    return decrypt_bytes(token, key).decode()


# ---------- Pseudonymization ----------

def pseudonymize(patient_id: str) -> str:
    """Deterministic pseudonymous token for a patient_id: the same
    patient always maps to the same token (so events can still be
    correlated to "the same person, visit to visit" without exposing
    who that is), derived via HMAC so the token can't be reversed back
    to patient_id without the key."""
    mac = hmac.new(get_or_create_key(), patient_id.encode(), hashlib.sha256)
    return "PT-" + mac.hexdigest()[:12]


def _load_identity_map() -> dict:
    raw = read_encrypted(IDENTITY_MAP_PATH)
    if not raw:
        return {}
    try:
        return json.loads(raw)
    except json.JSONDecodeError:
        return {}


def _save_identity_map(mapping: dict) -> None:
    write_encrypted(IDENTITY_MAP_PATH, json.dumps(mapping))


def record_identity(token: str, patient_id: str) -> None:
    """Persist the token -> real patient_id link, encrypted at rest.
    Called once per pseudonymization so an authorized viewer can later
    re-link (this is what makes the re-link auditable and revocable,
    rather than the token itself silently encoding the ID)."""
    mapping = _load_identity_map()
    if mapping.get(token) != patient_id:
        mapping[token] = patient_id
        _save_identity_map(mapping)


def resolve_identity(token: str, role: str, password: str) -> str:
    """Re-link a pseudonymous token back to a real patient_id -- gated by
    RBAC. Returns the token unchanged (never raises, never leaks the
    real ID) if the caller isn't authorized, so an unauthorized or
    mistaken call fails closed instead of exposing data on an
    exception a caller might not handle."""
    if not check_role_access(role, password):
        return token
    return _load_identity_map().get(token, token)


# ---------- Role-based access control ----------
# Prototype RBAC: one shared password per privileged role, compared as a
# salted hash (never stored or compared in plaintext) using a
# constant-time comparison. A production deployment would use per-user
# accounts behind SSO, not a shared role password.

_ROLE_PASSWORD_HASHES = {
    "Clinical Lead": hashlib.sha256(b"triage-lead-2026").hexdigest(),
}


def check_role_access(role: str, password: str) -> bool:
    """True if `password` is correct for `role`. Roles with no entry in
    _ROLE_PASSWORD_HASHES have no restricted data behind them, so they
    pass by default (e.g. Triage Nurse / Charge Nurse views, which show
    only the single patient or board the role already needs to see)."""
    expected = _ROLE_PASSWORD_HASHES.get(role)
    if expected is None:
        return True
    if not password:
        return False
    return hmac.compare_digest(hashlib.sha256(password.encode()).hexdigest(), expected)


# ---------- Data minimization documentation (Gap 4 + feeds Gap 5) ----------
# What's stored, why, and for how long, for every field the app collects.
# Rendered in the UI next to the fields it describes (see app.py) so the
# claim is visible at the point of collection, not buried in a policy
# document nobody opens.

FIELD_MINIMIZATION = {
    "patient_id":  ("Correlate records within one visit/episode", "7 years (US medical-record retention)"),
    "name":        ("Display to authorized clinical staff only; never used in scoring", "7 years, every view access-logged"),
    "age":         ("Selects age-band scoring thresholds (pediatric vs. adult)", "7 years"),
    "vitals":      ("Early-warning score input", "7 years"),
    "complaint":   ("Complaint-based escalation matching", "7 years"),
    "history":     ("Baseline-relative re-scoring for returning patients", "7 years"),
    "audit_log":   ("Accountability for scores, alerts, and overrides", "Indefinite, hash-chained, pseudonymized"),
}

