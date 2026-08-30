"""
app.py -- PatientTriage.ai clinical workspace (Streamlit)
Run:  streamlit run app.py

Frontend only. All scoring, surge, audit, and privacy logic lives in
triage_engine.py / audit_log.py / privacy.py / data_simulator.py and is
unchanged by this file -- this module is presentation only.
"""

import os
import numpy as np
import pandas as pd
import plotly.graph_objects as go
import streamlit as st

from triage_engine import (
    Vitals, score_patient, wait_breach, compute_surge_factor,
    safe_wait_minutes, effective_urgency, NORMAL_CAPACITY,
    SURGE_BANNER_THRESHOLD, age_band, PEDS_NORMAL, _match_high_risk_complaint,
)
from data_simulator import write_csv, surge_patients, base_patients, COLS, get_history
import audit_log
import privacy

st.set_page_config(page_title="PatientTriage.ai", page_icon="🩺", layout="wide")

# ============================================================
# DESIGN SYSTEM
# ============================================================
# Palette: cool clinical neutrals + a restrained teal brand, with a
# fixed acuity color scale (red -> orange -> amber -> green -> blue)
# used consistently everywhere a level appears. Data-critical numbers
# (IDs, vitals, timestamps) are set in a monospace face -- the rest of
# the UI is a plain, highly legible grotesk. Nothing else earns color.

