# 🏥 PatientTriage.ai

> **AI-assisted emergency department triage and patient-flow decision support workstation.**

[![Python 3.9+](https://img.shields.io/badge/python-3.9+-3776AB.svg)](https://python.org)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.100+-009688.svg)](https://fastapi.tiangolo.com)
[![React](https://img.shields.io/badge/React-18+-61DAFB.svg)](https://reactjs.org)
[![Tailwind CSS](https://img.shields.io/badge/Tailwind-3.4+-38B2AC.svg)](https://tailwindcss.com)
[![License: MIT](https://img.shields.io/badge/license-MIT-green.svg)](LICENSE)

When an emergency department gets crowded, physical queues fail to reflect true clinical risk. **PatientTriage.ai** detects risk early, recommends an ESI-aligned triage level with clinical rationale, continuously assesses waiting patients against adaptive safe-wait thresholds, and maintains a cryptographic audit log of all clinical actions.

**AI recommends. Clinician decides.** Every recommendation is explainable and every override requires clinician justification — this is a decision-support layer, not a diagnostic system, and never replaces clinical judgment.

---

## ✨ System Capabilities

| Capability | Description |
|---|---|
| **Early Risk Detection** | Age-calibrated early-warning scoring (NEWS2 / Fleming pediatric percentiles) evaluating vitals and symptoms. |
| **Personal-Baseline Awareness** | Returning patients evaluated against their own documented normal vitals from institutional EHR. |
| **Natural Language Clinical Matching** | Identifies critical symptoms ("I can't breathe", "crushing chest pressure") across clinical categories. |
| **5-Level ESI Triage Recommendation** | Standardized ESI Acuity (Levels 1–5) with concrete, mandated next-best-action. |
| **Dynamic Surge Protocols** | Department load factor adjusts safe-wait limits automatically to mitigate deterioration. |
| **Confidence & Uncertainty Guardrails** | Incomplete vitals penalize confidence and safely escalate priority (+1 tier). |
| **Clinician Override Tracking** | Overrides mandate clinical justification and are permanently recorded in a SHA-256 hash chain. |
| **Privacy by Design** | HIPAA-aligned architecture with Fernet AES encryption at rest and HMAC-SHA256 pseudonymized identifiers. |

---

## 👤 Clinical Roles & Views

| Role | Interface Highlights |
|---|---|
| **Triage Nurse** | Patient intake, telemetry vitals with animated ECG waveforms, instant ESI recommendation, and live clinical simulator. |
| **Charge Nurse** | Live waiting-room board, dynamic priority re-ranking, wait-time countdown meters, and emergency surge controls. |
| **Clinical Lead** | Population acuity distribution charts, regulatory safety checklists, and password-gated audit identity unmasking. |

---

## 🏗️ Architecture & Project Structure

```
patientTriage.ai/
├── server.py                           # FastAPI application & REST backend
├── patient_triage/                     # Core clinical & security package
│   ├── core/
│   │   └── engine.py                   # Scoring engine (NEWS2, pediatric, red flags, surge)
│   ├── data/
│   │   └── simulator.py               # Encrypted simulated patient cohort generator
│   └── security/
│       ├── audit.py                    # Hash-chained, encrypted audit logging (SHA-256)
│       └── privacy.py                  # Cryptographic pseudonymization, RBAC, Fernet AES
├── frontend/                           # Modern Clinical Command Center Web App
│   ├── src/
│   │   ├── components/
│   │   │   ├── Header.jsx              # Status telemetry, surge toggle & light/dark theme switch
│   │   │   ├── TriageNurseView.jsx     # Patient intake, ECG monitors & live calculator
│   │   │   ├── ChargeNurseView.jsx     # Dynamic priority queue & breach timers
│   │   │   ├── ClinicalLeadView.jsx    # Analytics charts & tamper-evident audit vault
│   │   │   ├── ECGWaveform.jsx         # Animated heart rate telemetry line
│   │   │   └── AcuityBadge.jsx         # Adaptive high-contrast ESI badges
│   │   ├── App.jsx                     # Application shell & telemetry synchronization
│   │   └── index.css                   # Clinical styling & custom scrollbars
│   ├── dist/                           # Pre-compiled production static assets (zero npm required to run)
│   ├── package.json
│   ├── vite.config.js
│   └── tailwind.config.js
├── tests/                              # Comprehensive test suite (95/95 passing)
│   ├── test_triage_engine.py           # Age-aware red flag tests
│   ├── test_surge_workflow.py          # Surge and history-aware scoring tests
│   ├── test_data_protection.py         # Encryption and privacy tests
│   └── test_audit_logging.py          # Audit dedup and chain integrity tests
├── scripts/
│   └── run_analysis.py                 # Gap analysis runner
├── run.bat                             # One-click Windows CMD launcher
├── run.ps1                             # One-click PowerShell launcher
├── requirements.txt                    # Python dependencies
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

### 4. Launch the Command Center
You can start the application with a single click or command:

```bash
# Option A: One-click launcher
.\run.ps1      # PowerShell
.\run.bat      # Windows CMD

# Option B: Direct Python command
python server.py
```

The command center opens automatically in your browser at **`http://localhost:8000`**.

> **Demo Credentials:** In the **Clinical Lead** role, use password `triage-lead-2026` to re-link pseudonymized audit records.

---

## 🧪 Testing

```bash
# Run all 95 unit tests
python -m pytest tests

# Run with verbose output
python -m pytest tests -v
```

---

## 🔒 Security & Compliance
- **Data Protection at Rest:** Encrypted with Fernet (AES-128-CBC with HMAC-SHA256).
- **Pseudonymization:** Patient IDs are replaced with keyed HMAC-SHA256 tokens in audit logs.
- **Tamper-Evident Hash Chain:** Every entry stores `SHA256(prev_hash + payload + ts)`. The chain is continuously verified.
- **Fail-Closed RBAC:** Re-linking patient identities requires strict role verification and authenticated passcodes.
