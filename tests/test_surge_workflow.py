"""
test_gap2_gap3.py
------------------
Unit test suite for:
  Gap 2 -- Patient History Not Used in Scoring
  Gap 3 -- Surge Mode Changes Volume, Not Behavior

Gap 2 design principle:
  History adjusts the *informative* EWS sub-score only (upward or downward,
  bounded by +/-1 point) and the red-flag override thresholds for a small,
  explainable set of chronic conditions. It NEVER touches the universal
  red flags (SpO2 < 90 default floor, AVPU != Alert), and zero-history /
  no-documented-baseline patients are scored identically to before Gap 2.

Gap 3 design principle:
  Safe-wait ceilings tighten under surge for Acuity 3-5 only (Acuity 1-2
  are unchanged); the surge factor is computed live from queue length; and
  the Charge Nurse board's effective-urgency ranking can reorder patients
  at the same acuity based on wait time and confidence.
"""

import pytest
from patient_triage.core.engine import (
    Vitals, score_patient, _red_flags, _baseline_adjusted_score,
    compute_surge_factor, safe_wait_minutes, wait_breach, effective_urgency,
    SAFE_WAIT_MINUTES, NORMAL_CAPACITY, CHRONIC_CONDITION_MODIFIERS,
)


# ==============================================================================
# GAP 2 -- baseline-relative re-scoring
# ==============================================================================

class TestBaselineAdjustedScore:

    def test_near_baseline_eases_abnormal_score_down(self):
        """A population-abnormal value within 10% of the patient's own
        baseline should ease down by one point (known-abnormal-for-them)."""
        reasons = []
        adjusted = _baseline_adjusted_score("HR", 105, 100, sub_score=1,
                                            reasons=reasons, worse_direction="high")
        assert adjusted == 0
        assert reasons  # explanatory reason recorded

    def test_near_baseline_never_goes_negative(self):
        reasons = []
        adjusted = _baseline_adjusted_score("HR", 101, 100, sub_score=0,
                                            reasons=reasons, worse_direction="high")
        assert adjusted == 0

    def test_far_from_baseline_no_change_when_already_abnormal(self):
        """If the value is nowhere near baseline, the population-based
        abnormal score is left as-is (no unwarranted easing)."""
        reasons = []
        adjusted = _baseline_adjusted_score("HR", 160, 100, sub_score=2,
                                            reasons=reasons, worse_direction="high")
        assert adjusted == 2

    def test_notable_deviation_bumps_normal_score_up(self):
        """Population-normal value that is >=20% off the patient's own
        baseline (in the concerning direction) is flagged for awareness."""
        reasons = []
        adjusted = _baseline_adjusted_score("HR", 78, 60, sub_score=0,
                                            reasons=reasons, worse_direction="high")
        assert adjusted == 1
        assert reasons

    def test_deviation_in_safe_direction_not_flagged(self):
        """HR notably *below* baseline is not 'worse' for the 'high' direction
        (e.g. a resting athlete's HR dropping further isn't a red flag)."""
        reasons = []
        adjusted = _baseline_adjusted_score("HR", 40, 60, sub_score=0,
                                            reasons=reasons, worse_direction="high")
        assert adjusted == 0

    def test_low_direction_sbp_notable_drop_bumps_up(self):
        reasons = []
        adjusted = _baseline_adjusted_score("SBP", 100, 140, sub_score=0,
                                            reasons=reasons, worse_direction="low")
        assert adjusted == 1

    def test_no_baseline_is_a_no_op(self):
        reasons = []
        adjusted = _baseline_adjusted_score("HR", 150, None, sub_score=3,
                                            reasons=reasons, worse_direction="high")
        assert adjusted == 3
        assert reasons == []

    def test_missing_current_value_is_a_no_op(self):
        reasons = []
        adjusted = _baseline_adjusted_score("HR", None, 100, sub_score=0,
                                            reasons=reasons, worse_direction="high")
        assert adjusted == 0
        assert reasons == []


class TestChronicConditionRedFlagModifiers:

    def test_copd_lowers_spo2_floor(self):
        """COPD-documented patient at SpO2 88 should NOT trigger the
        universal hypoxia flag (their chronic baseline is lower); a
        non-COPD patient at the same SpO2 DOES trigger it."""
        v = Vitals(hr=90, rr=18, spo2=88, sbp=120, temp=37.0, avpu="A")
        no_history_flags = _red_flags("adult", v)
        copd_flags = _red_flags("adult", v, chronic_conditions=["COPD"])
        assert any("hypoxia" in f.lower() for f in no_history_flags)
        assert not any("hypoxia" in f.lower() for f in copd_flags)

    def test_copd_still_flags_genuine_further_deterioration(self):
        """The floor is lowered, not removed -- true deterioration below
        the adjusted floor still fires."""
        v = Vitals(hr=90, rr=18, spo2=80, sbp=120, temp=37.0, avpu="A")
        flags = _red_flags("adult", v, chronic_conditions=["COPD"])
        assert any("hypoxia" in f.lower() for f in flags)

    def test_cardiac_lowers_hr_ceiling(self):
        """A known-cardiac patient at HR 115 should trigger the tachycardia
        red flag (adjusted ceiling ~110), while a patient with no cardiac
        history at the same HR should not (adult ceiling is 131)."""
        v = Vitals(hr=115, rr=18, spo2=98, sbp=120, temp=37.0, avpu="A")
        no_history_flags = _red_flags("adult", v)
        cardiac_flags = _red_flags("adult", v, chronic_conditions=["cardiac"])
        assert not any("tachycardia" in f.lower() for f in no_history_flags)
        assert any("tachycardia" in f.lower() for f in cardiac_flags)

    def test_unknown_chronic_condition_is_a_no_op(self):
        v = Vitals(hr=90, rr=18, spo2=95, sbp=120, temp=37.0, avpu="A")
        flags = _red_flags("adult", v, chronic_conditions=["diabetes"])
        assert flags == []

    def test_no_chronic_conditions_matches_pre_gap2_behavior(self):
        v = Vitals(hr=90, rr=18, spo2=95, sbp=120, temp=37.0, avpu="A")
        assert _red_flags("adult", v, chronic_conditions=None) == _red_flags("adult", v)