CSS = """
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&family=IBM+Plex+Mono:wght@500;600&display=swap');

:root{
  --bg:#F3F6F9; --surface:#FFFFFF; --surface-alt:#EDF1F5; --border:#DBE3EB;
  --text:#152232; --muted:#5C6B7C; --brand:#0E6E66; --brand-dark:#0A4F49;
  --navy:#0E2236;
  --l1:#C0392B; --l1-bg:#FBEAE8; --l1-bd:#F2C6C0;
  --l2:#C9631A; --l2-bg:#FCEEE1; --l2-bd:#F0CFA8;
  --l3:#A9790A; --l3-bg:#FBF3D9; --l3-bd:#EBD98F;
  --l4:#25864F; --l4-bg:#E7F5EC; --l4-bd:#B9E1C7;
  --l5:#2A5F9E; --l5-bg:#E9F1FA; --l5-bd:#BBD6F0;
}

html,body,[class*="css"]{ font-family:'Inter',-apple-system,sans-serif; color:var(--text); }
.stApp{ background:var(--bg); }
.mono{ font-family:'IBM Plex Mono',monospace; }
#MainMenu, footer, header[data-testid="stHeader"]{ visibility:hidden; height:0; }
.block-container{ padding-top:1.1rem; max-width:1180px; }

/* ---- App header bar ---- */
.pt-header{
  display:flex; justify-content:space-between; align-items:center;
  background:var(--navy); color:#fff; border-radius:14px;
  padding:16px 24px; margin-bottom:22px;
}
.pt-header .brand{ font-weight:800; font-size:1.28rem; letter-spacing:-.01em; }
.pt-header .dept{ font-size:.78rem; color:#9FB2C4; font-weight:500; margin-top:1px; }
.pt-header-right{ display:flex; align-items:center; gap:10px; }
.pt-status{ display:flex; align-items:center; gap:7px; font-size:.76rem; font-weight:600; color:#CFEFE0; }
.pt-status .dot{ width:7px; height:7px; border-radius:50%; background:#3FCF8E; box-shadow:0 0 0 3px rgba(63,207,142,.22); }
.pt-pill{ background:rgba(255,255,255,.10); border:1px solid rgba(255,255,255,.14); padding:6px 13px; border-radius:20px; font-size:.76rem; font-weight:600; }
.pt-pill-surge{ background:rgba(192,57,43,.85); border:1px solid rgba(255,255,255,.2); }

/* ---- Stat strip ---- */
.stat-row{ display:flex; gap:12px; margin-bottom:20px; flex-wrap:wrap; }
.stat-card{ flex:1; min-width:130px; background:var(--surface); border:1px solid var(--border); border-radius:12px; padding:14px 16px; }
.stat-card .n{ font-family:'IBM Plex Mono',monospace; font-size:1.6rem; font-weight:700; line-height:1; }
.stat-card .l{ font-size:.74rem; color:var(--muted); font-weight:600; text-transform:uppercase; letter-spacing:.04em; margin-top:5px; }
.stat-card.l1 .n{ color:var(--l1); } .stat-card.l2 .n{ color:var(--l2); }
.stat-card.l3 .n{ color:var(--l3); } .stat-card.neutral .n{ color:var(--text); }

/* ---- Section label ---- */
.sec-label{ font-size:.74rem; font-weight:700; text-transform:uppercase; letter-spacing:.06em; color:var(--muted); margin:2px 0 10px 0; }

/* ---- Acuity banner (the triage result) ---- */
.acuity-banner{ display:flex; gap:22px; align-items:center; border-radius:14px; padding:22px 26px; border:1px solid var(--BD); border-left:7px solid var(--COL); background:var(--BGC); margin-bottom:14px; }
.acuity-banner .lvl{ font-family:'IBM Plex Mono',monospace; font-weight:700; font-size:2.5rem; color:var(--COL); line-height:1; }
.acuity-banner .rt{ flex:1; }
.acuity-banner .lbl{ font-weight:800; font-size:1.02rem; letter-spacing:.02em; color:var(--COL); text-transform:uppercase; }
.acuity-banner .act{ font-size:1rem; font-weight:500; color:var(--text); margin-top:4px; }

/* ---- Chips ---- */
.chip{ display:inline-block; padding:3px 10px; border-radius:20px; font-size:.72rem; font-weight:700; letter-spacing:.02em; }
.chip-l1{ background:var(--l1-bg); color:var(--l1); } .chip-l2{ background:var(--l2-bg); color:var(--l2); }
.chip-l3{ background:var(--l3-bg); color:var(--l3); } .chip-l4{ background:var(--l4-bg); color:var(--l4); }
.chip-l5{ background:var(--l5-bg); color:var(--l5); }

/* ---- Cards ---- */
.card{ background:var(--surface); border:1px solid var(--border); border-radius:12px; padding:16px 18px; margin-bottom:14px; }
.card-title{ font-weight:700; font-size:.92rem; margin-bottom:8px; }

/* ---- Patient / queue card ---- */
.pcard{ display:flex; align-items:center; gap:14px; background:var(--surface); border:1px solid var(--border); border-left:5px solid var(--COL); border-radius:10px; padding:12px 16px; margin-bottom:9px; }
.pcard .pid{ font-family:'IBM Plex Mono',monospace; font-size:.72rem; color:var(--muted); font-weight:600; min-width:44px; }
.pcard .who{ min-width:190px; }
.pcard .who .nm{ font-weight:700; font-size:.93rem; }
.pcard .who .cc{ font-size:.8rem; color:var(--muted); }
.pcard .lvl{ font-family:'IBM Plex Mono',monospace; font-weight:700; color:var(--COL); font-size:.85rem; min-width:100px; }
.pcard .wait{ font-size:.82rem; color:var(--text); min-width:110px; }
.pcard .wait b{ font-family:'IBM Plex Mono',monospace; }
.pcard .flagbadge{ margin-left:auto; }

/* ---- Vitals grid ---- */
.vgrid{ display:grid; grid-template-columns:repeat(3,1fr); gap:10px; }
.vitem{ background:var(--surface-alt); border-radius:9px; padding:10px 12px; }
.vitem .lab{ font-size:.7rem; color:var(--muted); font-weight:600; text-transform:uppercase; letter-spacing:.03em; }
.vitem .val{ font-family:'IBM Plex Mono',monospace; font-weight:700; font-size:1.12rem; margin-top:2px; }
.vitem.warn .val{ color:var(--l2); } .vitem.crit .val{ color:var(--l1); }
.vitem .flag{ font-size:.68rem; font-weight:700; margin-top:1px; }
.vitem.warn .flag{ color:var(--l2); } .vitem.crit .flag{ color:var(--l1); }

/* ---- Reasons list ---- */
.reasons{ list-style:none; margin:0; padding:0; }
.reasons li{ padding:7px 0 7px 18px; border-bottom:1px solid var(--surface-alt); font-size:.87rem; position:relative; }
.reasons li:last-child{ border-bottom:none; }
.reasons li::before{ content:"•"; position:absolute; left:2px; color:var(--brand); font-weight:700; }

/* ---- Confidence bar ---- */
.conf-track{ background:var(--surface-alt); border-radius:6px; height:9px; width:100%; overflow:hidden; }
.conf-fill{ height:100%; border-radius:6px; }

/* ---- Alert / banner boxes ---- */
.abox{ border-radius:10px; padding:12px 15px; font-size:.86rem; margin-bottom:10px; border:1px solid; }
.abox-crit{ background:var(--l1-bg); border-color:var(--l1-bd); color:#7A2117; }
.abox-warn{ background:var(--l2-bg); border-color:var(--l2-bd); color:#7A430E; }
.abox-info{ background:var(--surface-alt); border-color:var(--border); color:var(--text); }
.abox-ok{ background:var(--l4-bg); border-color:var(--l4-bd); color:#155330; }
.abox b{ display:block; margin-bottom:2px; }

/* ---- Checklist ---- */
.checklist{ display:grid; grid-template-columns:repeat(2,1fr); gap:9px; }
.checkitem{ display:flex; gap:9px; align-items:flex-start; font-size:.87rem; background:var(--surface-alt); border-radius:9px; padding:10px 12px; }
.checkitem .tick{ color:var(--brand); font-weight:800; }

/* ---- Streamlit widget touch-ups ---- */
div[data-testid="stButton"] button{ border-radius:9px; font-weight:600; }
div[data-testid="stFormSubmitButton"] button{ border-radius:9px; font-weight:700; background:var(--brand); color:#fff; border:none; }
div[data-testid="stFormSubmitButton"] button:hover{ background:var(--brand-dark); }
section[data-testid="stSidebar"]{ background:var(--surface); border-right:1px solid var(--border); }
div[data-testid="stMetric"]{ background:var(--surface); border:1px solid var(--border); border-radius:10px; padding:10px 14px; }
hr{ border-color:var(--border); }
</style>
"""
st.markdown(CSS, unsafe_allow_html=True)

