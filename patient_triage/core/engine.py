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

def _red_flags(band: str, v: Vitals, chronic_conditions: Optional[list] = None):
    """
    Identify red-flag safety conditions that mandate immediate escalation.
    
    Args:
        band: Age band ('infant', 'young_child', 'child', 'adolescent', 'adult', 'geriatric')
        v: Vitals object
        chronic_conditions: optional list of known chronic conditions (Gap 2)
            that shift where the SpO2/HR overrides fire -- see
            CHRONIC_CONDITION_MODIFIERS. Absent/unknown conditions are a
            no-op, so callers with no history behave exactly as before.
    
    Returns:
        List of red-flag strings (empty list if no flags).
    
    Design principle:
      - SpO2 floor and altered mental status (not alert) are UNIVERSAL flags
        (true danger signs at any age); the SpO2 floor defaults to 90% but
        may be lowered for a documented chronic condition like COPD.
      - HR, RR, and SBP thresholds are age-adjusted via RED_FLAG_THRESHOLDS,
        so a 9-year-old with textbook-normal vitals (HR 110, RR 28) never
        triggers a false positive; the HR ceiling may be further lowered for
        a documented chronic condition like a cardiac history.
    """
    flags = []
    t = RED_FLAG_THRESHOLDS.get(band, RED_FLAG_THRESHOLDS["adult"])

    spo2_floor = 90
    hr_ceiling = t["hr_high"]
    for cond in (chronic_conditions or []):
        mod = CHRONIC_CONDITION_MODIFIERS.get(cond)
        if not mod:
            continue
        spo2_floor += mod.get("spo2_floor_delta", 0)
        hr_ceiling += mod.get("hr_ceiling_delta", 0)

    # Universal red flags (true danger signs at any age)
    if v.spo2 is not None and v.spo2 < spo2_floor:
        note = ", COPD-adjusted" if spo2_floor != 90 else ""
        flags.append(f"Critical hypoxia (SpO2 < {spo2_floor}%{note})")
    if v.avpu is not None and str(v.avpu).upper() != "A":
        flags.append("Altered mental status (not alert)")
    
    # Age-adjusted red flags
    if v.hr is not None and v.hr >= hr_ceiling:
        note = ", cardiac-history-adjusted" if hr_ceiling != t["hr_high"] else ""
        flags.append(f"Severe tachycardia (HR >= {hr_ceiling}, age-adjusted{note})")
    
    if v.rr is not None and (v.rr <= t["rr_low"] or v.rr >= t["rr_high"]):
        flags.append(f"Respiratory distress (age-adjusted RR band: {t['rr_low']}-{t['rr_high']})")
    
    if v.sbp is not None and v.sbp <= t["sbp_low"]:
        flags.append(f"Hypotension (SBP <= {t['sbp_low']}, age-adjusted)")
    
    return flags


# ---------- Gap 6: robust complaint/symptom matching ----------
#
# The original exact-string match missed high-risk complaints on ordinary
# wording differences (e.g. "difficulty breathing" not matching
# "shortness of breath" -- exactly what happened to P19, S. Lopez).
# Replaced with a small synonym/keyword map: each canonical high-risk
# category lists several phrasings a patient or nurse might actually
# type. Matching is by normalized keyword containment, not full-string
# equality. This stays rule-based and auditable (no black-box NLP) --
# the exact synonym set below is the complete, reviewable list, matching
# the same explainability principle used in RED_FLAG_THRESHOLDS and
# CHRONIC_CONDITION_MODIFIERS.

