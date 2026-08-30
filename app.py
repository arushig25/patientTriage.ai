import os
import streamlit as st

from patient_triage.ui.styles import HOSPITAL_CSS
from patient_triage.data.simulator import write_csv, surge_patients, base_patients, COLS, get_history
from patient_triage.core.engine import Vitals, score_patient, compute_surge_factor, NORMAL_CAPACITY, SURGE_BANNER_THRESHOLD
from patient_triage.ui.views import triage_nurse, charge_nurse, clinical_lead
from patient_triage.security import audit

st.set_page_config(page_title="PatientTriage.ai", page_icon="🏥", layout="wide")
st.markdown(HOSPITAL_CSS, unsafe_allow_html=True)

if not os.path.exists("data/patients.csv"):
    write_csv()

def load_records(surge=False):
    rows = surge_patients(3) if surge else base_patients()
    return [dict(zip(COLS, r)) for r in rows]

with st.sidebar:
    st.markdown(
        "<div style='font-weight:800;font-size:1.15rem;color:var(--text);'>🏥 PatientTriage.ai</div>"
        "<div style='font-size:.78rem;color:var(--muted);margin-bottom:16px;'>Emergency Department workspace</div>",
        unsafe_allow_html=True,
    )
    st.markdown("<div class='sec-label'>Viewing as</div>", unsafe_allow_html=True)
    role_display = st.radio(
        "Viewing as", ["Triage Nurse", "Charge Nurse", "Clinical Lead"],
        label_visibility="collapsed",
    )
    st.caption("Role preview for this demo workspace.")
    st.divider()
    surge = st.toggle("Simulate surge (3× volume)")
    st.divider()
    st.caption(
        "🔒 Encrypted at rest · pseudonymized audit trail · "
        "RBAC-gated identity access. Simulated data only — "
        "decision-support tool; clinician judgment is final."
    )
    if st.button("Verify audit chain", use_container_width=True):
        ok = audit.verify_chain()
        st.success("Audit chain intact ✅") if ok else st.error("Chain broken ❌")

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

surge_pill = (f'<div class="pt-pill pt-pill-surge">🔴 SURGE · {surge_factor}×</div>'
              if surge_active else "")
st.markdown(
    f"""
    <div class="pt-header">
      <div>
        <div class="brand">🏥 PatientTriage.ai</div>
        <div class="dept">Emergency Department</div>
      </div>
      <div class="pt-header-right">
        {surge_pill}
        <div class="pt-status"><span class="dot"></span>System Operational</div>
        <div class="pt-pill">{role_display}</div>
      </div>
    </div>
    """,
    unsafe_allow_html=True,
)

if role_display == "Triage Nurse":
    triage_nurse.render(scored, surge_factor, surge_active, role_display)
elif role_display == "Charge Nurse":
    charge_nurse.render(scored, surge_factor, surge_active, role_display)
else:
    clinical_lead.render(scored, surge_factor, surge_active, role_display)
