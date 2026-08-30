# PatientTriage.ai — AI-Assisted Emergency Triage

**Accenture Innovation Challenge 2026 — Round 2 | Team b23188**

> When the ER gets crowded, the queue stops reflecting risk.
> PatientTriage.ai detects risk early, recommends the next-best triage
> action, and continuously reassesses patients — without replacing
> clinical judgment.

## What it does
A safety-first clinical **decision-support** layer for emergency triage:
1. **Early risk detection** — age-calibrated early-warning score from vitals + complaint.
2. **Next-best action** — 5-level ESI-aligned acuity with a plain-language recommendation.
3. **Continuous re-assessment** — every waiting patient is re-checked; alerts fire on
   wait-time breach or worsening vitals.
4. **Explicit uncertainty** — every score carries a confidence indicator.
5. **Clinician-in-command** — every recommendation is overridable; every override is logged.

## Why it's clinically credible (not invented)
- **Adults/geriatric:** NEWS2 (RCP), 7-parameter 0–20 score — thresholds from the
  published clinical reference.
- **Pediatric:** age-banded HR/RR thresholds from Fleming et al. 2011 (Lancet).
- **Safety-first design:** red-flag overrides can only *raise* acuity; low confidence
  triggers escalation — matching field-triage targets (under-triage ~5%, over-triage 25–35%).

## Gap 1 Fix: Age-Aware Red-Flag Thresholds ✓ IMPLEMENTED

### The Bug
The initial prototype applied adult vital-sign thresholds in the red-flag safety-override layer, causing false positives on pediatric patients. Example:
- **Patient S. Lopez (P19), age 9, normal vitals (HR 110, RR 28)** would have been falsely flagged as "Respiratory distress" because the override layer checked `RR >= 25` (adult threshold), even though RR 28 is normal for a 9-year-old (normal range: 18–30).

### The Fix
Added age-aware red-flag thresholds (`RED_FLAG_THRESHOLDS` dict) keyed by age band:
- **infant** (<1yr): RR flag at >= 65 (not 25); HR flag at >= 200
- **young_child** (1–5yr): RR flag at >= 48; HR flag at >= 170  
- **child** (5–12yr): **RR flag at >= 36 (not 25)**; HR flag at >= 140
- **adolescent** (12–16yr): RR flag at >= 27; HR flag at >= 135
- **adult**: RR flag at >= 25; HR flag at >= 131 (NEWS2-aligned)

Universal flags (SpO2 < 90%, AVPU ≠ Alert) remain age-independent.

### Validation
- **23 pytest cases** covering normal ranges, abnormal vitals, boundary conditions, and integration.
- **Real-world test:** Patient P19 (age 9, RR 28) now correctly scores **Acuity 3 with no red flags** instead of false escalation.
- **Pediatric safety preserved:** Genuinely critical children (P13: age 1, HR 175, RR 52) still escalate to Acuity 1.

### Before/After (20-patient base dataset)
| Acuity | Before | After | Notes |
|--------|--------|-------|-------|
| 1 (Resuscitation) | 5 | 5 | No change (critical cases unaffected) |
| 2 (Urgent) | 3 | 2 | P19 dropped from 2→3 (false escalation fixed) |
| 3 (Semi-urgent) | 0 | 1 | P19 now correctly triaged here |
| 4–5 (Routine) | 12 | 12 | No change |

## Run locally
```bash
pip install -r requirements.txt
python data_simulator.py      # generates data/patients.csv
streamlit run app.py

# Run tests
pytest test_gap1_age_aware_red_flags.py -v

# View scoring analysis
python run_gap1_analysis.py