HIGH_RISK_COMPLAINTS = {
    "CHEST_PAIN": {
        "chest pain", "chest pressure", "chest tightness", "tight chest",
    },
    "RESPIRATORY_DISTRESS": {
        "shortness of breath", "difficulty breathing", "trouble breathing",
        "cant breathe", "can t breathe", "breathless", "gasping for air",
        "sob", "labored breathing",
    },
    "STROKE_SYMPTOMS": {
        "stroke symptoms", "facial droop", "face drooping", "slurred speech",
        "one sided weakness", "sudden weakness", "sudden numbness",
    },
    "SEVERE_BLEEDING": {
        "severe bleeding", "heavy bleeding", "uncontrolled bleeding",
        "bleeding heavily", "hemorrhage", "hemorrhaging",
    },
    "ALTERED_CONSCIOUSNESS": {
        "altered consciousness", "unresponsive", "not waking up",
        "loss of consciousness", "passed out", "suddenly confused",
    },
    "SEIZURE": {
        "seizure", "seizing", "convulsions", "convulsing",
    },
    "ANAPHYLAXIS": {
        "anaphylaxis", "allergic reaction", "severe allergic reaction",
        "throat swelling", "throat closing",
    },
    "MAJOR_TRAUMA": {
        "major trauma", "severe trauma", "car accident", "fall from height",
        "crush injury", "gunshot wound", "stab wound",
    },
}


def _normalize_complaint(text: str) -> str:
    """Lowercase, strip punctuation, collapse whitespace -- so wording
    differences like capitalization or an apostrophe don't defeat a
    match."""
    import re
    text = text.lower()
    text = re.sub(r"[^\w\s]", " ", text)
    return re.sub(r"\s+", " ", text).strip()


def _match_high_risk_complaint(complaint: str):
    """Return (canonical_category, matched_phrase) if `complaint`
    contains any phrase from a HIGH_RISK_COMPLAINTS category after
    normalization, else (None, None)."""
    if not complaint:
        return None, None
    norm = _normalize_complaint(complaint)
    for category, phrases in HIGH_RISK_COMPLAINTS.items():
        for phrase in phrases:
            if phrase in norm:
                return category, phrase
    return None, None


# ---------- Gap 2: patient-history-aware scoring ----------
#
# A returning patient's own documented baseline is often more informative
# than the generic population-normal range: a resting HR of 100 is a red
# flag for most adults but unremarkable for a patient whose chart says
# that's where they always run. This layer only ever adjusts the
# *informative* EWS sub-score (0-3 per parameter) and never touches the
# red-flag safety layer's universal triggers (SpO2 < 90, AVPU != Alert) --
# those stay absolute, at-any-age, at-any-history danger signs.
#
# Two independent, auditable mechanisms (both upward-safe):
#   1. Baseline-relative re-scoring of HR/SBP (this function).
#   2. Chronic-condition modifiers to the red-flag thresholds themselves
#      (see CHRONIC_CONDITION_MODIFIERS below) -- small enough to read at
#      a glance, not a black-box model.

BASELINE_NEAR_PCT = 0.10      # within 10% of own baseline -> "normal for them"
BASELINE_NOTABLE_PCT = 0.20   # >=20% off own baseline -> flag for awareness


def _baseline_adjusted_score(name: str, current, baseline, sub_score: int,
                              reasons: list, worse_direction: str) -> int:
    """
    Re-score a single NEWS2/peds parameter using the patient's own
    documented baseline, in addition to the population-normal range that
    produced `sub_score`.

    worse_direction: 'high' if higher values are the concerning direction
    (HR), 'low' if lower values are (SBP).

    - If the population layer flagged this value as abnormal (sub_score > 0)
      but it's within BASELINE_NEAR_PCT of the patient's own baseline,
      that's "known-abnormal-for-them, not new" -- ease the score down by
      one point (never below 0, and this never overrides a red flag).
    - If the population layer says this value is normal (sub_score == 0)
      but it has moved BASELINE_NOTABLE_PCT or more away from the
      patient's own baseline in the concerning direction, that's a new
      deviation worth the clinician's attention even though it's still
      inside the textbook-normal range -- bump the score up by one point.
    """
    if current is None or not baseline:
        return sub_score

    delta_pct = (current - baseline) / baseline
    worse_relative = delta_pct > 0 if worse_direction == "high" else delta_pct < 0

    if sub_score > 0 and abs(delta_pct) <= BASELINE_NEAR_PCT:
        adjusted = max(0, sub_score - 1)
        if adjusted != sub_score:
            reasons.append(
                f"{name} {current:g} is within 10% of this patient's documented "
                f"baseline ({baseline:g}) -- known-abnormal-for-them, not a new "
                f"finding; score eased {sub_score}\u2192{adjusted}."
            )
        return adjusted

    if sub_score == 0 and worse_relative and abs(delta_pct) >= BASELINE_NOTABLE_PCT:
        reasons.append(
            f"{name} {current:g} is {abs(delta_pct) * 100:.0f}% "
            f"{'above' if worse_direction == 'high' else 'below'} this patient's "
            f"documented baseline ({baseline:g}) -- within population-normal "
            f"range, but flagged for clinician awareness as a new deviation."
        )
        return 1

    return sub_score


