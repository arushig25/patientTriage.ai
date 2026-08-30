"""
test_gap1_age_aware_red_flags.py
---------------------------------
Unit test suite for Gap 1: Age-Blind Red-Flag Overrides (Critical Safety Bug)

Objective:
  Verify that the red-flag override layer now correctly applies age-adjusted
  vital-sign thresholds, so a healthy child at the midpoint of their normal
  range never triggers a false-positive red flag, and a child with genuinely
  abnormal vitals is still caught.

Design principle:
  For each age band:
    1. Assert that vitals at the MIDPOINT of the normal range do NOT trigger
       red flags (this catches the false-positive bug).
    2. Assert that vitals at 2x the abnormal boundary DO trigger red flags
       (this ensures the safety override still works).
    3. Verify that universal flags (SpO2 < 90, AVPU != A) trigger at any age.
"""

import pytest
from triage_engine import (
    Vitals, age_band, score_patient, _red_flags,
    PEDS_NORMAL, RED_FLAG_THRESHOLDS,
)


# ==============================================================================
# TEST SUITE 1: Red flags for pediatric patients at NORMAL midpoint
# ==============================================================================

class TestPediatricsAtNormalMidpoint:
    """
    Healthy children in their normal vital range should NOT trigger red flags,
    even if one vital is slightly outside the strict normal band but still
    clinically normal.
    """

    def test_infant_normal_midpoint_no_red_flags(self):
        """1-month-old with textbook normal vitals: should NOT flag."""
        v = Vitals(hr=130, rr=45, spo2=98, sbp=70, temp=37.0, avpu="A")
        flags = _red_flags("infant", v)
        assert flags == [], f"Healthy infant flagged: {flags}"

    def test_young_child_normal_midpoint_no_red_flags(self):
        """3-year-old with normal vitals: should NOT flag."""
        v = Vitals(hr=120, rr=32, spo2=98, sbp=100, temp=37.0, avpu="A")
        flags = _red_flags("young_child", v)
        assert flags == [], f"Healthy young child flagged: {flags}"

    def test_child_normal_midpoint_no_red_flags(self):
        """
        9-year-old (S. Lopez from base dataset) with textbook-normal vitals
        for their age: HR 110, RR 28. This was the bug case—should NOT flag.
        """
        v = Vitals(hr=110, rr=28, spo2=93, sbp=105, temp=38.6, avpu="A")
        flags = _red_flags("child", v)
        assert flags == [], (
            f"9-year-old with normal vitals (HR=110, RR=28) incorrectly flagged: {flags}. "
            "This is the exact bug case from the gap plan."
        )

    def test_child_at_upper_normal_rr_no_red_flags(self):
        """RR 30 is at the top of normal for child; should NOT flag."""
        v = Vitals(hr=100, rr=30, spo2=97, sbp=100, temp=37.0, avpu="A")
        flags = _red_flags("child", v)
        assert flags == [], f"Child at upper-normal RR flagged: {flags}"

    def test_adolescent_normal_midpoint_no_red_flags(self):
        """14-year-old with normal vitals: should NOT flag."""
        v = Vitals(hr=80, rr=16, spo2=98, sbp=110, temp=36.8, avpu="A")
        flags = _red_flags("adolescent", v)
        assert flags == [], f"Healthy adolescent flagged: {flags}"

    def test_adult_normal_midpoint_no_red_flags(self):
        """Adult with normal vitals: should NOT flag."""
        v = Vitals(hr=70, rr=16, spo2=98, sbp=120, temp=37.0, avpu="A")
        flags = _red_flags("adult", v)
        assert flags == [], f"Healthy adult flagged: {flags}"


# ==============================================================================
# TEST SUITE 2: Red flags for GENUINELY ABNORMAL vitals at 2x boundary
# ==============================================================================

