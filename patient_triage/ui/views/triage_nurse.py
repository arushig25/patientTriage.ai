import pandas as pd
import streamlit as st
from patient_triage.core.engine import (
    Vitals, age_band, PEDS_NORMAL, _match_high_risk_complaint
)
from patient_triage.data.simulator import get_history
from patient_triage.security import audit, privacy
from patient_triage.ui.components import (
    ACUITY_META, CONF_COLOR, HEX, BG, BD, chip, section_label, vital_cell, alert_box
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

    names = [f'{r["patient_id"]} &mdash; {r["name"]} ({int(float(r["age"]))}y)' for r, _ in scored]
    idx = st.selectbox("Select arriving / in-progress patient", range(len(names)),
                        format_func=lambda i: names[i])
    rec, res = scored[idx]
    v = to_vitals(rec)
    age = float(rec["age"])
    band = age_band(age)
    m = ACUITY_META[res.acuity]

    left, right = st.columns([1, 1.15], gap="large")

    with left:
        st.markdown(section_label('Patient'), unsafe_allow_html=True)
        st.markdown(
            f"""<div class="card">
                  <div style="display:flex;justify-content:space-between;align-items:baseline;">
                    <div>
                      <div style="font-weight:800;font-size:1.15rem;">{rec['name']}</div>
                      <div style="color:var(--muted);font-size:.85rem;">{int(age)} years &middot;
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
                alert_box("warn", f"✓ Recognized as {cat.replace('_',' ').title()}", 
                          f'Matched on "{phrase}" &mdash; this may raise the minimum triage priority.'),
                unsafe_allow_html=True,
            )

        if band in PEDS_NORMAL:
            st.markdown(
                alert_box("info", "🧒 Pediatric assessment", 
                          f"Age {int(age)} &mdash; vitals are interpreted using age-specific pediatric reference ranges, not adult thresholds."),
                unsafe_allow_html=True,
            )

        st.markdown(f"<div style='margin-top:6px;'>{section_label('Vital signs')}</div>", unsafe_allow_html=True)

        hr_warn, hr_crit = (v.hr is not None and v.hr >= 100), (v.hr is not None and (v.hr >= 140 or v.hr < 45))
        rr_warn, rr_crit = (v.rr is not None and v.rr >= 22), (v.rr is not None and v.rr >= 30)
        spo2_warn, spo2_crit = (v.spo2 is not None and v.spo2 < 94), (v.spo2 is not None and v.spo2 < 90)
        sbp_warn, sbp_crit = (v.sbp is not None and v.sbp < 100), (v.sbp is not None and v.sbp < 90)

        vhtml = "<div class='vgrid'>"
        vhtml += vital_cell("Heart rate", v.hr, "bpm", hr_warn, hr_crit, "🚨 Critical" if hr_crit else ("⚠ High" if hr_warn else None))
        vhtml += vital_cell("Resp. rate", v.rr, "/min", rr_warn, rr_crit, "🚨 Critical" if rr_crit else ("⚠ High" if rr_warn else None))
        vhtml += vital_cell("SpO₂", v.spo2, "%", spo2_warn, spo2_crit, "🚨 Critical" if spo2_crit else ("⚠ Low" if spo2_warn else None))
        vhtml += vital_cell("Systolic BP", v.sbp, "mmHg", sbp_warn, sbp_crit, "🚨 Critical" if sbp_crit else ("⚠ Low" if sbp_warn else None))
        vhtml += vital_cell("Temperature", v.temp, "°C")
        vhtml += vital_cell("Consciousness", v.avpu, "")
        vhtml += "</div>"
        st.markdown(vhtml, unsafe_allow_html=True)

        st.markdown(f"<div style='margin-top:14px;'>{section_label('Patient history')}</div>", unsafe_allow_html=True)
        has_hist = str(rec["has_history"]).lower() not in ("false", "0", "")
        history = get_history(rec["patient_id"])
        if not has_hist:
            st.markdown(
                alert_box("info", "No documented history", 
                          "First-time patient &mdash; assessed using current observed clinical information only."),
                unsafe_allow_html=True,
            )
        elif history:
            conds = ", ".join(history["chronic_conditions"]) or "None on file"
            st.markdown(
                alert_box("ok", "📋 Documented baseline on file", 
                          f"Baseline HR {history['baseline_hr']} bpm &middot; Baseline SBP {history['baseline_sbp']} mmHg &middot; "
                          f"Chronic conditions: {conds} &middot; Last visit {history['last_visit_date']} "
                          f"(Level {history['last_visit_acuity']})."),
                unsafe_allow_html=True,
            )
        else:
            st.markdown(
                alert_box("warn", "Returning patient &mdash; no usable baseline", 
                          "A previous record exists, but no documented clinical baseline is available for comparison. Scored the same as a first-time patient."),
                unsafe_allow_html=True,
            )

        with st.expander("🔒 Data protection &mdash; what's stored for this patient"):
            for field in ("patient_id", "name", "age", "vitals", "complaint", "history"):
                purpose, retention = privacy.FIELD_MINIMIZATION[field]
                st.caption(f"**{field}** &mdash; {purpose}. Retention: {retention}.")

    with right:
        st.markdown(section_label('Triage recommendation'), unsafe_allow_html=True)
        st.markdown(
            f"""<div class="acuity-banner" style="--COL:{HEX[m['c']]};--BGC:{BG[m['c']]};--BD:{BD[m['c']]}">
                  <div class="lvl">L{res.acuity}</div>
                  <div class="rt">
                    <div class="lbl">{m['label']} &mdash; {m['desc']}</div>
                    <div class="act">{res.recommended_action}</div>
                  </div>
                </div>""",
            unsafe_allow_html=True,
        )

        if res.red_flags:
            flags_html = "".join(f"<li>{f}</li>" for f in res.red_flags)
            st.markdown(
                f"""<div class="abox abox-crit">
                    <b>🚨 Safety alert &mdash; {len(res.red_flags)} red flag(s) detected</b>
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
                  <div style="font-family:'JetBrains Mono',monospace;font-weight:700;color:{HEX[cc]};">
                    {int(res.confidence*100)}% &middot; {res.confidence_label.upper()}
                  </div>
                </div>
                <div class="conf-track" style="margin-top:8px;">
                  <div class="conf-fill" style="width:{int(res.confidence*100)}%;background:{HEX[cc]};"></div>
                </div>""",
            unsafe_allow_html=True,
        )
        if res.confidence_label == "Low":
            st.markdown(
                f"<div style='margin-top:10px;'>{alert_box('warn', '⚠ Safety escalation applied', 'Priority was raised because important clinical information is missing or incomplete. Consider retaking a complete set of vitals.')}</div>",
                unsafe_allow_html=True,
            )
        st.markdown("</div>", unsafe_allow_html=True)

        st.markdown("<div class='card'><div class='card-title'>Why this recommendation</div>", unsafe_allow_html=True)
        st.markdown("<ul class='reasons'>" + "".join(f"<li>{r}</li>" for r in res.reasons) + "</ul></div>",
                    unsafe_allow_html=True)

    if audit.should_log_score(st.session_state, rec["patient_id"], res.acuity):
        audit.log_event("SCORE", rec["patient_id"],
                             {"acuity": res.acuity, "ews": res.ews_score,
                              "confidence": res.confidence_label})
    if audit.should_log_access(st.session_state, rec["patient_id"]):
        audit.log_event("ACCESS", rec["patient_id"],
                             {"fields": ["name", "vitals", "complaint"], "viewer_role": role})

    st.markdown(f"<div style='margin-top:6px;'>{section_label('Clinician decision')}</div>", unsafe_allow_html=True)
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
            audit.log_event("OVERRIDE", rec["patient_id"],
                                 {"from_acuity": res.acuity, "to_acuity": new_acuity, "reason": reason},
                                 actor=clinician)
            st.success(f"✓ Override recorded &mdash; Level {res.acuity} &rarr; Level {new_acuity} by {clinician}. "
                       f"Added to the audit trail. Chain intact: {audit.verify_chain()}")