ACUITY_META = {
    1: {"label": "Resuscitation", "desc": "Immediate life-threatening emergency", "c": "l1"},
    2: {"label": "Emergent",      "desc": "Immediate physician assessment",       "c": "l2"},
    3: {"label": "Urgent",        "desc": "Timely assessment",                    "c": "l3"},
    4: {"label": "Less Urgent",   "desc": "Standard queue",                       "c": "l4"},
    5: {"label": "Non-Urgent",    "desc": "Fast-track / minor care",              "c": "l5"},
}
CONF_COLOR = {"High": "l4", "Moderate": "l3", "Low": "l1"}
HEX = {"l1": "#C0392B", "l2": "#C9631A", "l3": "#A9790A", "l4": "#25864F", "l5": "#2A5F9E"}
BG = {"l1": "#FBEAE8", "l2": "#FCEEE1", "l3": "#FBF3D9", "l4": "#E7F5EC", "l5": "#E9F1FA"}
BD = {"l1": "#F2C6C0", "l2": "#F0CFA8", "l3": "#EBD98F", "l4": "#B9E1C7", "l5": "#BBD6F0"}


def chip(level):
    m = ACUITY_META[level]
    return f'<span class="chip chip-{m["c"]}">LEVEL {level} · {m["label"].upper()}</span>'


# ============================================================
# DATA
# ============================================================
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
        on_o2 = on_o2.lower() in ("true", "1", "yes")
    return Vitals(hr=num(rec["hr"]), rr=num(rec["rr"]), spo2=num(rec["spo2"]),
                  sbp=num(rec["sbp"]), temp=num(rec["temp"]),
                  avpu=_clean(rec["avpu"]), on_oxygen=on_o2)


