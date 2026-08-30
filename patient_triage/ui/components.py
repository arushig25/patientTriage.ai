# patient_triage/ui/components.py

import streamlit as st

ACUITY_META = {
    1: {"label": "Resuscitation", "desc": "Immediate life-threatening emergency", "c": "l1"},
    2: {"label": "Emergent",      "desc": "Immediate physician assessment",       "c": "l2"},
    3: {"label": "Urgent",        "desc": "Timely assessment",                    "c": "l3"},
    4: {"label": "Less Urgent",   "desc": "Standard queue",                       "c": "l4"},
    5: {"label": "Non-Urgent",    "desc": "Fast-track / minor care",              "c": "l5"},
}

CONF_COLOR = {"High": "l4", "Moderate": "l3", "Low": "l1"}

HEX = {"l1": "#DC2626", "l2": "#EA580C", "l3": "#D97706", "l4": "#059669", "l5": "#2563EB"}
BG = {"l1": "#FEF2F2", "l2": "#FFF7ED", "l3": "#FFFBEB", "l4": "#ECFDF5", "l5": "#EFF6FF"}
BD = {"l1": "#FECACA", "l2": "#FED7AA", "l3": "#FDE68A", "l4": "#A7F3D0", "l5": "#BFDBFE"}

def render_html(html_str: str) -> None:
    """Render HTML safely into Streamlit without markdown interpreting indentation as code blocks."""
    cleaned = "\n".join(line.strip() for line in html_str.strip().splitlines())
    st.markdown(cleaned, unsafe_allow_html=True)

def chip(level):
    m = ACUITY_META[level]
    return f'<span class="chip chip-{m["c"]}">LEVEL {level} · {m["label"].upper()}</span>'

def section_label(text):
    return f'<div class="sec-label">{text}</div>'

def stat_card_html(value, label, color_class):
    return f'<div class="stat-card {color_class}"><div class="n">{value}</div><div class="l">{label}</div></div>'

def vital_cell(label, val, unit, warn=False, crit=False, flagtext=None):
    cls = "crit" if crit else ("warn" if warn else "")
    fv = "—" if val is None else (f"{val:g}" if isinstance(val, float) else val)
    flag_html = f'<div class="flag">{flagtext}</div>' if (warn or crit) and flagtext else ""
    return f'<div class="vitem {cls}"><div class="lab">{label}</div><div class="val">{fv} {unit if val is not None else ""}</div>{flag_html}</div>'

def alert_box(box_type, title, body):
    return f'<div class="abox abox-{box_type}"><b>{title}</b>\n{body}</div>'