class TestScorePatientWithHistory:

    def test_zero_history_patient_unaffected(self):
        """No history object at all -> identical result to calling without
        the `history` kwarg (Gap 2 must not change default behavior)."""
        v = Vitals(hr=105, rr=18, spo2=96, sbp=120, temp=37.0, avpu="A")
        baseline = score_patient(50, v, "abdominal pain")
        explicit_none = score_patient(50, v, "abdominal pain", history=None)
        assert baseline.acuity == explicit_none.acuity
        assert baseline.ews_score == explicit_none.ews_score

    def test_history_never_relaxes_a_universal_red_flag(self):
        """SpO2 < the (possibly-adjusted) floor and altered consciousness
        must still escalate acuity even with a documented baseline."""
        v = Vitals(hr=90, rr=18, spo2=80, sbp=120, temp=37.0, avpu="V")
        res = score_patient(50, v, "", history={
            "baseline_hr": 90, "baseline_sbp": 120,
            "chronic_conditions": ["COPD"],
            "last_visit_acuity": 4, "last_visit_date": "2026-01-01",
        })
        assert res.acuity == 1
        assert res.red_flags

    def test_history_reasons_surfaced(self):
        v = Vitals(hr=105, rr=18, spo2=96, sbp=120, temp=37.0, avpu="A")
        res = score_patient(50, v, "", history={
            "baseline_hr": 100, "baseline_sbp": 120,
            "chronic_conditions": [],
            "last_visit_acuity": 4, "last_visit_date": "2026-03-01",
        })
        assert any("last visit" in r.lower() for r in res.reasons)

    def test_pediatric_history_path_also_supported(self):
        """Baseline adjustment applies on the pediatric scoring path too,
        not just NEWS2 adults."""
        v = Vitals(hr=118, rr=25, spo2=98, sbp=90, temp=37.0, avpu="A")
        no_hist = score_patient(8, v, "")
        with_hist = score_patient(8, v, "", history={
            "baseline_hr": 115, "baseline_sbp": 90,
            "chronic_conditions": [], "last_visit_acuity": 4,
            "last_visit_date": "2026-02-01",
        })
        assert with_hist.ews_score <= no_hist.ews_score


# ==============================================================================
# GAP 3 -- surge-adaptive workflow
# ==============================================================================

class TestSurgeFactor:

    def test_quiet_shift_factor_is_one(self):
        assert compute_surge_factor(NORMAL_CAPACITY) == 1.0

    def test_three_x_surge_factor(self):
        assert compute_surge_factor(NORMAL_CAPACITY * 3) == 3.0

    def test_zero_capacity_does_not_divide_by_zero(self):
        assert compute_surge_factor(10, capacity=0) == 0.0


class TestSafeWaitMinutes:

    def test_quiet_shift_matches_base_table(self):
        for acuity, minutes in SAFE_WAIT_MINUTES.items():
            assert safe_wait_minutes(acuity, surge_factor=1.0) == minutes

    def test_acuity_1_and_2_unaffected_by_surge(self):
        assert safe_wait_minutes(1, surge_factor=3.0) == SAFE_WAIT_MINUTES[1]
        assert safe_wait_minutes(2, surge_factor=3.0) == SAFE_WAIT_MINUTES[2]

    def test_acuity_4_tightens_from_60_to_40_at_3x(self):
        """The exact worked example from the Gap Closure Plan."""
        assert safe_wait_minutes(4, surge_factor=3.0) == 40

    def test_acuity_4_at_2x_between_quiet_and_3x(self):
        quiet = safe_wait_minutes(4, surge_factor=1.0)
        surge3x = safe_wait_minutes(4, surge_factor=3.0)
        surge2x = safe_wait_minutes(4, surge_factor=2.0)
        assert surge3x < surge2x < quiet

    def test_surge_beyond_3x_is_capped(self):
        assert safe_wait_minutes(4, surge_factor=5.0) == safe_wait_minutes(4, surge_factor=3.0)

    def test_wait_breach_uses_surge_adjusted_limit(self):
        assert not wait_breach(4, minutes_waited=45, surge_factor=1.0)
        assert wait_breach(4, minutes_waited=45, surge_factor=3.0)


class TestEffectiveUrgency:

    def test_higher_acuity_is_always_more_urgent_at_equal_wait(self):
        u1 = effective_urgency(1, minutes_waited=0, confidence_label="High")
        u3 = effective_urgency(3, minutes_waited=0, confidence_label="High")
        assert u1 < u3  # lower score = seen sooner

    def test_longer_wait_increases_urgency_within_same_acuity(self):
        short_wait = effective_urgency(3, minutes_waited=5, confidence_label="High")
        long_wait = effective_urgency(3, minutes_waited=60, confidence_label="High")
        assert long_wait < short_wait

    def test_low_confidence_can_surface_above_high_confidence_same_acuity(self):
        """A Low-confidence Acuity-3 patient who has waited less can still
        rank as more urgent than a High-confidence Acuity-3 patient who has
        waited longer, per the Gap Closure Plan's stated scenario."""
        low_conf_short_wait = effective_urgency(3, minutes_waited=5, confidence_label="Low")
        high_conf_longer_wait = effective_urgency(3, minutes_waited=10, confidence_label="High")
        assert low_conf_short_wait < high_conf_longer_wait