# ============================================================
# SIDEBAR
# ============================================================
with st.sidebar:
    st.markdown(
        "<div style='font-weight:800;font-size:1.15rem;color:var(--navy);'>🩺 PatientTriage.ai</div>"
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
        ok = audit_log.verify_chain()
        st.success("Audit chain intact ✅") if ok else st.error("Chain broken ❌")

role = {"Triage Nurse": "Triage Nurse", "Charge Nurse": "Charge Nurse (Flow)",
        "Clinical Lead": "Clinical Lead"}[role_display]

records = load_records(surge)
surge_factor = compute_surge_factor(len(records), NORMAL_CAPACITY)
surge_active = surge_factor > SURGE_BANNER_THRESHOLD

if st.session_state.get("_surge_active") != surge_active:
    audit_log.log_event("SURGE_MODE_ON" if surge_active else "SURGE_MODE_OFF",
                         "SYSTEM", {"surge_factor": surge_factor,
                                    "queue_length": len(records),
                                    "capacity": NORMAL_CAPACITY})
    st.session_state["_surge_active"] = surge_active

scored = []
for rec in records:
    history = get_history(rec["patient_id"])
    res = score_patient(float(rec["age"]), to_vitals(rec), rec["complaint"], history=history)
    scored.append((rec, res))

n_total = len(scored)
n_l1 = sum(1 for _, r in scored if r.acuity == 1)
n_l2 = sum(1 for _, r in scored if r.acuity == 2)
n_l3 = sum(1 for _, r in scored if r.acuity == 3)

# ============================================================
# HEADER
# ============================================================
surge_pill = (f'<div class="pt-pill pt-pill-surge">🔴 SURGE · {surge_factor}×</div>'
              if surge_active else "")
st.markdown(
    f"""
    <div class="pt-header">
      <div>
        <div class="brand">PatientTriage.ai</div>
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

# ============================================================
# VIEW 1 — TRIAGE NURSE
# ============================================================
if role == "Triage Nurse":
    st.markdown(
        f"""
        <div class="stat-row">
          <div class="stat-card neutral"><div class="n">{n_total}</div><div class="l">Active patients</div></div>
          <div class="stat-card l1"><div class="n">{n_l1}</div><div class="l">Immediate (L1)</div></div>
          <div class="stat-card l2"><div class="n">{n_l2}</div><div class="l">Emergent (L2)</div></div>
          <div class="stat-card l3"><div class="n">{n_l3}</div><div class="l">Urgent (L3)</div></div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    names = [f'{r["patient_id"]} — {r["name"]} ({int(float(r["age"]))}y)' for r, _ in scored]
    idx = st.selectbox("Select arriving / in-progress patient", range(len(names)),
                        format_func=lambda i: names[i])
    rec, res = scored[idx]
    v = to_vitals(rec)
    age = float(rec["age"])
    band = age_band(age)
    m = ACUITY_META[res.acuity]

    left, right = st.columns([1, 1.15], gap="large")

    with left:
        st.markdown("<div class='sec-label'>Patient</div>", unsafe_allow_html=True)
        st.markdown(
            f"""<div class="card">
                  <div style="display:flex;justify-content:space-between;align-items:baseline;">
                    <div>
                      <div style="font-weight:800;font-size:1.15rem;">{rec['name']}</div>
                      <div style="color:var(--muted);font-size:.85rem;">{int(age)} years ·
                        <span class="mono">{rec['patient_id']}</span></div>
                    </div>
                  </div>
                  <div style="margin-top:10px;font-size:.9rem;"><b>Chief complaint</b><br>{rec['complaint'].capitalize()}</div>
                </div>""",
            unsafe_allow_html=True,
        )

        cat, phrase = _match_high_risk_complaint(rec["complaint"])
        if cat:
            st.markdown(
                f"""<div class="abox abox-warn"><b>✓ Recognized as {cat.replace('_',' ').title()}</b>
                    Matched on "{phrase}" — this may raise the minimum triage priority.</div>""",
                unsafe_allow_html=True,
            )

        if band in PEDS_NORMAL:
            st.markdown(
                f"""<div class="abox abox-info"><b>🧒 Pediatric assessment</b>
                    Age {int(age)} — vitals are interpreted using age-specific pediatric
                    reference ranges, not adult thresholds.</div>""",
                unsafe_allow_html=True,
            )

        st.markdown("<div class='sec-label' style='margin-top:6px;'>Vital signs</div>", unsafe_allow_html=True)

        def vcell(label, val, unit, warn=False, crit=False, flagtext=None):
            cls = "crit" if crit else ("warn" if warn else "")
            fv = "—" if val is None else (f"{val:g}" if isinstance(val, float) else val)
            flag_html = f'<div class="flag">{flagtext}</div>' if (warn or crit) and flagtext else ""
            return f'<div class="vitem {cls}"><div class="lab">{label}</div><div class="val">{fv} {unit if val is not None else ""}</div>{flag_html}</div>'

        hr_warn, hr_crit = (v.hr is not None and v.hr >= 100), (v.hr is not None and (v.hr >= 140 or v.hr < 45))
        rr_warn, rr_crit = (v.rr is not None and v.rr >= 22), (v.rr is not None and v.rr >= 30)
        spo2_warn, spo2_crit = (v.spo2 is not None and v.spo2 < 94), (v.spo2 is not None and v.spo2 < 90)
        sbp_warn, sbp_crit = (v.sbp is not None and v.sbp < 100), (v.sbp is not None and v.sbp < 90)

        vhtml = "<div class='vgrid'>"
        vhtml += vcell("Heart rate", v.hr, "bpm", hr_warn, hr_crit, "🚨 Critical" if hr_crit else ("⚠ High" if hr_warn else None))
        vhtml += vcell("Resp. rate", v.rr, "/min", rr_warn, rr_crit, "🚨 Critical" if rr_crit else ("⚠ High" if rr_warn else None))
        vhtml += vcell("SpO₂", v.spo2, "%", spo2_warn, spo2_crit, "🚨 Critical" if spo2_crit else ("⚠ Low" if spo2_warn else None))
        vhtml += vcell("Systolic BP", v.sbp, "mmHg", sbp_warn, sbp_crit, "🚨 Critical" if sbp_crit else ("⚠ Low" if sbp_warn else None))
        vhtml += vcell("Temperature", v.temp, "°C")
        vhtml += vcell("Consciousness", v.avpu, "")
        vhtml += "</div>"
        st.markdown(vhtml, unsafe_allow_html=True)

        st.markdown("<div class='sec-label' style='margin-top:14px;'>Patient history</div>", unsafe_allow_html=True)
        has_hist = str(rec["has_history"]).lower() not in ("false", "0", "")
        history = get_history(rec["patient_id"])
        if not has_hist:
            st.markdown(
                """<div class="abox abox-info"><b>No documented history</b>
                First-time patient — assessed using current observed clinical
                information only.</div>""",
                unsafe_allow_html=True,
            )
        elif history:
            conds = ", ".join(history["chronic_conditions"]) or "None on file"
            st.markdown(
                f"""<div class="abox abox-ok"><b>📋 Documented baseline on file</b>
                Baseline HR {history['baseline_hr']} bpm · Baseline SBP {history['baseline_sbp']} mmHg ·
                Chronic conditions: {conds} · Last visit {history['last_visit_date']}
                (Level {history['last_visit_acuity']}).</div>""",
                unsafe_allow_html=True,
            )
        else:
            st.markdown(
                """<div class="abox abox-warn"><b>Returning patient — no usable baseline</b>
                A previous record exists, but no documented clinical baseline is
                available for comparison. Scored the same as a first-time patient.</div>""",
                unsafe_allow_html=True,
            )

        with st.expander("🔒 Data protection — what's stored for this patient"):
            for field in ("patient_id", "name", "age", "vitals", "complaint", "history"):
                purpose, retention = privacy.FIELD_MINIMIZATION[field]
                st.caption(f"**{field}** — {purpose}. Retention: {retention}.")

    with right:
        st.markdown("<div class='sec-label'>Triage recommendation</div>", unsafe_allow_html=True)
        st.markdown(
            f"""<div class="acuity-banner" style="--COL:{HEX[m['c']]};--BGC:{BG[m['c']]};--BD:{BD[m['c']]}">
                  <div class="lvl">L{res.acuity}</div>
                  <div class="rt">
                    <div class="lbl">{m['label']} — {m['desc']}</div>
                    <div class="act">{res.recommended_action}</div>
                  </div>
                </div>""",
            unsafe_allow_html=True,
        )

        if res.red_flags:
            flags_html = "".join(f"<li>{f}</li>" for f in res.red_flags)
            st.markdown(
                f"""<div class="abox abox-crit">
                    <b>🚨 Safety alert — {len(res.red_flags)} red flag(s) detected</b>
                    <ul class="reasons" style="margin-top:6px;">{flags_html}</ul>
                    These findings escalate priority and cannot be relaxed by history.
                    </div>""",
                unsafe_allow_html=True,
            )

        cc = CONF_COLOR[res.confidence_label]
        st.markdown("<div class='card'>", unsafe_allow_html=True)
        st.markdown(
            f"""<div style="display:flex;justify-content:space-between;align-items:baseline;">
                  <div class="card-title" style="margin-bottom:0;">Confidence</div>
                  <div style="font-family:'IBM Plex Mono',monospace;font-weight:700;color:{HEX[cc]};">
                    {int(res.confidence*100)}% · {res.confidence_label.upper()}
                  </div>
                </div>
                <div class="conf-track" style="margin-top:8px;">
                  <div class="conf-fill" style="width:{int(res.confidence*100)}%;background:{HEX[cc]};"></div>
                </div>""",
            unsafe_allow_html=True,
        )
        if res.confidence_label == "Low":
            st.markdown(
                "<div style='margin-top:10px;' class='abox abox-warn'><b>⚠ Safety escalation applied</b>"
                " Priority was raised because important clinical information is missing or incomplete."
                " Consider retaking a complete set of vitals.</div>",
                unsafe_allow_html=True,
            )
        st.markdown("</div>", unsafe_allow_html=True)

        st.markdown("<div class='card'><div class='card-title'>Why this recommendation</div>", unsafe_allow_html=True)
        st.markdown("<ul class='reasons'>" + "".join(f"<li>{r}</li>" for r in res.reasons) + "</ul></div>",
                    unsafe_allow_html=True)

    if audit_log.should_log_score(st.session_state, rec["patient_id"], res.acuity):
        audit_log.log_event("SCORE", rec["patient_id"],
                             {"acuity": res.acuity, "ews": res.ews_score,
                              "confidence": res.confidence_label})
    if audit_log.should_log_access(st.session_state, rec["patient_id"]):
        audit_log.log_event("ACCESS", rec["patient_id"],
                             {"fields": ["name", "vitals", "complaint"], "viewer_role": role})

    st.markdown("<div class='sec-label' style='margin-top:6px;'>Clinician decision</div>", unsafe_allow_html=True)
    with st.form("override"):
        c1, c2, c3 = st.columns([1, 2, 1])
        new_acuity = c1.selectbox("Override acuity to", [1, 2, 3, 4, 5], index=res.acuity - 1)
        reason = c2.text_input("Reason for override (required, logged)")
        clinician = c3.text_input("Clinician ID", value="RN-1042")
        submitted = st.form_submit_button("Confirm / record decision", use_container_width=True)
    if submitted:
        if new_acuity == res.acuity:
            st.info("Recommendation confirmed as-is — no override recorded.")
        elif not reason.strip():
            st.error("A reason is required to record an override.")
        else:
            audit_log.log_event("OVERRIDE", rec["patient_id"],
                                 {"from_acuity": res.acuity, "to_acuity": new_acuity, "reason": reason},
                                 actor=clinician)
            st.success(f"✓ Override recorded — Level {res.acuity} → Level {new_acuity} by {clinician}. "
                       f"Added to the audit trail. Chain intact: {audit_log.verify_chain()}")

# ============================================================
# VIEW 2 — CHARGE NURSE / WAITING ROOM
# ============================================================
elif role == "Charge Nurse (Flow)":
    rng = np.random.default_rng(7)
    board = []
    for rec, res in scored:
        waited = int(rng.integers(0, 90))
        limit = safe_wait_minutes(res.acuity, surge_factor)
        breach = wait_breach(res.acuity, waited, surge_factor)
        urgency = effective_urgency(res.acuity, waited, res.confidence_label)
        board.append({"rec": rec, "res": res, "waited": waited, "limit": limit,
                       "breach": breach, "urgency": urgency})
        if audit_log.should_log_alert(st.session_state, rec["patient_id"], breach):
            audit_log.log_event("ALERT", rec["patient_id"],
                                 {"type": "wait_breach", "acuity": res.acuity, "waited": waited,
                                  "safe_limit": limit, "surge_factor": surge_factor})
    board.sort(key=lambda b: b["urgency"])
    n_breach = sum(1 for b in board if b["breach"])

    st.markdown(
        f"""
        <div class="stat-row">
          <div class="stat-card neutral"><div class="n">{n_total}</div><div class="l">Patients waiting</div></div>
          <div class="stat-card l1"><div class="n">{n_l1}</div><div class="l">Immediate</div></div>
          <div class="stat-card l2"><div class="n">{n_l2}</div><div class="l">Urgent</div></div>
          <div class="stat-card l1"><div class="n">{n_breach}</div><div class="l">Reassess now</div></div>
          <div class="stat-card neutral"><div class="n">{surge_factor}×</div><div class="l">Current load</div></div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    if surge_active:
        base60 = safe_wait_minutes(4, 1.0)
        cur60 = safe_wait_minutes(4, surge_factor)
        st.markdown(
            f"""<div class="abox abox-crit">
                <b>🔴 SURGE MODE ACTIVE — {surge_factor}× normal capacity</b>
                Safe waiting thresholds have tightened and the board below is
                re-ranked live. Example: a Level 4 patient's safe wait is now
                {cur60} min, down from {base60} min under normal load.
                </div>""",
            unsafe_allow_html=True,
        )
    else:
        st.markdown(
            "<div class='abox abox-ok'><b>✓ Normal operating load</b> "
            "Standard safe-wait targets are in effect.</div>",
            unsafe_allow_html=True,
        )

    st.markdown("<div class='sec-label'>Waiting-room board — highest priority first</div>", unsafe_allow_html=True)
    for b in board:
        rec, res = b["rec"], b["res"]
        m = ACUITY_META[res.acuity]
        status = (f'<span class="chip chip-l1">🚨 REASSESS NOW</span>' if b["breach"]
                  else f'<span style="font-size:.78rem;color:var(--muted);">within safe wait</span>')
        why = ""
        if res.confidence_label == "Low" and not b["breach"]:
            why = '<div style="font-size:.75rem;color:var(--l1);margin-top:2px;">⚠ Low-confidence assessment — moved up in priority</div>'
        st.markdown(
            f"""<div class="pcard" style="--COL:{HEX[m['c']]}">
                  <div class="pid">{rec['patient_id']}</div>
                  <div class="who"><div class="nm">{rec['name']} <span style="font-weight:400;color:var(--muted);">· {int(float(rec['age']))}y</span></div>
                    <div class="cc">{rec['complaint'].capitalize()}</div></div>
                  <div class="lvl">L{res.acuity} · {m['label']}</div>
                  <div class="wait">Waited <b>{b['waited']}</b> min · safe limit <b>{b['limit']}</b> min{why}</div>
                  <div class="flagbadge">{status}</div>
                </div>""",
            unsafe_allow_html=True,
        )

# ============================================================
# VIEW 3 — CLINICAL LEAD
# ============================================================
else:
    log_all = audit_log.read_log()
    n_overrides = sum(1 for e in log_all if e.get("event_type") == "OVERRIDE")
    n_alerts = sum(1 for e in log_all if e.get("event_type") == "ALERT")
    n_lowconf = sum(1 for _, r in scored if r.confidence_label == "Low")

    st.markdown(
        f"""
        <div class="stat-row">
          <div class="stat-card neutral"><div class="n">{n_total}</div><div class="l">Patients assessed</div></div>
          <div class="stat-card l1"><div class="n">{n_l1 + n_l2}</div><div class="l">Level 1–2</div></div>
          <div class="stat-card l3"><div class="n">{n_lowconf}</div><div class="l">Low-confidence</div></div>
          <div class="stat-card neutral"><div class="n">{n_alerts}</div><div class="l">Reassess alerts</div></div>
          <div class="stat-card neutral"><div class="n">{n_overrides}</div><div class="l">Overrides</div></div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    c1, c2 = st.columns([1.3, 1], gap="large")
    with c1:
        st.markdown("<div class='sec-label'>Acuity distribution</div>", unsafe_allow_html=True)
        accdf = pd.DataFrame([{"acuity": r.acuity} for _, r in scored])
        dist = accdf["acuity"].value_counts().reindex([1, 2, 3, 4, 5], fill_value=0).reset_index()
        dist.columns = ["Acuity", "Count"]
        colors = [HEX[ACUITY_META[a]["c"]] for a in dist["Acuity"]]
        fig = go.Figure(go.Bar(
            x=[f"L{a}" for a in dist["Acuity"]], y=dist["Count"],
            marker_color=colors, text=dist["Count"], textposition="outside",
        ))
        fig.update_layout(
            height=280, margin=dict(l=10, r=10, t=10, b=10),
            plot_bgcolor="white", paper_bgcolor="white",
            font=dict(family="Inter", color="#152232"),
            yaxis=dict(gridcolor="#EDF1F5", zeroline=False),
            xaxis=dict(showgrid=False),
        )
        st.plotly_chart(fig, use_container_width=True, config={"displayModeBar": False})

    with c2:
        st.markdown("<div class='sec-label'>Safety & trust</div>", unsafe_allow_html=True)
        checks = [
            "Age-aware pediatric thresholds", "Red-flag safety overrides",
            "Uncertainty escalation", "Explainable complaint matching",
            "Clinician override available", "Audit trail active",
            "Patient identifiers protected", "Baseline-aware scoring",
        ]
        html = "<div class='checklist'>" + "".join(
            f'<div class="checkitem"><span class="tick">✓</span>{c}</div>' for c in checks
        ) + "</div>"
        st.markdown(html, unsafe_allow_html=True)

    st.markdown("<div class='sec-label' style='margin-top:8px;'>Audit log</div>", unsafe_allow_html=True)
    st.caption("Patient identifiers in the log are pseudonymized tokens. "
               "Authorize below to re-link tokens to real patient IDs for review — "
               "identity access is itself audited.")
    pw = st.text_input("Clinical Lead authorization password", type="password", key="lead_pw")
    authorized = privacy.check_role_access("Clinical Lead", pw)
    log = log_all[-15:]
    if not log:
        st.info("No events yet — use the Triage Nurse view to generate some.")
    else:
        df = pd.DataFrame(log)[["ts", "event_type", "patient_id", "actor"]]
        df.columns = ["Time", "Event", "Patient", "Actor"]
        if authorized:
            df["Patient"] = df["Patient"].apply(
                lambda t: audit_log.resolve_identity(t, "Clinical Lead", pw))
            st.markdown("<div class='abox abox-ok'><b>🔓 Authorized</b> Identifiers re-linked below.</div>",
                        unsafe_allow_html=True)
        else:
            st.markdown(
                "<div class='abox abox-info'><b>🔒 Not authorized</b> Showing pseudonymous tokens only.</div>",
                unsafe_allow_html=True,
            )
        st.dataframe(df, use_container_width=True, hide_index=True)
        st.caption(f"Hash chain intact: {audit_log.verify_chain()}")

    with st.expander("🔒 Privacy & compliance"):
        st.markdown(
            "**Jurisdiction:** United States — HIPAA (prototype assumption, not a "
            "production HIPAA certification).\n\n"
            "**Retention:** raw vitals & identifiers 7 years · audit records retained "
            "indefinitely (pseudonymized, hash-chained) · de-identified aggregate scores "
            "retained for model monitoring.\n\n"
            "**Consent:** triage-time data collection falls under implied consent for "
            "emergency care; ongoing reassessment is part of the same care episode."
        )
        st.caption("Field-level data minimization:")
        for field, (purpose, retention) in privacy.FIELD_MINIMIZATION.items():
            st.caption(f"**{field}** — {purpose}. Retention: {retention}.")
