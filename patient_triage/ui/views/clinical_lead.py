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
          <div class="stat-card neutral"><div class="n">{n_total}</div><div class="l">Total Assessed</div></div>
          <div class="stat-card l1"><div class="n">{n_l1 + n_l2}</div><div class="l">High Acuity (L1–L2)</div></div>
          <div class="stat-card l3"><div class="n">{n_lowconf}</div><div class="l">Low-Confidence Flags</div></div>
          <div class="stat-card neutral"><div class="n">{n_alerts}</div><div class="l">Reassess Alerts</div></div>
          <div class="stat-card neutral"><div class="n">{n_overrides}</div><div class="l">Clinician Overrides</div></div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    c1, c2 = st.columns([1.3, 1], gap="large")
    with c1:
        st.markdown(section_label('📊 Acuity Distribution (ESI 1-5)'), unsafe_allow_html=True)
        accdf = pd.DataFrame([{"acuity": r.acuity} for _, r in scored])
        dist = accdf["acuity"].value_counts().reindex([1, 2, 3, 4, 5], fill_value=0).reset_index()
        dist.columns = ["Acuity", "Count"]
        colors = [HEX[ACUITY_META[a]["c"]] for a in dist["Acuity"]]
        
        fig = go.Figure(go.Bar(
            x=[f"Level {a}<br><b>{ACUITY_META[a]['label']}</b>" for a in dist["Acuity"]], 
            y=dist["Count"],
            marker=dict(
                color=colors,
                line=dict(width=1, color="rgba(0,0,0,0.1)"),
            ),
            text=dist["Count"], 
            textposition="outside",
            textfont=dict(family="JetBrains Mono", size=14, color="#0F172A"),
        ))
        fig.update_layout(
            height=290, 
            margin=dict(l=15, r=15, t=20, b=20),
            plot_bgcolor="white", 
            paper_bgcolor="white",
            font=dict(family="Inter", color="#0F172A", size=11),
            yaxis=dict(gridcolor="#E2E8F0", zeroline=False, title="Patients"),
            xaxis=dict(showgrid=False),
        )
        st.plotly_chart(fig, use_container_width=True, config={"displayModeBar": False})

    with c2:
        st.markdown(section_label('🛡️ Clinical Safety & Model Guardrails'), unsafe_allow_html=True)
        checks = [
            "Age-aware pediatric vital thresholds",
            "Red-flag upward-only overrides",
            "Uncertainty safety escalation",
            "Explainable complaint matching",
            "Mandated clinician override logging",
            "Tamper-evident audit hash chain",
            "Pseudonymized patient identifiers",
            "Personal baseline-aware scoring",
        ]
        html = "<div class='checklist'>" + "".join(
            f'<div class="checkitem"><span class="tick">✓</span>{c}</div>' for c in checks
        ) + "</div>"
        st.markdown(html, unsafe_allow_html=True)

    st.markdown(f"<div style='margin-top:14px;'>{section_label('🔐 Tamper-Evident Audit Log (HIPAA-Style Accountability)')}</div>", unsafe_allow_html=True)
    st.caption("Patient identifiers are cryptographically pseudonymized (HMAC-SHA256). "
               "Clinical Leads may authorize below to re-link tokens for formal quality or legal review. "
               "Every re-link request is itself audited.")
    
    col_auth1, col_auth2 = st.columns([2, 1])
    with col_auth1:
        pw = st.text_input("Enter Clinical Lead authorization password (demo: triage-lead-2026)", type="password", key="lead_pw")
    with col_auth2:
        st.write("")
        st.write("")
        authorized = privacy.check_role_access("Clinical Lead", pw)
        if pw and authorized:
            st.success("🔓 Identity re-linking authorized")
        elif pw and not authorized:
            st.error("❌ Invalid authorization key")

    log = log_all[-15:]
    if not log:
        st.info("No audit events recorded yet. Switch to Triage Nurse view to record scores or overrides.")
    else:
        df = pd.DataFrame(log)[["ts", "event_type", "patient_id", "actor"]]
        df.columns = ["Timestamp (UTC)", "Event Type", "Patient Identifier", "Authorized Actor"]
        if authorized:
            df["Patient Identifier"] = df["Patient Identifier"].apply(
                lambda t: audit.resolve_identity(t, "Clinical Lead", pw))
            st.markdown(alert_box("ok", "🔓 Authorized Access Active", "Pseudonymous tokens have been re-linked to real Patient MRNs for review."),
                        unsafe_allow_html=True)
        else:
            st.markdown(
                alert_box("info", "🔒 Protected Privacy Mode", "Displaying pseudonymized HMAC tokens. Sensitive MRNs are masked."),
                unsafe_allow_html=True,
            )
        st.dataframe(df, use_container_width=True, hide_index=True)
        st.caption(f"SHA-256 Hash Chain Integrity: **{'✓ INTACT' if audit.verify_chain() else '❌ COMPROMISED'}**")

    with st.expander("📑 Healthcare Privacy, Compliance & Data Minimization Policy"):
        st.markdown(
            "**Assumed Jurisdiction:** United States — HIPAA Privacy & Security Rules (Prototype Implementation).\n\n"
            "**Data Retention:** Raw vitals and clinical identifiers stored encrypted at rest for 7 years · "
            "Audit records retained indefinitely (pseudonymized, tamper-evident hash-chained) · "
            "De-identified aggregate metrics maintained for clinical safety monitoring.\n\n"
            "**Care Consent:** Emergency intake falls under implied consent for immediate resuscitation; "
            "continuous re-assessment forms part of the ongoing clinical care episode."
        )
        st.caption("Field-Level Minimization Table:")
        for field, (purpose, retention) in privacy.FIELD_MINIMIZATION.items():
            st.caption(f"• **`{field}`** — {purpose} *(Policy: {retention})*")
