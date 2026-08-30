import numpy as np
import streamlit as st
from patient_triage.core.engine import (safe_wait_minutes, wait_breach, effective_urgency)
from patient_triage.security import audit
from patient_triage.ui.components import (ACUITY_META, HEX, chip, section_label, alert_box)

def render(scored, surge_factor, surge_active, role_display):
    rng = np.random.default_rng(7)
    board = []
    
    n_total = len(scored)
    n_l1 = sum(1 for _, r in scored if r.acuity == 1)
    n_l2 = sum(1 for _, r in scored if r.acuity == 2)
    
    for rec, res in scored:
        waited = int(rng.integers(0, 90))
        limit = safe_wait_minutes(res.acuity, surge_factor)
        breach = wait_breach(res.acuity, waited, surge_factor)
        urgency = effective_urgency(res.acuity, waited, res.confidence_label)
        board.append({"rec": rec, "res": res, "waited": waited, "limit": limit,
                       "breach": breach, "urgency": urgency})
        if audit.should_log_alert(st.session_state, rec["patient_id"], breach):
            audit.log_event("ALERT", rec["patient_id"],
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
          <div class="stat-card neutral"><div class="n">{surge_factor}&times;</div><div class="l">Current load</div></div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    if surge_active:
        base60 = safe_wait_minutes(4, 1.0)
        cur60 = safe_wait_minutes(4, surge_factor)
        st.markdown(
            alert_box("crit", f"🔴 SURGE MODE ACTIVE &mdash; {surge_factor}&times; normal capacity", 
                      f"Safe waiting thresholds have tightened and the board below is re-ranked live. Example: a Level 4 patient's safe wait is now {cur60} min, down from {base60} min under normal load."),
            unsafe_allow_html=True,
        )
    else:
        st.markdown(
            alert_box("ok", "✓ Normal operating load", "Standard safe-wait targets are in effect."),
            unsafe_allow_html=True,
        )

    st.markdown(section_label('Waiting-room board &mdash; highest priority first'), unsafe_allow_html=True)
    for b in board:
        rec, res = b["rec"], b["res"]
        m = ACUITY_META[res.acuity]
        status = (f'<span class="chip chip-l1">🚨 REASSESS NOW</span>' if b["breach"]
                  else f'<span style="font-size:.78rem;color:var(--muted);">within safe wait</span>')
        why = ""
        if res.confidence_label == "Low" and not b["breach"]:
            why = '<div style="font-size:.75rem;color:var(--l1);margin-top:2px;">⚠ Low-confidence assessment &mdash; moved up in priority</div>'
        st.markdown(
            f"""<div class="pcard" style="--COL:{HEX[m['c']]}">
                  <div class="pid">{rec['patient_id']}</div>
                  <div class="who"><div class="nm">{rec['name']} <span style="font-weight:400;color:var(--muted);">&middot; {int(float(rec['age']))}y</span></div>
                    <div class="cc">{rec['complaint'].capitalize()}</div></div>
                  <div class="lvl">L{res.acuity} &middot; {m['label']}</div>
                  <div class="wait">Waited <b>{b['waited']}</b> min &middot; safe limit <b>{b['limit']}</b> min{why}</div>
                  <div class="flagbadge">{status}</div>
                </div>""",
            unsafe_allow_html=True,
        )
