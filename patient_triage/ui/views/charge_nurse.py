import numpy as np
import streamlit as st
from patient_triage.core.engine import (safe_wait_minutes, wait_breach, effective_urgency)
from patient_triage.security import audit
from patient_triage.ui.components import (ACUITY_META, HEX, chip, section_label, alert_box, render_html)

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

    render_html(
        f"""
        <div class="stat-row">
          <div class="stat-card neutral"><div class="n">{n_total}</div><div class="l">Waiting Room Queue</div></div>
          <div class="stat-card l1"><div class="n">{n_l1}</div><div class="l">Immediate (L1)</div></div>
          <div class="stat-card l2"><div class="n">{n_l2}</div><div class="l">Emergent (L2)</div></div>
          <div class="stat-card l1"><div class="n">{n_breach}</div><div class="l">Safe-Wait Breaches</div></div>
          <div class="stat-card neutral"><div class="n">{surge_factor}×</div><div class="l">Current Volume Surge</div></div>
        </div>
        """
    )

    if surge_active:
        base60 = safe_wait_minutes(4, 1.0)
        cur60 = safe_wait_minutes(4, surge_factor)
        render_html(
            alert_box("crit", f"🔴 SURGE PROTOCOL ACTIVE — {surge_factor}× Normal Department Load", 
                      f"Safe waiting thresholds have tightened across non-critical tiers. Waiting-room board below is dynamically re-ranked. (Example: Level 4 threshold shortened from {base60} min to {cur60} min).")
        )
    else:
        render_html(
            alert_box("ok", "✓ Normal Operational Flow", "Safe-wait thresholds are calibrated at standard baselines.")
        )

    st.markdown(section_label('📋 Live Waiting-Room Priority Queue (Highest Clinical Risk First)'), unsafe_allow_html=True)
    
    # Filter controls
    f_col1, f_col2 = st.columns([2, 1])
    with f_col1:
        search_query = st.text_input("🔍 Quick Search Patient or Complaint", placeholder="Search by name, ID, or symptom...", label_visibility="collapsed")
    with f_col2:
        filter_status = st.selectbox("Queue Filter", ["All Patients", "Breaches Only (Reassess Now)", "Level 1 & 2 Only"], label_visibility="collapsed")

    filtered_board = board
    if filter_status == "Breaches Only (Reassess Now)":
        filtered_board = [b for b in filtered_board if b["breach"]]
    elif filter_status == "Level 1 & 2 Only":
        filtered_board = [b for b in filtered_board if b["res"].acuity in (1, 2)]

    if search_query.strip():
        q = search_query.lower()
        filtered_board = [b for b in filtered_board if q in b["rec"]["name"].lower() or q in b["rec"]["patient_id"].lower() or q in b["rec"]["complaint"].lower()]

    if not filtered_board:
        st.info("No patients match current filter criteria.")

    for b in filtered_board:
        rec, res = b["rec"], b["res"]
        m = ACUITY_META[res.acuity]
        status = (f'<span class="chip chip-l1">🚨 REASSESS NOW</span>' if b["breach"]
                  else f'<span class="chip chip-l4">✓ WITHIN TARGET</span>')
        why = ""
        if res.confidence_label == "Low" and not b["breach"]:
            why = '<div style="font-size:0.78rem;color:var(--l1);margin-top:2px;font-weight:600;">⚠️ Low-confidence triage — surfaced earlier in priority queue</div>'
        
        pcard_html = f"""
        <div class="pcard" style="--COL:{HEX[m['c']]}">
          <div class="pid">{rec['patient_id']}</div>
          <div class="who">
            <div class="nm">{rec['name']} <span style="font-weight:400;color:var(--muted);font-size:0.85rem;">· {int(float(rec['age']))}y</span></div>
            <div class="cc">{rec['complaint'].capitalize()}</div>
          </div>
          <div class="lvl">L{res.acuity} · {m['label']}</div>
          <div class="wait">Elapsed: <b>{b['waited']}</b> min · Limit: <b>{b['limit']}</b> min{why}</div>
          <div class="flagbadge">{status}</div>
        </div>
        """
        render_html(pcard_html)
