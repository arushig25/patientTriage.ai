"""
triage_engine.py
----------------
Hybrid triage scoring engine for PatientTriage.ai.

Design principle: SAFETY-FIRST / ESCALATE-UNDER-UNCERTAINTY.
Under-triage (missing a critical patient) is treated as categorically
worse than over-triage, per field-triage safety targets (under-triage
~5%, over-triage 25-35% accepted).

Architecture (three layers, deterministic layer has upward veto):
  1. Deterministic early-warning score:
        - Adults (>=16): NEWS2, 7 parameters, 0-20.
          Thresholds from RCP NEWS2 (NCBI clinical reference).
        - Children (<16): age-banded vital thresholds converted to an
          equivalent 0-3 sub-score per parameter, ranges from Fleming
          et al. 2011 (Lancet) / PedsCases pediatric vitals chart.
  2. Hard red-flag safety overrides: can only raise acuity, never lower.
  3. Confidence estimate based on completeness of the input data
     (missing vitals -> lower confidence -> bias toward escalation).

Output acuity is mapped to a 5-level scale aligned with the Emergency
Severity Index (ESI): 1 = most critical, 5 = least urgent.
"""

from dataclasses import dataclass, field
from typing import Optional


# ---------- Age band helpers ----------

def age_band(age: float) -> str:
    if age < 1:
        return "infant"
    if age < 5:
        return "young_child"
    if age < 12:
        return "child"
    if age < 16:
        return "adolescent"
    if age >= 65:
        return "geriatric"
    return "adult"


# Age-banded NORMAL vital ranges (heart rate, respiratory rate).
# Pediatric ranges from Fleming et al. 2011 / PedsCases chart.
# Used to build age-appropriate sub-scores for children.
PEDS_NORMAL = {
    "infant":       {"hr": (100, 160), "rr": (30, 60)},
    "young_child":  {"hr": (90, 150),  "rr": (24, 40)},
    "child":        {"hr": (70, 120),  "rr": (18, 30)},
    "adolescent":   {"hr": (60, 100),  "rr": (12, 20)},
}

# Age-banded RED FLAG THRESHOLDS for safety overrides.
# Derived from the upper end of abnormal ranges in clinical literature.
# These define the point at which a vital sign is so abnormal that it
# triggers an immediate escalation, independent of the EWS scoring path.
# Thresholds are set at the edge of clinical concern, close enough to normal
# to catch problems but with enough buffer to avoid false positives.
RED_FLAG_THRESHOLDS = {
    "infant": {
        "hr_high": 200,        # Tachycardia threshold for infants (<1yr; normal 100-160)
        "rr_high": 65,         # Severe tachypnea threshold (normal 30-60)
        "rr_low": 25,          # Severe bradypnea threshold (normal 30-60)
        "sbp_low": 50,         # Age-adjusted hypotension for infants
    },
    "young_child": {
        "hr_high": 170,        # Tachycardia threshold (1-5yr; normal 90-150)
        "rr_high": 48,         # Severe tachypnea threshold (normal 24-40)
        "rr_low": 22,          # Severe bradypnea threshold (normal 24-40)
        "sbp_low": 60,         # Age-adjusted hypotension
    },
    "child": {
        "hr_high": 140,        # Tachycardia threshold (5-12yr; normal 70-120)
        "rr_high": 36,         # Severe tachypnea threshold (normal 18-30)
        "rr_low": 14,          # Severe bradypnea threshold (normal 18-30)
        "sbp_low": 70,         # Age-adjusted hypotension
    },
    "adolescent": {
        "hr_high": 135,        # Tachycardia threshold (12-16yr; normal 60-100)
        "rr_high": 27,         # Severe tachypnea threshold (normal 12-20)
        "rr_low": 10,          # Severe bradypnea threshold (normal 12-20)
        "sbp_low": 85,         # Age-adjusted hypotension (transitioning to adult)
    },
    "adult": {
        "hr_high": 131,        # Adult tachycardia (NEWS2-aligned)
        "rr_high": 25,         # Adult tachypnea (NEWS2-aligned)
        "rr_low": 8,           # Adult bradypnea (NEWS2-aligned)
        "sbp_low": 90,         # Adult hypotension (NEWS2-aligned)
    },
    "geriatric": {
        "hr_high": 131,        # Same as adult; geriatric fragility handled elsewhere
        "rr_high": 25,         # Same as adult
        "rr_low": 8,           # Same as adult
        "sbp_low": 90,         # Same as adult
    },
}


# ---------- NEWS2 (adult / geriatric) parameter scoring ----------

def _news2_resp_rate(rr):
    if rr is None: return 0, True
    if rr <= 8:  return 3, False
    if rr <= 11: return 1, False
    if rr <= 20: return 0, False
    if rr <= 24: return 2, False
    return 3, False

