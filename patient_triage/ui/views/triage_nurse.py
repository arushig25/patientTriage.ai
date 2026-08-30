import pandas as pd
import streamlit as st
from patient_triage.core.engine import (
    Vitals, age_band, score_patient, PEDS_NORMAL, _match_high_risk_complaint
)
from patient_triage.data.simulator import get_history
from patient_triage.security import audit, privacy
from patient_triage.ui.components import (
    ACUITY_META, CONF_COLOR, HEX, BG, BD, chip, section_label, vital_cell, alert_box, render_html
)

def _clean(v):
    return None if (v is None or (isinstance(v, float) and pd.isna(v)) or v == "") else v

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

def render(scored, surge_factor, surge_active, role_display):
    role = "Triage Nurse"
    n_total = len(scored)
    n_l1 = sum(1 for _, r in scored if r.acuity == 1)
    n_l2 = sum(1 for _, r in scored if r.acuity == 2)
    n_l3 = sum(1 for _, r in scored if r.acuity == 3)

    # Top Clinical Stats Row
    render_html(
        f"""
        <div class="stat-row">
          <div class="stat-card neutral"><div class="n">{n_total}</div><div class="l">Active Patients</div></div>
          <div class="stat-card l1"><div class="n">{n_l1}</div><div class="l">Immediate (Level 1)</div></div>
          <div class="stat-card l2"><div class="n">{n_l2}</div><div class="l">Emergent (Level 2)</div></div>
          <div class="stat-card l3"><div class="n">{n_l3}</div><div class="l">Urgent (Level 3)</div></div>
        </div>
        """
    )

    tab_active, tab_calc = st.tabs(["📋 Arriving Patient Intake", "⚡ Quick Triage Calculator"])

    with tab_active:
        names = [f'{r["patient_id"]} — {r["name"]} ({int(float(r["age"]))}y) · {r["complaint"].capitalize()}' for r, _ in scored]
        idx = st.selectbox(
            "Select arriving / in-progress patient",
            range(len(names)),
            format_func=lambda i: names[i],
            help="Choose a patient from the current arrival queue to view AI triage assessment"
        )
        rec, res = scored[idx]
        v = to_vitals(rec)
        age = float(rec["age"])
        band = age_band(age)
        m = ACUITY_META[res.acuity]

        left, right = st.columns([1, 1.15], gap="large")

        with left:
            st.markdown(section_label('👤 Patient Demographics & Intake'), unsafe_allow_html=True)
            render_html(
                f"""
                <div class="card">
                  <div style="display:flex;justify-content:space-between;align-items:baseline;">
                    <div>
                      <div style="font-weight:800;font-size:1.2rem;color:var(--text);">{rec['name']}</div>
                      <div style="color:var(--muted);font-size:0.88rem;margin-top:2px;">
                        Age: <b>{int(age)}</b> years &middot; MRN: <span class="mono">{rec['patient_id']}</span> &middot; Band: <b>{band.replace('_', ' ').title()}</b>
                      </div>
                    </div>
                  </div>
                  <div style="margin-top:14px;padding-top:12px;border-top:1px solid var(--border);font-size:0.92rem;">
                    <span style="color:var(--muted);font-size:0.75rem;font-weight:700;text-transform:uppercase;letter-spacing:0.04em;">Chief Complaint</span>
                    <div style="font-weight:600;color:var(--text);font-size:1.05rem;margin-top:2px;">{rec['complaint'].capitalize()}</div>
                  </div>
                </div>
                """
            )

            cat, phrase = _match_high_risk_complaint(rec["complaint"])
            if cat:
                render_html(
                    alert_box("warn", f"⚠️ Recognized High-Risk Category: {cat.replace('_',' ').title()}", 
                              f'Matched pattern: "<b>{phrase}</b>" — safety override elevates minimum priority to Emergent (Level 2).')
                )

            if band in PEDS_NORMAL:
                render_html(
                    alert_box("info", "🧒 Pediatric Assessment Mode", 
                              f"Patient is {int(age)} years old ({band.replace('_', ' ')}). Vitals evaluated against Fleming/Lancet pediatric vital percentiles.")
                )

            st.markdown(f"<div style='margin-top:8px;'>{section_label('🩺 Measured Vital Signs')}</div>", unsafe_allow_html=True)

            hr_warn = (v.hr is not None and v.hr >= 100)
            hr_crit = (v.hr is not None and (v.hr >= 140 or v.hr < 45))
            rr_warn = (v.rr is not None and v.rr >= 22)
            rr_crit = (v.rr is not None and v.rr >= 30)
            spo2_warn = (v.spo2 is not None and v.spo2 < 94)
            spo2_crit = (v.spo2 is not None and v.spo2 < 90)
            sbp_warn = (v.sbp is not None and v.sbp < 100)
            sbp_crit = (v.sbp is not None and v.sbp < 90)

            vitals_card_html = f"""
            <div class="card" style="padding:16px;">
              <div class="vgrid">
                {vital_cell("Heart Rate", v.hr, "bpm", hr_warn, hr_crit, "🚨 Critical" if hr_crit else ("⚠️ High" if hr_warn else None))}
                {vital_cell("Resp. Rate", v.rr, "/min", rr_warn, rr_crit, "🚨 Critical" if rr_crit else ("⚠️ High" if rr_warn else None))}
                {vital_cell("SpO₂", v.spo2, "%", spo2_warn, spo2_crit, "🚨 Critical" if spo2_crit else ("⚠️ Low" if spo2_warn else None))}
                {vital_cell("Systolic BP", v.sbp, "mmHg", sbp_warn, sbp_crit, "🚨 Critical" if sbp_crit else ("⚠️ Low" if sbp_warn else None))}
                {vital_cell("Temperature", v.temp, "°C")}
                {vital_cell("Consciousness", v.avpu, "(AVPU)")}
              </div>
            </div>
            """
            render_html(vitals_card_html)

            st.markdown(f"<div style='margin-top:12px;'>{section_label('📜 Historical EHR Baseline')}</div>", unsafe_allow_html=True)
            has_hist = str(rec["has_history"]).lower() not in ("false", "0", "")
            history = get_history(rec["patient_id"])
            if not has_hist:
                render_html(
                    alert_box("info", "First-Time Patient (Zero Prior History)", 
                              "No prior institutional encounters on file. Assessed strictly against standard population reference ranges.")
                )
            elif history:
                conds = ", ".join(history["chronic_conditions"]) or "None documented"
                render_html(
                    alert_box("ok", "📋 Documented Baseline on File", 
                              f"Baseline HR: <b>{history['baseline_hr']} bpm</b> · Baseline SBP: <b>{history['baseline_sbp']} mmHg</b><br>"
                              f"Chronic Conditions: <b>{conds}</b><br>Last Encounter: <b>{history['last_visit_date']}</b> (Assigned Level {history['last_visit_acuity']}).")
                )
            else:
                render_html(
                    alert_box("warn", "Returning Patient — Incomplete Baseline", 
                              "Prior record exists in database, but no verified clinical baseline vitals were captured.")
                )

            with st.expander("🔒 Data Protection & Field Minimization (HIPAA)"):
                for field in ("patient_id", "name", "age", "vitals", "complaint", "history"):
                    purpose, retention = privacy.FIELD_MINIMIZATION[field]
                    st.caption(f"**{field}** — {purpose} *(Retention: {retention})*")

        with right:
            st.markdown(section_label('⚡ AI Triage Recommendation'), unsafe_allow_html=True)
            render_html(
                f"""
                <div class="acuity-banner" style="--COL:{HEX[m['c']]};--BGC:{BG[m['c']]};--BD:{BD[m['c']]}">
                  <div class="lvl">L{res.acuity}</div>
                  <div class="rt">
                    <div class="lbl">{m['label']} — Level {res.acuity}</div>
                    <div class="act">{res.recommended_action}</div>
                  </div>
                </div>
                """
            )

            if res.red_flags:
                flags_html = "".join(f"<li>{f}</li>" for f in res.red_flags)
                render_html(
                    f"""
                    <div class="abox abox-crit">
                      <b>🚨 Red-Flag Safety Trigger — {len(res.red_flags)} Mandated Escalation(s)</b>
                      <ul class="reasons" style="margin-top:6px;">{flags_html}</ul>
                      <div style="font-size:0.8rem;margin-top:6px;opacity:0.9;">Mandated safety thresholds elevate priority and cannot be relaxed by personal history.</div>
                    </div>
                    """
                )

            # Confidence Card — single unified container
            cc = CONF_COLOR[res.confidence_label]
            low_alert = ""
            if res.confidence_label == "Low":
                low_alert = f"<div style='margin-top:12px;'>{alert_box('warn', '⚠️ Uncertainty Safety Escalation', 'Priority was raised by +1 tier because critical vitals are missing. Re-take complete vital signs to confirm.')}</div>"

            confidence_card_html = f"""
            <div class="card">
              <div style="display:flex;justify-content:space-between;align-items:baseline;">
                <div class="card-title" style="margin-bottom:0;">Assessment Confidence</div>
                <div style="font-family:'JetBrains Mono',monospace;font-weight:700;color:{HEX[cc]};font-size:1.1rem;">
                  {int(res.confidence*100)}% &middot; {res.confidence_label.upper()}
                </div>
              </div>
              <div class="conf-track" style="margin-top:10px;">
                <div class="conf-fill" style="width:{int(res.confidence*100)}%;background:{HEX[cc]};"></div>
              </div>
              {low_alert}
            </div>
            """
            render_html(confidence_card_html)

            # Rationale Card — single unified container
            reasons_html = "".join(f"<li>{r}</li>" for r in res.reasons)
            rationale_card_html = f"""
            <div class="card">
              <div class="card-title">🔍 Clinical Decision Rationale</div>
              <ul class="reasons">{reasons_html}</ul>
            </div>
            """
            render_html(rationale_card_html)

        if audit.should_log_score(st.session_state, rec["patient_id"], res.acuity):
            audit.log_event("SCORE", rec["patient_id"],
                                 {"acuity": res.acuity, "ews": res.ews_score,
                                  "confidence": res.confidence_label})
        if audit.should_log_access(st.session_state, rec["patient_id"]):
            audit.log_event("ACCESS", rec["patient_id"],
                                 {"fields": ["name", "vitals", "complaint"], "viewer_role": role})

        st.markdown(f"<div style='margin-top:10px;'>{section_label('✍️ Clinician Confirmation & Override')}</div>", unsafe_allow_html=True)
        with st.form("override"):
            c1, c2, c3 = st.columns([1, 2, 1])
            new_acuity = c1.selectbox("Override Acuity to", [1, 2, 3, 4, 5], index=res.acuity - 1,
                                      help="Select new ESI level if overriding AI suggestion")
            reason = c2.text_input("Clinical Justification for Override", 
                                   placeholder="e.g., Pale, diaphoretic, clinical suspicion of ACS")
            clinician = c3.text_input("Clinician ID", value="RN-1042")
            submitted = st.form_submit_button("Confirm & Commit Decision", use_container_width=True)
        if submitted:
            if new_acuity == res.acuity:
                st.info("Recommendation confirmed as suggested — no override necessary.")
            elif not reason.strip():
                st.error("A clinical justification is required to record an override.")
            else:
                audit.log_event("OVERRIDE", rec["patient_id"],
                                     {"from_acuity": res.acuity, "to_acuity": new_acuity, "reason": reason},
                                     actor=clinician)
                st.success(f"✓ Override logged: Level {res.acuity} → Level {new_acuity} by {clinician}. "
                           f"Tamper-evident audit chain verified intact: {audit.verify_chain()}")

    with tab_calc:
        st.markdown("### ⚡ Live Patient Triage Simulator")
        st.caption("Input custom patient vitals and symptoms to compute an instant ESI recommendation.")
        
        c_col1, c_col2, c_col3 = st.columns(3)
        with c_col1:
            c_age = st.number_input("Age (years)", min_value=0.1, max_value=110.0, value=45.0, step=1.0)
            c_complaint = st.text_input("Chief Complaint", value="Sudden chest tightness")
            c_avpu = st.selectbox("AVPU Mental Status", ["A", "V", "P", "U"], index=0)
        with c_col2:
            c_hr = st.number_input("Heart Rate (bpm)", min_value=20, max_value=250, value=98)
            c_rr = st.number_input("Respiratory Rate (/min)", min_value=4, max_value=80, value=20)
            c_spo2 = st.number_input("SpO₂ (%)", min_value=50, max_value=100, value=96)
        with c_col3:
            c_sbp = st.number_input("Systolic Blood Pressure (mmHg)", min_value=40, max_value=260, value=125)
            c_temp = st.number_input("Temperature (°C)", min_value=30.0, max_value=44.0, value=37.0, step=0.1)
            c_o2 = st.checkbox("Supplemental Oxygen", value=False)
            
        custom_vitals = Vitals(hr=float(c_hr), rr=float(c_rr), spo2=float(c_spo2),
                               sbp=float(c_sbp), temp=float(c_temp), avpu=c_avpu, on_oxygen=c_o2)
        
        custom_res = score_patient(float(c_age), custom_vitals, c_complaint)
        c_meta = ACUITY_META[custom_res.acuity]
        
        st.divider()
        render_html(
            f"""
            <div class="acuity-banner" style="--COL:{HEX[c_meta['c']]};--BGC:{BG[c_meta['c']]};--BD:{BD[c_meta['c']]}">
              <div class="lvl">L{custom_res.acuity}</div>
              <div class="rt">
                <div class="lbl">{c_meta['label']} — Level {custom_res.acuity}</div>
                <div class="act">{custom_res.recommended_action}</div>
              </div>
            </div>
            """
        )
        if custom_res.red_flags:
            flags_text = "".join(f"<li>{f}</li>" for f in custom_res.red_flags)
            render_html(f'<div class="abox abox-crit"><b>🚨 Red Flags:</b><ul class="reasons">{flags_text}</ul></div>')
        st.markdown(f"**Reasons:** " + " · ".join(custom_res.reasons))