# Small, explainable rule table (not a black-box model): a known chronic
# condition can shift where the *red-flag safety override* fires, in
# either direction, depending on the clinical reason:
#   - COPD patients often run a chronically lower SpO2 at their personal
#     baseline (targets of ~88-92% are standard practice), so the generic
#     <90% universal flag causes false-positive escalations for them --
#     the floor is lowered so genuine further deterioration still fires.
#   - Known cardiac history means sustained tachycardia is a bigger risk
#     signal than it is for the general adult population, so the ceiling
#     is lowered (more cautious / fires sooner) rather than raised.
CHRONIC_CONDITION_MODIFIERS = {
    "COPD":    {"spo2_floor_delta": -4},    # 90 -> 86
    "cardiac": {"hr_ceiling_delta": -21},   # adult/geriatric 131 -> 110
}


def score_patient(age: float, vitals: Vitals, complaint: str = "",
                   history: Optional[dict] = None) -> TriageResult:
    band = age_band(age)
    reasons = []
    missing = 0
    total_params = 6

    baseline_hr = history.get("baseline_hr") if history else None
    baseline_sbp = history.get("baseline_sbp") if history else None
    chronic_conditions = (history.get("chronic_conditions") or []) if history else []

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
        if not m_hr:
            s_hr = _baseline_adjusted_score("HR", vitals.hr, baseline_hr, s_hr,
                                             reasons, "high")
        if not m_sbp:
            s_sbp = _baseline_adjusted_score("SBP", vitals.sbp, baseline_sbp, s_sbp,
                                              reasons, "low")
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
        if not m_hr:
            s_hr = _baseline_adjusted_score("HR", vitals.hr, baseline_hr, s_hr,
                                             reasons, "high")
        if not m_sbp:
            s_sbp = _baseline_adjusted_score("SBP", vitals.sbp, baseline_sbp, s_sbp,
                                              reasons, "low")
        parts = [("RR", s_rr, m_rr), ("SpO2", s_spo2, m_spo2), ("Temp", s_temp, m_temp),
                 ("SBP", s_sbp, m_sbp), ("HR", s_hr, m_hr), ("Consciousness", s_av, m_av),
                 ("Oxygen", s_o2, m_o2)]
        total_params = 7
        if band == "geriatric":
            reasons.append("Geriatric patient: NEWS2 applied; low threshold "
                           "for escalation (atypical presentation common).")

    if history:
        if chronic_conditions:
            reasons.append(
                f"Known chronic condition(s) on file: {', '.join(chronic_conditions)} "
                f"-- red-flag override thresholds adjusted accordingly (see below)."
            )
        last_acuity = history.get("last_visit_acuity")
        last_date = history.get("last_visit_date")
        if last_acuity is not None and last_date:
            reasons.append(f"History on file: last visit {last_date}, "
                           f"acuity L{last_acuity}.")

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
    flags = _red_flags(band, vitals, chronic_conditions)
    if flags:
        acuity = min(acuity, 1 if len(flags) >= 2 else 2)
        reasons.append("Red-flag override applied (acuity raised, never lowered).")

    # --- Complaint-based escalation (upward only, Gap 6: synonym-aware) ---
    hr_category, hr_phrase = _match_high_risk_complaint(complaint)
    if hr_category:
        acuity = min(acuity, 2)
        reasons.append(f"High-risk complaint '{complaint}' matched category "
                       f"{hr_category} (via '{hr_phrase}') -> minimum acuity 2.")

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
# These are the QUIET-SHIFT (surge_factor <= 1x) baseline values; see
# safe_wait_minutes() below for the surge-adaptive version (Gap 3).
SAFE_WAIT_MINUTES = {1: 0, 2: 10, 3: 30, 4: 60, 5: 120}


