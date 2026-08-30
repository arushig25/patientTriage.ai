"""
app.py -- PatientTriage.ai Clinical Decision Support Workspace
Entry point for Streamlit web application.
"""

import os
import sys

# Self-bootstrap if executed directly via `python app.py`
try:
    import streamlit.runtime
    if not streamlit.runtime.exists():
        from streamlit.web import cli as stcli
        sys.argv = ["streamlit", "run", os.path.abspath(__file__)]
        sys.exit(stcli.main())
except (ImportError, AttributeError):
    pass

import streamlit as st

from patient_triage.ui.styles import HOSPITAL_CSS
from patient_triage.data.simulator import write_csv, surge_patients, base_patients, COLS, get_history
from patient_triage.core.engine import Vitals, score_patient, compute_surge_factor, NORMAL_CAPACITY, SURGE_BANNER_THRESHOLD
from patient_triage.ui.views import triage_nurse, charge_nurse, clinical_lead
from patient_triage.security import audit

# Page configuration
st.set_page_config(
    page_title="PatientTriage.ai — Emergency Clinical Workspace",
    page_icon="🏥",
    layout="wide",
    initial_sidebar_state="expanded",
)
st.markdown(HOSPITAL_CSS, unsafe_allow_html=True)

# Ensure patient data exists
if not os.path.exists("data/patients.csv"):
    write_csv()

def load_records(surge=False):
    rows = surge_patients(3) if surge else base_patients()
    return [dict(zip(COLS, r)) for r in rows]

# ---- Sidebar Navigation & Controls ----
with st.sidebar:
    st.markdown(
        """
        <div style='display:flex;align-items:center;gap:10px;margin-bottom:4px;'>
          <span style='font-size:1.6rem;'>🏥</span>
          <div>
            <div style='font-weight:800;font-size:1.25rem;color:var(--text);line-height:1.1;'>PatientTriage.ai</div>
            <div style='font-size:0.75rem;color:var(--muted);font-weight:600;letter-spacing:0.02em;'>CLINICAL DECISION SUPPORT</div>
          </div>
        </div>
        <div style='font-size:0.8rem;color:var(--muted);margin-bottom:18px;padding-bottom:14px;border-bottom:1px solid var(--border);'>
          Level 1 Trauma Center &middot; ED Pavilion
        </div>
        """,
        unsafe_allow_html=True,
    )
    
    st.markdown("<div class='sec-label'>Role-Based Workspace</div>", unsafe_allow_html=True)
    role_display = st.radio(
        "Viewing as", 
        ["Triage Nurse", "Charge Nurse", "Clinical Lead"],
        label_visibility="collapsed",
    )
    
    role_descriptions = {
        "Triage Nurse": "Patient arrival, vital sign assessment, automated ESI scoring & clinical override.",
        "Charge Nurse": "Live waiting-room flow, safe-wait threshold tracking & queue re-prioritization.",
        "Clinical Lead": "Quality oversight, triage distribution analytics & tamper-evident audit inspection.",
    }
    st.caption(role_descriptions[role_display])
    
    st.divider()
    st.markdown("<div class='sec-label'>Department Controls</div>", unsafe_allow_html=True)
    surge = st.toggle("Simulate Emergency Surge (3× Load)", help="Simulates a 3× volume surge to test adaptive safe-wait ceilings and re-ranking.")
    
    st.divider()
    st.markdown("<div class='sec-label'>Security & Integrity</div>", unsafe_allow_html=True)
    st.caption(
        "🔒 Encrypted at rest (Fernet) · Pseudonymized HMAC audit trail · "
        "RBAC-protected access. Decision-support prototype only — clinician judgment is final."
    )
    if st.button("Verify Audit Hash Chain", use_container_width=True):
        ok = audit.verify_chain()
        if ok:
            st.success("Audit Hash Chain Intact ✅ (SHA-256 verified)")
        else:
            st.error("Audit Chain Broken ❌")

# ---- Compute Triage State & Surge Metrics ----
records = load_records(surge)
surge_factor = compute_surge_factor(len(records), NORMAL_CAPACITY)
surge_active = surge_factor > SURGE_BANNER_THRESHOLD

if st.session_state.get("_surge_active") != surge_active:
    audit.log_event("SURGE_MODE_ON" if surge_active else "SURGE_MODE_OFF",
                         "SYSTEM", {"surge_factor": surge_factor,
                                    "queue_length": len(records),
                                    "capacity": NORMAL_CAPACITY})
    st.session_state["_surge_active"] = surge_active

scored = []
for rec in records:
    history = get_history(rec["patient_id"])
    res = score_patient(float(rec["age"]), triage_nurse.to_vitals(rec), rec["complaint"], history=history)
    scored.append((rec, res))

# ---- Top Header Bar ----
surge_pill = (f'<div class="pt-pill pt-pill-surge">🔴 SURGE ACTIVE &middot; {surge_factor}× CAPACITY</div>'
              if surge_active else "")
st.markdown(
    f"""
    <div class="pt-header">
      <div>
        <div class="brand">🏥 PatientTriage.ai</div>
        <div class="dept">Emergency Department &middot; Clinical Decision Support &middot; Level 1 Trauma Center</div>
      </div>
      <div class="pt-header-right">
        {surge_pill}
        <div class="pt-status"><span class="dot"></span>Live Clinical Engine Active</div>
        <div class="pt-pill">{role_display}</div>
      </div>
    </div>
    """,
    unsafe_allow_html=True,
)

# ---- Route View by Role ----
if role_display == "Triage Nurse":
    triage_nurse.render(scored, surge_factor, surge_active, role_display)
elif role_display == "Charge Nurse":
    charge_nurse.render(scored, surge_factor, surge_active, role_display)
else:
    clinical_lead.render(scored, surge_factor, surge_active, role_display)
