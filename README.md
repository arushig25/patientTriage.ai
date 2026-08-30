# 🏥 PatientTriage.ai

> **AI-assisted emergency department triage and patient-flow decision support.**

[![Python 3.9+](https://img.shields.io/badge/python-3.9+-3776AB.svg)](https://python.org)
[![Streamlit](https://img.shields.io/badge/streamlit-1.28+-FF4B4B.svg)](https://streamlit.io)
[![License: MIT](https://img.shields.io/badge/license-MIT-green.svg)](LICENSE)

When an emergency department gets crowded, the physical queue stops
reflecting clinical risk. **PatientTriage.ai** flags risk early, recommends
an ESI-aligned triage priority with a plain-language reason, and keeps
re-checking every patient still waiting.

**AI recommends. Clinician decides.** Every recommendation is explainable
and every override is captured — this is a decision-support layer, not a
diagnostic system, and it never replaces clinical judgment.

---

## ✨ Features

| Feature | Description |
|---|---|
| **Early Risk Detection** | Age-calibrated early-warning score from vitals and chief complaint, with pediatric, adult, and geriatric reference ranges |
| **Personal-Baseline Awareness** | Returning patients scored against their own documented normal, not just population averages |
| **Natural Language Complaint Matching** | Recognizes real-world phrasing ("I can't breathe", "crushing chest pain") against clinical categories |
| **5-Level Acuity Recommendation** | ESI-aligned acuity with concrete, actionable next-best-action — never just a number |
| **Continuous Re-Assessment** | Waiting patients monitored against safe-wait targets that tighten automatically under surge conditions |
| **Uncertainty-Aware** | Every score carries a confidence level; system leans toward caution when data is incomplete |
| **Clinician Override** | Every recommendation can be confirmed or overridden; overrides require a reason and are permanently recorded |
| **Privacy by Design** | Encrypted at rest, pseudonymized audit trail, RBAC-gated identity access, access logging |

---

## 👤 Role-Based Views

| Role | Dashboard |
|---|---|
| **Triage Nurse** | Patient intake, vitals capture, recommendation review, confirm or override |
| **Charge Nurse** | Live waiting-room board — highest risk first, breach alerts, surge monitoring |
| **Clinical Lead** | Safety metrics, override review, audit trail, privacy and compliance |

---

## 🏗️ Project Structure

```
patientTriage.ai/
├── app.py                              # Streamlit entry point
├── patient_triage/                     # Core application package
│   ├── core/
│   │   └── engine.py                   # Triage scoring engine (NEWS2, pediatric, red flags)
│   ├── data/
│   │   └── simulator.py               # Simulated patient data generator
│   ├── security/
│   │   ├── audit.py                    # Hash-chained, encrypted audit log
│   │   └── privacy.py                  # Encryption, pseudonymization, RBAC
│   └── ui/
│       ├── styles.py                   # Hospital-grade CSS design system
│       ├── components.py               # Reusable UI components
│       └── views/
│           ├── triage_nurse.py         # Triage Nurse dashboard
│           ├── charge_nurse.py         # Charge Nurse waiting-room board
│           └── clinical_lead.py        # Clinical Lead oversight dashboard
├── tests/                              # Comprehensive test suite
│   ├── test_triage_engine.py           # Age-aware red flag tests
│   ├── test_surge_workflow.py          # Surge and history-aware scoring tests
│   ├── test_data_protection.py         # Encryption and privacy tests
│   └── test_audit_logging.py          # Audit dedup and chain integrity tests
├── scripts/
│   └── run_analysis.py                 # Gap analysis runner
├── data/                               # Runtime data (gitignored, auto-generated)
├── .streamlit/
│   └── config.toml                     # Streamlit theme configuration
├── requirements.txt
├── pyproject.toml
└── README.md
```

---

## 🚀 Quick Start

### 1. Clone the repository
```bash
git clone https://github.com/arushig25/patientTriage.ai.git
cd patientTriage.ai
```

### 2. (Optional) Create a virtual environment
```bash
python -m venv .venv

# On Windows:
.venv\Scripts\activate

# On macOS/Linux:
source .venv/bin/activate
```

### 3. Install dependencies
```bash
pip install -r requirements.txt
```

### 4. Launch the application
```bash
streamlit run app.py
```

The application will open in your browser at `http://localhost:8501`. On first launch, encrypted simulated patient data is automatically generated in `data/`.

> **Demo Credentials:** For the **Clinical Lead** role, use password `triage-lead-2026` to re-link pseudonymized audit tokens.

---

## 🧪 Testing

```bash
# Run all tests
pytest

# Run with verbose output
pytest -v

# Run a specific test module
pytest tests/test_triage_engine.py
```

---

## 🏥 Clinical Architecture

```
┌─────────────────────────────────────────────────┐
│                  Scoring Pipeline                 │
│                                                   │
│  1. Deterministic Early-Warning Score             │
│     • Adults (≥16): NEWS2, 7 parameters, 0-20    │
│     • Children (<16): Age-banded vital thresholds │
│     • Baseline-relative adjustment (Gap 2)        │
│                                                   │
│  2. Red-Flag Safety Overrides                     │
│     • Age-adjusted thresholds (Gap 1)             │
│     • Chronic condition modifiers                  │
│     • Can only RAISE acuity, never lower          │
│                                                   │
│  3. Confidence & Uncertainty                      │
│     • Data completeness → confidence score        │
│     • Low confidence → escalate under uncertainty │
│                                                   │
│  Output: 5-level ESI-aligned acuity (1=critical)  │
└─────────────────────────────────────────────────┘
```

---

## 🔒 Compliance & Privacy

| Control | Implementation |
|---|---|
| **Encryption at Rest** | Fernet symmetric encryption for patient data and audit logs |
| **Pseudonymization** | HMAC-based patient ID tokens in audit trail |
| **RBAC** | Role-gated identity re-linking with constant-time password comparison |
| **Access Logging** | Every patient record view logged as a discrete audit event |
| **Data Minimization** | Field-level purpose and retention documentation |
| **Hash-Chained Audit** | Tamper-evident log with SHA-256 chain verification |

**Assumed jurisdiction:** United States — HIPAA. Retention, consent, and data-minimization details available in-app under **Clinical Lead → Privacy & Compliance**.

---

## ⚠️ Disclaimer

This is a prototype. All patient data shown is simulated — no real patient data is used or stored. PatientTriage.ai is a clinical decision-support tool; it does not diagnose patients and does not replace professional clinical judgment. It is not certified for production HIPAA deployment.