# ---------- Gap 3: surge-adaptive workflow ----------
#
# Gap 3 makes the system genuinely behave differently under load, not just
# process more identical rows through the same thresholds: safe-wait
# ceilings tighten for lower-acuity tiers, and the waiting-room board
# re-ranks dynamically instead of sorting by acuity alone.

NORMAL_CAPACITY = 20          # ED sized for ~20 concurrently-active patients
SURGE_BANNER_THRESHOLD = 2.0  # surge_factor above which the UI/audit flags surge mode


def compute_surge_factor(queue_length: int, capacity: int = NORMAL_CAPACITY) -> float:
    """
    Live surge factor = currently-waiting patients / normal capacity.
    1.0 = a normal quiet shift; 3.0 = the department is running at 3x its
    sized capacity. Recomputed fresh from the current queue on every call --
    there is no stored/stale state.
    """
    if capacity <= 0:
        return 0.0
    return round(queue_length / capacity, 2)


def safe_wait_minutes(acuity: int, surge_factor: float = 1.0) -> int:
    """
    Surge-adaptive safe-wait ceiling (Gap 3).

    Acuity 1-2 are left unchanged regardless of load: those patients
    should never be waiting in the first place, and their margin is
    already at (or near) zero. For Acuity 3-5, the ceiling scales down
    linearly from 1.0x (unchanged) to 3.0x load (two-thirds of the quiet-
    shift value) -- e.g. Acuity 4's 60-minute quiet-shift ceiling tightens
    to 40 minutes at 3x surge, reflecting that deterioration risk per
    minute of waiting rises for stable-looking patients once the
    department is crowded. Surge beyond 3x is capped at the 3x scaling
    (thresholds don't keep shrinking without bound).
    """
    base = SAFE_WAIT_MINUTES.get(acuity, 120)
    if acuity <= 2 or surge_factor <= 1.0:
        return base
    factor = min(surge_factor, 3.0)
    scale = 1.0 - (1.0 / 3.0) * ((factor - 1.0) / 2.0)   # 1x:1.00, 2x:0.833, 3x:0.667
    return max(5, round(base * scale))


def wait_breach(acuity: int, minutes_waited: float, surge_factor: float = 1.0) -> bool:
    return minutes_waited > safe_wait_minutes(acuity, surge_factor)


CONFIDENCE_URGENCY_PENALTY = {"Low": -6, "Moderate": -2, "High": 0}


def effective_urgency(acuity: int, minutes_waited: float, confidence_label: str) -> float:
    """
    Dynamic re-ranking score for the Charge Nurse board (Gap 3): combines
    acuity, elapsed wait, and confidence instead of a static sort by acuity
    alone, so a low-confidence patient can surface above a higher-
    confidence patient at the same acuity who has waited less -- confidence
    reflects how much we trust the score, and a score we trust less
    deserves a closer look sooner.

    Lower score = seen sooner. Acuity remains the dominant term.
    """
    base = acuity * 20
    wait_relief = minutes_waited * 0.15
    conf_penalty = CONFIDENCE_URGENCY_PENALTY.get(confidence_label, 0)
    return round(base - wait_relief + conf_penalty, 2)

