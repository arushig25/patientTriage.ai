"""
test_gap6_gap7.py
------------------
Unit test suite for:
  Gap 6 -- Brittle Exact-String Complaint Matching
  Gap 7 -- Audit Log Floods on Every UI Rerun

Gap 6 design principle:
  High-risk complaints are matched by normalized keyword containment
  against a reviewable synonym map (HIGH_RISK_COMPLAINTS), not exact
  full-string equality -- so ordinary wording differences ("difficulty
  breathing" vs. "shortness of breath") still escalate.

Gap 7 design principle:
  should_log_score() / should_log_alert() / should_log_access() are the
  pure decision functions app.py consults before writing to the audit
  log, so a Streamlit rerun that doesn't represent a new clinical event
  doesn't produce a new log entry. They operate on a plain dict-like
  session store, so they're testable without a running Streamlit app.
"""

import pytest

from triage_engine import (
    Vitals, score_patient, _match_high_risk_complaint, _normalize_complaint,
    HIGH_RISK_COMPLAINTS,
)
import audit_log


# ==============================================================================
# GAP 6 -- complaint normalization and matching
# ==============================================================================

class TestNormalizeComplaint:

    def test_lowercases(self):
        assert _normalize_complaint("Chest Pain") == "chest pain"

    def test_strips_punctuation(self):
        assert _normalize_complaint("can't breathe!") == "can t breathe"

    def test_collapses_whitespace(self):
        assert _normalize_complaint("chest   pain") == "chest pain"


class TestMatchHighRiskComplaint:

    def test_exact_canonical_phrase_still_matches(self):
        category, phrase = _match_high_risk_complaint("chest pain")
        assert category == "CHEST_PAIN"

    def test_synonym_not_in_original_flat_set_now_matches(self):
        """This is the exact failure the gap plan calls out: 'difficulty
        breathing' did not match the old flat HIGH_RISK_COMPLAINTS set,
        which only contained 'shortness of breath'."""
        category, phrase = _match_high_risk_complaint("difficulty breathing")
        assert category == "RESPIRATORY_DISTRESS"

    def test_keyword_containment_within_a_longer_sentence(self):
        category, _ = _match_high_risk_complaint("Patient reports chest pain since this morning")
        assert category == "CHEST_PAIN"

    def test_case_and_punctuation_insensitive(self):
        category, _ = _match_high_risk_complaint("Can't Breathe!!")
        assert category == "RESPIRATORY_DISTRESS"

    def test_no_match_returns_none(self):
        category, phrase = _match_high_risk_complaint("ankle sprain")
        assert category is None
        assert phrase is None

    def test_empty_complaint_returns_none(self):
        assert _match_high_risk_complaint("") == (None, None)
        assert _match_high_risk_complaint(None) == (None, None)

    def test_every_category_has_at_least_two_phrasings(self):
        """A category with only one phrasing is exactly the brittleness
        this gap closes -- guard against regressing to that."""
        for category, phrases in HIGH_RISK_COMPLAINTS.items():
            assert len(phrases) >= 2, category


class TestComplaintEscalationIntegration:

    def test_p19_style_case_now_escalates_on_synonym(self):
        """P19 (S. Lopez, age 9): normal-for-age vitals (HR 130, RR 28)
        but complaint 'difficulty breathing' -- Gap 1 already fixed the
        red-flag false-positive; Gap 6 makes sure the complaint-based
        floor of acuity 2 actually fires for this exact wording."""
        vitals = Vitals(hr=130, rr=28, spo2=93, sbp=105, temp=38.6, avpu="A")
        result = score_patient(9, vitals, "difficulty breathing")
        assert result.acuity <= 2
        assert any("RESPIRATORY_DISTRESS" in r for r in result.reasons)

    def test_reasons_surface_the_matched_category(self):
        vitals = Vitals(hr=84, rr=18, spo2=97, sbp=120, temp=37.0, avpu="A")
        result = score_patient(35, vitals, "chest pain")
        assert result.acuity <= 2
        assert any("CHEST_PAIN" in r for r in result.reasons)

    def test_non_high_risk_complaint_does_not_force_low_acuity(self):
        vitals = Vitals(hr=72, rr=14, spo2=99, sbp=118, temp=36.8, avpu="A")
        result = score_patient(41, vitals, "ankle sprain")
        assert result.acuity >= 4


# ==============================================================================
# GAP 7 -- discrete-event audit logging
# ==============================================================================

class TestShouldLogScore:

    def test_first_score_for_a_patient_logs(self):
        state = {}
        assert audit_log.should_log_score(state, "P01", 3) is True

    def test_identical_rerun_does_not_relog(self):
        state = {}
        audit_log.should_log_score(state, "P01", 3)
        assert audit_log.should_log_score(state, "P01", 3) is False

    def test_acuity_change_for_same_patient_relogs(self):
        state = {}
        audit_log.should_log_score(state, "P01", 3)
        assert audit_log.should_log_score(state, "P01", 2) is True

    def test_switching_patient_relogs(self):
        state = {}
        audit_log.should_log_score(state, "P01", 3)
        assert audit_log.should_log_score(state, "P02", 3) is True

    def test_many_reruns_of_same_outcome_log_exactly_once(self):
        state = {}
        fires = [audit_log.should_log_score(state, "P01", 4) for _ in range(10)]
        assert fires == [True] + [False] * 9


class TestShouldLogAlert:

    def test_transition_into_breach_logs(self):
        state = {}
        assert audit_log.should_log_alert(state, "P05", True) is True

    def test_staying_breached_does_not_relog(self):
        state = {}
        audit_log.should_log_alert(state, "P05", True)
        assert audit_log.should_log_alert(state, "P05", True) is False
        assert audit_log.should_log_alert(state, "P05", True) is False

    def test_resolving_then_re_breaching_logs_again(self):
        state = {}
        audit_log.should_log_alert(state, "P05", True)    # breach starts
        audit_log.should_log_alert(state, "P05", False)   # resolved
        assert audit_log.should_log_alert(state, "P05", True) is True  # new breach

    def test_never_breached_never_logs(self):
        state = {}
        assert audit_log.should_log_alert(state, "P05", False) is False

    def test_independent_per_patient(self):
        state = {}
        assert audit_log.should_log_alert(state, "P01", True) is True
        assert audit_log.should_log_alert(state, "P02", True) is True
        assert audit_log.should_log_alert(state, "P01", True) is False