def _news2_spo2(spo2):
    if spo2 is None: return 0, True
    if spo2 <= 91: return 3, False
    if spo2 <= 93: return 2, False
    if spo2 <= 95: return 1, False
    return 0, False

def _news2_temp(temp):
    if temp is None: return 0, True
    if temp <= 35.0: return 3, False
    if temp <= 36.0: return 1, False
    if temp <= 38.0: return 0, False
    if temp <= 39.0: return 1, False
    return 2, False

def _news2_sbp(sbp):
    if sbp is None: return 0, True
    if sbp <= 90:  return 3, False
    if sbp <= 100: return 2, False
    if sbp <= 110: return 1, False
    if sbp <= 219: return 0, False
    return 3, False

def _news2_hr(hr):
    if hr is None: return 0, True
    if hr <= 40:  return 3, False
    if hr <= 50:  return 1, False
    if hr <= 90:  return 0, False
    if hr <= 110: return 1, False
    if hr <= 130: return 2, False
    return 3, False

def _news2_consciousness(avpu):
    # AVPU: Alert / Voice / Pain / Unresponsive; anything but Alert scores 3.
    if avpu is None: return 0, True
    return (0, False) if str(avpu).upper() == "A" else (3, False)

def _news2_oxygen(on_oxygen):
    if on_oxygen is None: return 0, True
    return (2, False) if on_oxygen else (0, False)


# ---------- Pediatric parameter scoring (age-banded) ----------

def _peds_param(value, low, high):
    """Return 0-3 sub-score based on distance outside the normal band."""
    if value is None:
        return 0, True
    if low <= value <= high:
        return 0, False
    span = high - low
    if value < low:
        dev = (low - value) / max(span, 1)
    else:
        dev = (value - high) / max(span, 1)
    if dev <= 0.25: return 1, False
    if dev <= 0.75: return 2, False
    return 3, False


# ---------- Data structures ----------

@dataclass
class Vitals:
    hr: Optional[float] = None
    rr: Optional[float] = None
    spo2: Optional[float] = None
    sbp: Optional[float] = None
    temp: Optional[float] = None
    avpu: Optional[str] = None          # A / V / P / U
    on_oxygen: Optional[bool] = None

@dataclass
class TriageResult:
    acuity: int                         # 1 (critical) .. 5 (non-urgent)
    ews_score: int
    confidence: float                   # 0..1
    confidence_label: str
    reasons: list = field(default_factory=list)
    red_flags: list = field(default_factory=list)
    recommended_action: str = ""
    completeness: float = 0.0


# ---------- Red-flag safety overrides (upward only) ----------

def _red_flags(band: str, v: Vitals):
    """
    Identify red-flag safety conditions that mandate immediate escalation.
    
    Args:
        band: Age band ('infant', 'young_child', 'child', 'adolescent', 'adult', 'geriatric')
        v: Vitals object
    
    Returns:
        List of red-flag strings (empty list if no flags).
    
    Design principle:
      - SpO2 < 90% and altered mental status (not alert) are UNIVERSAL flags
        (true danger signs at any age).
      - HR, RR, and SBP thresholds are age-adjusted via RED_FLAG_THRESHOLDS,
        so a 9-year-old with textbook-normal vitals (HR 110, RR 28) never
        triggers a false positive.
    """
    flags = []
    t = RED_FLAG_THRESHOLDS.get(band, RED_FLAG_THRESHOLDS["adult"])
    
    # Universal red flags (true danger signs at any age)
    if v.spo2 is not None and v.spo2 < 90:
        flags.append("Critical hypoxia (SpO2 < 90%)")
    if v.avpu is not None and str(v.avpu).upper() != "A":
        flags.append("Altered mental status (not alert)")
    
    # Age-adjusted red flags
    if v.hr is not None and v.hr >= t["hr_high"]:
        flags.append(f"Severe tachycardia (HR >= {t['hr_high']}, age-adjusted)")
    
    if v.rr is not None and (v.rr <= t["rr_low"] or v.rr >= t["rr_high"]):
        flags.append(f"Respiratory distress (age-adjusted RR band: {t['rr_low']}-{t['rr_high']})")
    
    if v.sbp is not None and v.sbp <= t["sbp_low"]:
        flags.append(f"Hypotension (SBP <= {t['sbp_low']}, age-adjusted)")
    
    return flags


HIGH_RISK_COMPLAINTS = {
    "chest pain", "shortness of breath", "stroke symptoms",
    "severe bleeding", "altered consciousness", "seizure",
    "anaphylaxis", "major trauma",
}


