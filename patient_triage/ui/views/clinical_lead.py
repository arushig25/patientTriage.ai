import pandas as pd
import plotly.graph_objects as go
import streamlit as st
from patient_triage.security import audit, privacy
from patient_triage.ui.components import (ACUITY_META, HEX, section_label, alert_box)

def render(scored, surge_factor, surge_active, role_display):
    log_all = audit.read_log()
    n_overrides = sum(1 for e in log_all if e.get("event_type") == "OVERRIDE")
    n_alerts = sum(1 for e in log_all if e.get("event_type") == "ALERT")
    n_lowconf = sum(1 for _, r in scored if r.confidence_label == "Low")
    
    n_total = len(scored)
    n_l1 = sum(1 for _, r in scored if r.acuity == 1)
    n_l2 = sum(1 for _, r in scored if r.acuity == 2)

    st.markdown(
        f"""
        <div class="stat-row">
          <div class="stat-card neutral"><div class="n">{n_total}</div><div class="l">Patients assessed</div></div>
          <div class="stat-card l1"><div class="n">{n_l1 + n_l2}</div><div class="l">Level 1&ndash;2</div></div>
          <div class="stat-card l3"><div class="n">{n_lowconf}</div><div class="l">Low-confidence</div></div>
          <div class="stat-card neutral"><div class="n">{n_alerts}</div><div class="l">Reassess alerts</div></div>
          <div class="stat-card neutral"><div class="n">{n_overrides}</div><div class="l">Overrides</div></div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    c1, c2 = st.columns([1.3, 1], gap="large")
    with c1:
        st.markdown(section_label('Acuity distribution'), unsafe_allow_html=True)
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
            font=dict(family="Inter", color="#1E293B"),
            yaxis=dict(gridcolor="#E2E8F0", zeroline=False),
            xaxis=dict(showgrid=False),
        )
        st.plotly_chart(fig, use_container_width=True, config={"displayModeBar": False})

    with c2:
        st.markdown(section_label('Safety & trust'), unsafe_allow_html=True)
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

    st.markdown(f"<div style='margin-top:8px;'>{section_label('Audit log')}</div>", unsafe_allow_html=True)
    st.caption("Patient identifiers in the log are pseudonymized tokens. "
               "Authorize below to re-link tokens to real patient IDs for review &mdash; "
               "identity access is itself audited.")
    pw = st.text_input("Clinical Lead authorization password", type="password", key="lead_pw")
    authorized = privacy.check_role_access("Clinical Lead", pw)
    log = log_all[-15:]
    if not log:
        st.info("No events yet &mdash; use the Triage Nurse view to generate some.")
    else:
        df = pd.DataFrame(log)[["ts", "event_type", "patient_id", "actor"]]
        df.columns = ["Time", "Event", "Patient", "Actor"]
        if authorized:
            df["Patient"] = df["Patient"].apply(
                lambda t: audit.resolve_identity(t, "Clinical Lead", pw))
            st.markdown(alert_box("ok", "🔓 Authorized", "Identifiers re-linked below."),
                        unsafe_allow_html=True)
        else:
            st.markdown(
                alert_box("info", "🔒 Not authorized", "Showing pseudonymous tokens only."),
                unsafe_allow_html=True,
            )
        st.dataframe(df, use_container_width=True, hide_index=True)
        st.caption(f"Hash chain intact: {audit.verify_chain()}")

    with st.expander("🔒 Privacy & compliance"):
        st.markdown(
            "**Jurisdiction:** United States &mdash; HIPAA (prototype assumption, not a "
            "production HIPAA certification).\n\n"
            "**Retention:** raw vitals & identifiers 7 years &middot; audit records retained "
            "indefinitely (pseudonymized, hash-chained) &middot; de-identified aggregate scores "
            "retained for model monitoring.\n\n"
            "**Consent:** triage-time data collection falls under implied consent for "
            "emergency care; ongoing reassessment is part of the same care episode."
        )
        st.caption("Field-level data minimization:")
        for field, (purpose, retention) in privacy.FIELD_MINIMIZATION.items():
            st.caption(f"**{field}** &mdash; {purpose}. Retention: {retention}.")