class TestAbnormalVitalsStillCaught:
    """
    The safety override must still catch genuinely abnormal vitals.
    This test ensures we didn't break the safety mechanism while fixing the
    false-positive bug.
    """

    def test_infant_severe_tachycardia_flagged(self):
        """Infant HR >> upper threshold should flag."""
        v = Vitals(hr=250, rr=45, spo2=98, sbp=70, temp=37.0, avpu="A")
        flags = _red_flags("infant", v)
        assert any("tachycardia" in f.lower() for f in flags), (
            f"Severe tachycardia in infant not caught: {flags}"
        )

    def test_young_child_severe_tachypnea_flagged(self):
        """Young child RR >> upper threshold should flag."""
        v = Vitals(hr=100, rr=80, spo2=98, sbp=100, temp=37.0, avpu="A")
        flags = _red_flags("young_child", v)
        assert any("respiratory" in f.lower() or "distress" in f.lower() for f in flags), (
            f"Severe tachypnea in young child not caught: {flags}"
        )

    def test_child_severe_bradypnea_flagged(self):
        """Child RR << lower threshold should flag."""
        v = Vitals(hr=100, rr=10, spo2=98, sbp=100, temp=37.0, avpu="A")
        flags = _red_flags("child", v)
        assert any("respiratory" in f.lower() or "distress" in f.lower() for f in flags), (
            f"Severe bradypnea in child not caught: {flags}"
        )

    def test_adolescent_hypotension_flagged(self):
        """Adolescent SBP at critical threshold should flag."""
        v = Vitals(hr=100, rr=16, spo2=98, sbp=75, temp=37.0, avpu="A")
        flags = _red_flags("adolescent", v)
        assert any("hypotension" in f.lower() for f in flags), (
            f"Hypotension in adolescent not caught: {flags}"
        )

    def test_adult_severe_tachycardia_flagged(self):
        """Adult HR >> threshold should flag."""
        v = Vitals(hr=150, rr=16, spo2=98, sbp=120, temp=37.0, avpu="A")
        flags = _red_flags("adult", v)
        assert any("tachycardia" in f.lower() for f in flags), (
            f"Severe tachycardia in adult not caught: {flags}"
        )


# ==============================================================================
# TEST SUITE 3: Universal red flags (should trigger at ANY age)
# ==============================================================================

class TestUniversalRedFlags:
    """
    SpO2 < 90% and altered mental status are danger signs at any age and
    should ALWAYS trigger a red flag.
    """

    def test_critical_hypoxia_flags_all_ages(self):
        """SpO2 < 90 should flag regardless of age band."""
        for band in ["infant", "young_child", "child", "adolescent", "adult", "geriatric"]:
            v = Vitals(hr=100, rr=20, spo2=88, sbp=100, temp=37.0, avpu="A")
            flags = _red_flags(band, v)
            assert any("hypoxia" in f.lower() for f in flags), (
                f"Critical hypoxia (SpO2=88) not flagged for {band}: {flags}"
            )

    def test_altered_consciousness_flags_all_ages(self):
        """AVPU != A should flag regardless of age band."""
        for band in ["infant", "young_child", "child", "adolescent", "adult", "geriatric"]:
            v = Vitals(hr=100, rr=20, spo2=98, sbp=100, temp=37.0, avpu="V")
            flags = _red_flags(band, v)
            assert any("mental status" in f.lower() or "alert" in f.lower() for f in flags), (
                f"Altered mental status (AVPU=V) not flagged for {band}: {flags}"
            )

    def test_spo2_at_boundary_flags(self):
        """SpO2 exactly at 90 should not flag, but 89 should."""
        v_boundary = Vitals(hr=100, rr=20, spo2=90, sbp=100, temp=37.0, avpu="A")
        flags_boundary = _red_flags("child", v_boundary)
        assert not any("hypoxia" in f.lower() for f in flags_boundary), (
            f"False positive at boundary (SpO2=90): {flags_boundary}"
        )
        
        v_critical = Vitals(hr=100, rr=20, spo2=89, sbp=100, temp=37.0, avpu="A")
        flags_critical = _red_flags("child", v_critical)
        assert any("hypoxia" in f.lower() for f in flags_critical), (
            f"Critical hypoxia (SpO2=89) not flagged: {flags_critical}"
        )


# ==============================================================================
# TEST SUITE 4: Integration with full score_patient() pathway
# ==============================================================================

class TestIntegrationWithScoring:
    """
    Verify the fix works end-to-end when called from score_patient().
    """

    def test_child_with_normal_vitals_no_escalation_from_red_flags(self):
        """
        9-year-old with normal vitals should NOT be escalated due to red flags.
        Previously would have been escalated to Acuity 2 due to false RR flag.
        """
        result = score_patient(age=9, vitals=Vitals(
            hr=110, rr=28, spo2=93, sbp=105, temp=38.6, avpu="A"
        ), complaint="")
        
        # Should have no red flags
        assert result.red_flags == [], (
            f"9-year-old with normal vitals has unexpected red flags: {result.red_flags}"
        )
        # Acuity should be based on EWS score alone, not escalated by false red flag
        assert result.acuity >= 3, (
            f"Expected acuity 3-5 for healthy child, got {result.acuity}. "
            f"Was it incorrectly escalated by a red flag?"
        )

    def test_adult_high_risk_complaint_still_escalates(self):
        """
        Adult with high-risk complaint should still be escalated properly
        (e.g., to Acuity 2), even after red-flag fix.
        """
        result = score_patient(age=35, vitals=Vitals(
            hr=84, rr=18, spo2=97, sbp=120, temp=37.0, avpu="A"
        ), complaint="chest pain")
        
        # High-risk complaint should escalate
        assert result.acuity <= 2, (
            f"High-risk complaint didn't escalate properly: acuity={result.acuity}"
        )

    def test_critically_ill_child_still_caught(self):
        """
        A critically ill child with multiple red flags should still be escalated to Acuity 1.
        """
        result = score_patient(age=6, vitals=Vitals(
            hr=200, rr=55, spo2=85, sbp=40, temp=39.5, avpu="P"
        ), complaint="")
        
        # Multiple red flags should escalate to Acuity 1
        assert result.acuity == 1, (
            f"Critically ill child not escalated to Acuity 1: acuity={result.acuity}, "
            f"flags={result.red_flags}"
        )