def score_patient(age: float, vitals: Vitals, complaint: str = "") -> TriageResult:
    band = age_band(age)
    reasons = []
    missing = 0
    total_params = 6

    if band in PEDS_NORMAL:
        # Pediatric path: age-banded HR/RR + shared SpO2/temp/consciousness.
        norms = PEDS_NORMAL[band]
        s_hr, m_hr = _peds_param(vitals.hr, *norms["hr"])
        s_rr, m_rr = _peds_param(vitals.rr, *norms["rr"])
        s_spo2, m_spo2 = _news2_spo2(vitals.spo2)
        s_temp, m_temp = _news2_temp(vitals.temp)
        s_av, m_av = _news2_consciousness(vitals.avpu)
        s_sbp, m_sbp = (0, True) if vitals.sbp is None else (
            (2, False) if vitals.sbp < 70 else (0, False))
        parts = [("HR", s_hr, m_hr), ("RR", s_rr, m_rr), ("SpO2", s_spo2, m_spo2),
                 ("Temp", s_temp, m_temp), ("Consciousness", s_av, m_av),
                 ("SBP", s_sbp, m_sbp)]
        reasons.append(f"Pediatric scoring for age band '{band}' "
                       f"(age-calibrated HR/RR thresholds).")
    else:
        # Adult / geriatric path: NEWS2.
        s_rr, m_rr = _news2_resp_rate(vitals.rr)
        s_spo2, m_spo2 = _news2_spo2(vitals.spo2)
        s_temp, m_temp = _news2_temp(vitals.temp)
        s_sbp, m_sbp = _news2_sbp(vitals.sbp)
        s_hr, m_hr = _news2_hr(vitals.hr)
        s_av, m_av = _news2_consciousness(vitals.avpu)
        s_o2, m_o2 = _news2_oxygen(vitals.on_oxygen)
        parts = [("RR", s_rr, m_rr), ("SpO2", s_spo2, m_spo2), ("Temp", s_temp, m_temp),
                 ("SBP", s_sbp, m_sbp), ("HR", s_hr, m_hr), ("Consciousness", s_av, m_av),
                 ("Oxygen", s_o2, m_o2)]
        total_params = 7
        if band == "geriatric":
            reasons.append("Geriatric patient: NEWS2 applied; low threshold "
                           "for escalation (atypical presentation common).")

    ews = sum(p[1] for p in parts)
    missing = sum(1 for p in parts if p[2])
    for name, sc, miss in parts:
        if miss:
            reasons.append(f"{name}: not recorded (assumed normal, lowers confidence).")
        elif sc > 0:
            reasons.append(f"{name}: abnormal, +{sc} to early-warning score.")

    # --- Map EWS to 5-level acuity (ESI-aligned) ---
    if ews >= 7:
        acuity = 1
    elif ews >= 5:
        acuity = 2
    elif ews >= 3:
        acuity = 3
    elif ews >= 1:
        acuity = 4
    else:
        acuity = 5

    # --- Red-flag overrides (upward only) ---
    flags = _red_flags(band, vitals)
    if flags:
        acuity = min(acuity, 1 if len(flags) >= 2 else 2)
        reasons.append("Red-flag override applied (acuity raised, never lowered).")

    # --- Complaint-based escalation (upward only) ---
    if complaint and complaint.strip().lower() in HIGH_RISK_COMPLAINTS:
        acuity = min(acuity, 2)
        reasons.append(f"High-risk complaint '{complaint}' -> minimum acuity 2.")

    # --- Confidence from data completeness ---
    completeness = 1 - (missing / total_params)
    if band == "geriatric":
        completeness *= 0.9   # atypical presentation -> discount confidence
    confidence = round(max(0.15, completeness), 2)
    if confidence >= 0.8:
        clabel = "High"
    elif confidence >= 0.55:
        clabel = "Moderate"
    else:
        clabel = "Low"

    # --- Escalate under uncertainty ---
    if clabel == "Low" and acuity > 2:
        acuity -= 1
        reasons.append("LOW confidence + non-critical score -> escalated one "
                       "level (bias toward safety under uncertainty).")

    action = _recommend_action(acuity, flags, clabel)

    return TriageResult(
        acuity=acuity, ews_score=ews, confidence=confidence,
        confidence_label=clabel, reasons=reasons, red_flags=flags,
        recommended_action=action, completeness=round(completeness, 2),
    )


def _recommend_action(acuity, flags, clabel):
    if acuity == 1:
        return "IMMEDIATE: resuscitation bay, notify physician now."
    if acuity == 2:
        base = "URGENT: place in monitored area, physician review < 10 min."
        if clabel == "Low":
            base += " Re-take full vitals to confirm."
        return base
    if acuity == 3:
        return "Room when available; re-assess within 30 min."
    if acuity == 4:
        return "Standard queue; re-assess within 60 min."
    return "Non-urgent; fast-track / minor care stream."


# ---------- Safe wait-time thresholds per acuity (minutes) ----------
# If a waiting patient exceeds these, the system triggers re-assessment.
SAFE_WAIT_MINUTES = {1: 0, 2: 10, 3: 30, 4: 60, 5: 120}


def wait_breach(acuity: int, minutes_waited: float) -> bool:
    return minutes_waited > SAFE_WAIT_MINUTES.get(acuity, 120)
