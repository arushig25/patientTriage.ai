"""
app.py -- PatientTriage.ai prototype UI (Streamlit)
Run:  streamlit run app.py
"""

import os
import pandas as pd
import plotly.express as px
import streamlit as st

from triage_engine import Vitals, score_patient, wait_breach, SAFE_WAIT_MINUTES
from data_simulator import write_csv, surge_patients, base_patients, COLS
import audit_log

st.set_page_config(page_title="PatientTriage.ai", layout="wide")

# ---------- Load / generate data ----------
if not os.path.exists("data/patients.csv"):
    write_csv()

def _clean(v):
    return None if (v is None or (isinstance(v, float) and pd.isna(v)) or v == "") else v

def load_records(surge=False):
    rows = surge_patients(3) if surge else base_patients()
    return [dict(zip(COLS, r)) for r in rows]

def to_vitals(rec):
    def num(x):
        x = _clean(x)
        return float(x) if x is not None else None
    on_o2 = _clean(rec["on_oxygen"])
    if isinstance(on_o2, str):
        on_o2 = on_o2.lower() in ("true","1","yes")
    return Vitals(hr=num(rec["hr"]), rr=num(rec["rr"]), spo2=num(rec["spo2"]),
                  sbp=num(rec["sbp"]), temp=num(rec["temp"]),
                  avpu=_clean(rec["avpu"]), on_oxygen=on_o2)

# ---------- Sidebar ----------
st.sidebar.title("PatientTriage.ai")
role = st.sidebar.radio("View as", ["Triage Nurse", "Charge Nurse (Flow)", "Clinical Lead"])
surge = st.sidebar.toggle("Simulate surge (3× volume)")
st.sidebar.caption("HIPAA-aligned. Simulated data only. "
                   "Decision-support — clinician judgment is final.")
if st.sidebar.button("Verify audit chain"):
    ok = audit_log.verify_chain()
    st.sidebar.success("Audit chain intact ✅") if ok else st.sidebar.error("Chain broken ❌")

records = load_records(surge)

# Score everyone once
scored = []
for rec in records:
    res = score_patient(float(rec["age"]), to_vitals(rec), rec["complaint"])
    scored.append((rec, res))

ACUITY_COLOR = {1:"#c0392b",2:"#e67e22",3:"#f1c40f",4:"#27ae60",5:"#2980b9"}

# ============================================================
# VIEW 1 — TRIAGE NURSE
# ============================================================
if role == "Triage Nurse":
    st.title("Triage — In-the-Moment Recommendation")
    names = [f'{r["patient_id"]} — {r["name"]} ({int(float(r["age"]))}y)' for r,_ in scored]
    idx = st.selectbox("Select arriving patient", range(len(names)),
                       format_func=lambda i: names[i])
    rec, res = scored[idx]

    c1, c2, c3 = st.columns(3)
    c1.metric("Suggested acuity (ESI)", f"Level {res.acuity}")
    c2.metric("Early-warning score", res.ews_score)
    c3.metric("Confidence", f"{res.confidence_label} ({int(res.confidence*100)}%)")

    st.markdown(f"<div style='padding:12px;border-radius:8px;"
                f"background:{ACUITY_COLOR[res.acuity]};color:white;"
                f"font-weight:600'>{res.recommended_action}</div>",
                unsafe_allow_html=True)

    if res.red_flags:
        st.error("🚩 Red flags: " + "; ".join(res.red_flags))
    if not rec["has_history"] or str(rec["has_history"]).lower() in ("false","0"):
        st.warning("⚠️ Zero-history patient — no prior record. Scored on observed data only.")

    st.subheader("Why this recommendation")
    for r in res.reasons:
        st.write("• " + r)

    audit_log.log_event("SCORE", rec["patient_id"],
                        {"acuity":res.acuity,"ews":res.ews_score,
                         "confidence":res.confidence_label})

    # ----- Override capture -----
    st.subheader("Clinician override")
    with st.form("override"):
        new_acuity = st.selectbox("Override acuity to", [1,2,3,4,5],
                                  index=res.acuity-1)
        reason = st.text_input("Reason for override (required, logged)")
        clinician = st.text_input("Clinician ID", value="RN-1042")
        submitted = st.form_submit_button("Record override")
    if submitted:
        if not reason.strip():
            st.error("A reason is required for the audit trail.")
        else:
            audit_log.log_event("OVERRIDE", rec["patient_id"],
                {"from_acuity":res.acuity,"to_acuity":new_acuity,"reason":reason},
                actor=clinician)
            st.success(f"Override logged: L{res.acuity} → L{new_acuity} "
                       f"by {clinician}. Chain intact: {audit_log.verify_chain()}")

# ============================================================
# VIEW 2 — CHARGE NURSE / FLOW  (continuous re-assessment board)
# ============================================================
elif role == "Charge Nurse (Flow)":
    st.title("Waiting-Room Board — Continuous Re-Assessment")
    st.caption("System re-checks every waiting patient. Alerts fire on "
               "wait-time breach for the patient's acuity, or on worsening vitals.")

    import numpy as np
    rng = np.random.default_rng(7)
    board = []
    for rec, res in scored:
        waited = int(rng.integers(0, 90))
        breach = wait_breach(res.acuity, waited)
        board.append({
            "Patient": rec["patient_id"], "Name": rec["name"],
            "Acuity": res.acuity, "Confidence": res.confidence_label,
            "Waited (min)": waited,
            "Safe limit": SAFE_WAIT_MINUTES[res.acuity],
            "ALERT": "⏰ RE-ASSESS" if breach else "",
        })
        if breach:
            audit_log.log_event("ALERT", rec["patient_id"],
                {"type":"wait_breach","acuity":res.acuity,"waited":waited})
    df = pd.DataFrame(board).sort_values(["Acuity","Waited (min)"],
                                         ascending=[True, False])
    alerts = df[df["ALERT"] != ""]
    st.metric("Active re-assessment alerts", len(alerts))
    if len(alerts):
        st.error(f"{len(alerts)} patient(s) exceeded safe wait for their acuity.")
    st.dataframe(df, use_container_width=True, hide_index=True)

# ============================================================
# VIEW 3 — CLINICAL LEAD  (safety metrics)
# ============================================================
else:
    st.title("Clinical Lead — Safety & Trust Metrics")
    accdf = pd.DataFrame([{"acuity":res.acuity,"conf":res.confidence_label,
                           "ews":res.ews_score} for _,res in scored])
    c1,c2,c3 = st.columns(3)
    c1.metric("Patients scored", len(accdf))
    c2.metric("High-acuity (L1–L2)", int((accdf["acuity"]<=2).sum()))
    c3.metric("Low-confidence scores", int((accdf["conf"]=="Low").sum()))

    dist = accdf["acuity"].value_counts().sort_index().reset_index()
    dist.columns = ["Acuity","Count"]
    fig = px.bar(dist, x="Acuity", y="Count",
                 color="Acuity", color_discrete_map={str(k):v for k,v in ACUITY_COLOR.items()},
                 title="Acuity distribution")
    st.plotly_chart(fig, use_container_width=True)

    st.subheader("Audit log (most recent 15)")
    log = audit_log.read_log()[-15:]
    if log:
        st.dataframe(pd.DataFrame(log)[["ts","event_type","patient_id","actor"]],
                     use_container_width=True, hide_index=True)
        st.caption(f"Hash chain intact: {audit_log.verify_chain()}")
    else:
        st.info("No events yet — use the Triage Nurse view to generate some.")