# ==============================================================================
# TEST SUITE 5: Boundary condition edge cases
# ==============================================================================

class TestBoundaryConditions:
    """
    Test edge cases around threshold boundaries to ensure clear, consistent behavior.
    """

    def test_child_rr_exactly_at_upper_normal_boundary(self):
        """RR = 30 is the upper limit of normal for child; should NOT flag."""
        v = Vitals(hr=100, rr=30, spo2=98, sbp=100, temp=37.0, avpu="A")
        flags = _red_flags("child", v)
        assert not any("respiratory" in f.lower() for f in flags), (
            f"RR at upper normal boundary (30) incorrectly flagged: {flags}"
        )

    def test_child_rr_above_threshold(self):
        """RR = 37 is above red-flag threshold (36) for child; SHOULD flag."""
        v = Vitals(hr=100, rr=37, spo2=98, sbp=100, temp=37.0, avpu="A")
        flags = _red_flags("child", v)
        assert any("respiratory" in f.lower() or "distress" in f.lower() for f in flags), (
            f"RR above threshold (37) should flag: {flags}"
        )

    def test_adolescent_hr_exactly_at_threshold(self):
        """HR = 140 is the adolescent threshold; should flag at this point."""
        v = Vitals(hr=140, rr=16, spo2=98, sbp=110, temp=37.0, avpu="A")
        flags = _red_flags("adolescent", v)
        assert any("tachycardia" in f.lower() for f in flags), (
            f"HR at tachycardia threshold (140) should flag: {flags}"
        )

    def test_adolescent_hr_below_threshold(self):
        """HR = 134 is just below threshold (135); should NOT flag."""
        v = Vitals(hr=134, rr=16, spo2=98, sbp=110, temp=37.0, avpu="A")
        flags = _red_flags("adolescent", v)
        assert not any("tachycardia" in f.lower() for f in flags), (
            f"HR below threshold (134) incorrectly flagged: {flags}"
        )


# ==============================================================================
# TEST SUITE 6: Consistency between pediatric bands
# ==============================================================================

class TestConsistencyAcrossBands:
    """
    Verify that the thresholds across bands form a logical progression
    (generally tightening as children age toward adult ranges).
    """

    def test_hr_thresholds_decrease_with_age(self):
        """HR red-flag threshold should generally decrease as children age."""
        thresholds = [
            RED_FLAG_THRESHOLDS["infant"]["hr_high"],
            RED_FLAG_THRESHOLDS["young_child"]["hr_high"],
            RED_FLAG_THRESHOLDS["child"]["hr_high"],
            RED_FLAG_THRESHOLDS["adolescent"]["hr_high"],
            RED_FLAG_THRESHOLDS["adult"]["hr_high"],
        ]
        # Each should be >= the next (thresholds should get stricter/lower with age)
        assert thresholds[0] >= thresholds[1] >= thresholds[2] >= thresholds[3] >= thresholds[4], (
            f"HR thresholds don't show expected age progression: {thresholds}"
        )

    def test_rr_thresholds_decrease_with_age(self):
        """RR upper red-flag threshold should decrease as children age."""
        thresholds = [
            RED_FLAG_THRESHOLDS["infant"]["rr_high"],
            RED_FLAG_THRESHOLDS["young_child"]["rr_high"],
            RED_FLAG_THRESHOLDS["child"]["rr_high"],
            RED_FLAG_THRESHOLDS["adolescent"]["rr_high"],
            RED_FLAG_THRESHOLDS["adult"]["rr_high"],
        ]
        assert thresholds[0] >= thresholds[1] >= thresholds[2] >= thresholds[3] >= thresholds[4], (
            f"RR thresholds don't show expected age progression: {thresholds}"
        )


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
