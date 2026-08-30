# PatientTriage.ai

**AI-assisted emergency department triage and patient-flow decision support.**

> When an emergency department gets crowded, the physical queue stops
> reflecting clinical risk. PatientTriage.ai flags risk early, recommends
> an ESI-aligned triage priority with a plain-language reason, and keeps
> re-checking every patient still waiting.

**AI recommends. Clinician decides.** Every recommendation is explainable
and every override is captured — this is a decision-support layer, not a
diagnostic system, and it never replaces clinical judgment.

## What it does

- **Early risk detection** — an age-calibrated early-warning score built
  from vitals and chief complaint, with pediatric, adult, and geriatric
  patients each assessed against clinically appropriate ranges.
- **Personal-baseline awareness** — returning patients with a documented
  baseline are scored against *their own* normal, not just the population
  average, so a chronic condition doesn't produce a false alarm and a
  meaningful change from baseline doesn't get missed.
- **Understands how patients actually describe symptoms** — recognizes
  real-world phrasing ("I can't breathe," "crushing chest pain") against
  the clinical category it maps to, so the nurse can verify the system
  understood correctly.
- **Next-best action** — a 5-level ESI-aligned acuity with a concrete,
  actionable recommendation, never just a number.
- **Continuous re-assessment** — every waiting patient is monitored
  against a safe-wait target for their acuity; the target tightens
  automatically as the department gets busier, and the board re-prioritizes
  accordingly.
- **Honest about uncertainty** — every score carries a confidence level,
  and the system leans toward caution (never toward calm) when
  information is incomplete.
- **Clinician stays in control** — every recommendation can be confirmed
  or overridden; every override requires a reason and is permanently
  recorded.
- **Protected by design** — patient data is encrypted at rest, audit
  identifiers are pseudonymized, identity re-linking is role-gated, and
  every access to a patient record is itself logged.

## Who it's for

| Role | What they see |
|---|---|
| **Triage Nurse** | Register a patient, capture complaint and vitals, review the recommendation and its reasoning, confirm or override. |
| **Charge Nurse** | A live waiting-room board — who's highest risk, who's waited too long, current department load. |
| **Clinical Lead** | Safety and trust metrics, override review, audit history, and privacy/compliance information. |

## Run locally

```bash
pip install -r requirements.txt
python data_simulator.py      # generates the simulated patient dataset
streamlit run app.py
```

## Tests

```bash
pytest
```

## Compliance

Assumed deployment jurisdiction: **United States — HIPAA.** Data
retention, consent model, and field-level data-minimization notes are
available in-app under **Clinical Lead → Privacy & Compliance.**

## Disclaimer

This is a prototype. All patient data shown is simulated — no real
patient data is used or stored. PatientTriage.ai is a clinical
decision-support tool; it does not diagnose patients and does not
replace professional clinical judgment. It is not certified for
production HIPAA deployment.
