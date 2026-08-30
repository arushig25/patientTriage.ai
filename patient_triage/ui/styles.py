"""Hospital-grade CSS design system for PatientTriage.ai."""

HOSPITAL_CSS = """
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800&family=JetBrains+Mono:wght@400;500;600;700&display=swap');

:root {
  --bg: #F8FAFC;
  --surface: #FFFFFF;
  --surface-alt: #F1F5F9;
  --border: #E2E8F0;
  --border-strong: #CBD5E1;
  --text: #0F172A;
  --text-secondary: #334155;
  --muted: #64748B;
  --brand: #0D9488;
  --brand-dark: #0F766E;
  --brand-light: #CCFBF1;
  
  /* Clinical Acuity Scale (ESI-aligned) */
  --l1: #DC2626; --l1-bg: #FEF2F2; --l1-bd: #FECACA; --l1-dark: #991B1B;
  --l2: #EA580C; --l2-bg: #FFF7ED; --l2-bd: #FED7AA; --l2-dark: #9A3412;
  --l3: #D97706; --l3-bg: #FFFBEB; --l3-bd: #FDE68A; --l3-dark: #92400E;
  --l4: #059669; --l4-bg: #ECFDF5; --l4-bd: #A7F3D0; --l4-dark: #065F46;
  --l5: #2563EB; --l5-bg: #EFF6FF; --l5-bd: #BFDBFE; --l5-dark: #1E40AF;
}

html, body, [class*="css"] { 
    font-family: 'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; 
    color: var(--text);
    -webkit-font-smoothing: antialiased;
}

.stApp { 
    background: var(--bg); 
}

.mono { 
    font-family: 'JetBrains Mono', monospace; 
}

/* Hide deploy & footer chrome, keep sidebar toggle accessible */
#MainMenu, footer { 
    visibility: hidden; 
    height: 0; 
}
header[data-testid="stHeader"] {
    background: transparent !important;
}
div[data-testid="stToolbar"] {
    visibility: hidden !important;
}

.block-container { 
    padding-top: 1rem; 
    padding-bottom: 2.5rem;
    max-width: 1280px; 
}

/* ---- Hospital Header Bar ---- */
.pt-header {
  display: flex; 
  justify-content: space-between; 
  align-items: center;
  background: linear-gradient(135deg, #0F172A 0%, #1E293B 60%, #0F2D37 100%); 
  color: #FFFFFF; 
  border-radius: 16px;
  padding: 20px 28px; 
  margin-bottom: 24px;
  box-shadow: 0 4px 12px rgba(15, 23, 42, 0.15), 0 1px 3px rgba(15, 23, 42, 0.08);
  border: 1px solid rgba(255, 255, 255, 0.1);
}
.pt-header .brand { 
    font-weight: 800; 
    font-size: 1.4rem; 
    letter-spacing: -0.02em; 
    display: flex;
    align-items: center;
    gap: 8px;
}
.pt-header .dept { 
    font-size: 0.85rem; 
    color: #94A3B8; 
    font-weight: 500; 
    margin-top: 3px; 
    letter-spacing: 0.01em;
}
.pt-header-right { 
    display: flex; 
    align-items: center; 
    gap: 12px; 
}
.pt-status { 
    display: flex; 
    align-items: center; 
    gap: 8px; 
    font-size: 0.82rem; 
    font-weight: 600; 
    color: #A7F3D0; 
    background: rgba(16, 185, 129, 0.12);
    border: 1px solid rgba(16, 185, 129, 0.25);
    padding: 6px 14px;
    border-radius: 20px;
}

@keyframes pulse {
    0% { transform: scale(1); opacity: 1; }
    50% { transform: scale(1.35); opacity: 0.7; }
    100% { transform: scale(1); opacity: 1; }
}
.pt-status .dot { 
    width: 8px; 
    height: 8px; 
    border-radius: 50%; 
    background: #10B981; 
    animation: pulse 2s infinite; 
}
.pt-pill { 
    background: rgba(255, 255, 255, 0.1); 
    border: 1px solid rgba(255, 255, 255, 0.18); 
    padding: 6px 14px; 
    border-radius: 20px; 
    font-size: 0.82rem; 
    font-weight: 600; 
    color: #FFFFFF;
}
.pt-pill-surge { 
    background: rgba(220, 38, 38, 0.9); 
    border: 1px solid rgba(254, 202, 202, 0.4); 
    color: #FFFFFF;
    font-weight: 700;
}

/* ---- Stat Strip ---- */
.stat-row { 
    display: grid; 
    grid-template-columns: repeat(auto-fit, minmax(170px, 1fr)); 
    gap: 14px; 
    margin-bottom: 24px; 
}
.stat-card { 
    background: var(--surface); 
    border-radius: 14px; 
    padding: 16px 20px; 
    border: 1px solid var(--border);
    border-top: 4px solid var(--border-strong);
    box-shadow: 0 1px 3px rgba(0, 0, 0, 0.04);
    transition: transform 0.15s ease, box-shadow 0.15s ease;
}
.stat-card:hover {
    transform: translateY(-1px);
    box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.07);
}
.stat-card .n { 
    font-family: 'JetBrains Mono', monospace; 
    font-size: 2rem; 
    font-weight: 700; 
    line-height: 1.1; 
    color: var(--text);
}
.stat-card .l { 
    font-size: 0.76rem; 
    color: var(--muted); 
    font-weight: 600; 
    text-transform: uppercase; 
    letter-spacing: 0.05em; 
    margin-top: 6px; 
}
.stat-card.l1 { border-top-color: var(--l1); } .stat-card.l1 .n { color: var(--l1); } 
.stat-card.l2 { border-top-color: var(--l2); } .stat-card.l2 .n { color: var(--l2); }
.stat-card.l3 { border-top-color: var(--l3); } .stat-card.l3 .n { color: var(--l3); } 
.stat-card.neutral { border-top-color: var(--brand); } .stat-card.neutral .n { color: var(--text); }

/* ---- Section Label ---- */
.sec-label { 
    font-size: 0.8rem; 
    font-weight: 700; 
    text-transform: uppercase; 
    letter-spacing: 0.06em; 
    color: var(--muted); 
    margin: 4px 0 10px 0; 
    display: flex;
    align-items: center;
    gap: 6px;
}

/* ---- Acuity Banner (Triage Outcome) ---- */
.acuity-banner { 
    display: flex; 
    gap: 22px; 
    align-items: center; 
    border-radius: 16px; 
    padding: 22px 26px; 
    border: 1px solid var(--BD); 
    border-left: 8px solid var(--COL); 
    background: var(--BGC); 
    margin-bottom: 16px; 
    box-shadow: 0 2px 8px rgba(0, 0, 0, 0.04);
}
.acuity-banner .lvl { 
    font-family: 'JetBrains Mono', monospace; 
    font-weight: 800; 
    font-size: 3rem; 
    color: var(--COL); 
    line-height: 1; 
    min-width: 75px;
}
.acuity-banner .rt { 
    flex: 1; 
}
.acuity-banner .lbl { 
    font-weight: 800; 
    font-size: 1.1rem; 
    letter-spacing: 0.02em; 
    color: var(--COL); 
    text-transform: uppercase; 
}
.acuity-banner .act { 
    font-size: 1.05rem; 
    font-weight: 600; 
    color: var(--text); 
    margin-top: 5px; 
}

/* ---- Clinical Chips / Badges ---- */
.chip { 
    display: inline-block; 
    padding: 4px 12px; 
    border-radius: 20px; 
    font-size: 0.75rem; 
    font-weight: 700; 
    letter-spacing: 0.03em; 
}
.chip-l1 { background: var(--l1-bg); color: var(--l1); border: 1px solid var(--l1-bd); } 
.chip-l2 { background: var(--l2-bg); color: var(--l2); border: 1px solid var(--l2-bd); }
.chip-l3 { background: var(--l3-bg); color: var(--l3); border: 1px solid var(--l3-bd); } 
.chip-l4 { background: var(--l4-bg); color: var(--l4); border: 1px solid var(--l4-bd); }
.chip-l5 { background: var(--l5-bg); color: var(--l5); border: 1px solid var(--l5-bd); }

/* ---- Card Containers ---- */
.card { 
    background: var(--surface); 
    border: 1px solid var(--border);
    border-radius: 14px; 
    padding: 18px 22px; 
    margin-bottom: 16px; 
    box-shadow: 0 1px 3px rgba(0, 0, 0, 0.04);
}
.card-title { 
    font-weight: 700; 
    font-size: 0.98rem; 
    margin-bottom: 12px; 
    color: var(--text);
}

/* ---- Queue Patient Cards ---- */
.pcard { 
    display: flex; 
    align-items: center; 
    gap: 16px; 
    background: var(--surface); 
    border: 1px solid var(--border);
    border-radius: 12px; 
    padding: 14px 18px; 
    margin-bottom: 10px; 
    border-left: 6px solid var(--COL);
    box-shadow: 0 1px 2px rgba(0, 0, 0, 0.04);
    transition: transform 0.15s ease, box-shadow 0.15s ease;
}
.pcard:hover { 
    transform: translateY(-2px); 
    box-shadow: 0 4px 8px -1px rgba(0, 0, 0, 0.08); 
}
.pcard .pid { 
    font-family: 'JetBrains Mono', monospace; 
    font-size: 0.82rem; 
    color: var(--muted); 
    font-weight: 600; 
    min-width: 48px; 
}
.pcard .who { 
    min-width: 190px; 
}
.pcard .who .nm { 
    font-weight: 700; 
    font-size: 0.98rem; 
    color: var(--text);
}
.pcard .who .cc { 
    font-size: 0.84rem; 
    color: var(--muted); 
    margin-top: 2px; 
}
.pcard .lvl { 
    font-family: 'JetBrains Mono', monospace; 
    font-weight: 700; 
    color: var(--COL); 
    font-size: 0.88rem; 
    min-width: 110px; 
}
.pcard .wait { 
    font-size: 0.85rem; 
    color: var(--text); 
    min-width: 120px; 
}
.pcard .wait b { 
    font-family: 'JetBrains Mono', monospace; 
}
.pcard .flagbadge { 
    margin-left: auto; 
}

/* ---- Vitals Grid ---- */
.vgrid { 
    display: grid; 
    grid-template-columns: repeat(3, 1fr); 
    gap: 10px; 
}
.vitem { 
    background: var(--surface-alt); 
    border: 1px solid var(--border);
    border-radius: 10px; 
    padding: 10px 12px; 
}
.vitem .lab { 
    font-size: 0.72rem; 
    color: var(--muted); 
    font-weight: 600; 
    text-transform: uppercase; 
    letter-spacing: 0.04em; 
}
.vitem .val { 
    font-family: 'JetBrains Mono', monospace; 
    font-weight: 700; 
    font-size: 1.18rem; 
    margin-top: 3px; 
    color: var(--text);
}
.vitem.warn { border-color: var(--l2-bd); background: var(--l2-bg); }
.vitem.warn .val { color: var(--l2-dark); }
.vitem.crit { border-color: var(--l1-bd); background: var(--l1-bg); }
.vitem.crit .val { color: var(--l1-dark); }
.vitem .flag { 
    font-size: 0.72rem; 
    font-weight: 700; 
    margin-top: 3px; 
}
.vitem.warn .flag { color: var(--l2-dark); } 
.vitem.crit .flag { color: var(--l1-dark); }

/* ---- Reasons List ---- */
.reasons { 
    list-style: none; 
    margin: 0; 
    padding: 0; 
}
.reasons li { 
    padding: 8px 0 8px 18px; 
    border-bottom: 1px solid var(--border); 
    font-size: 0.92rem; 
    position: relative; 
    color: var(--text);
}
.reasons li:last-child { 
    border-bottom: none; 
}
.reasons li::before { 
    content: "•"; 
    position: absolute; 
    left: 2px; 
    color: var(--brand); 
    font-weight: 800; 
    font-size: 1.2em; 
}

/* ---- Confidence Track ---- */
.conf-track { 
    background: var(--surface-alt); 
    border: 1px solid var(--border);
    border-radius: 6px; 
    height: 10px; 
    width: 100%; 
    overflow: hidden; 
}
.conf-fill { 
    height: 100%; 
    border-radius: 6px; 
}

/* ---- Alert & Callout Boxes ---- */
.abox { 
    border-radius: 12px; 
    padding: 12px 16px; 
    font-size: 0.88rem; 
    margin-bottom: 12px; 
    border: 1px solid;
    border-left: 5px solid; 
}
.abox-crit { background: var(--l1-bg); border-color: var(--l1-bd); border-left-color: var(--l1); color: var(--l1-dark); }
.abox-warn { background: var(--l2-bg); border-color: var(--l2-bd); border-left-color: var(--l2); color: var(--l2-dark); }
.abox-info { background: var(--surface-alt); border-color: var(--border); border-left-color: var(--brand); color: var(--text); }
.abox-ok { background: var(--l4-bg); border-color: var(--l4-bd); border-left-color: var(--l4); color: var(--l4-dark); }
.abox b { display: block; margin-bottom: 3px; font-weight: 700; }

/* ---- Safety Checklist ---- */
.checklist { 
    display: grid; 
    grid-template-columns: repeat(2, 1fr); 
    gap: 10px; 
}
.checkitem { 
    display: flex; 
    gap: 10px; 
    align-items: center; 
    font-size: 0.9rem; 
    background: var(--surface-alt); 
    border: 1px solid var(--border);
    border-radius: 10px; 
    padding: 10px 12px; 
    color: var(--text);
}
.checkitem .tick { 
    color: var(--brand); 
    font-weight: 800; 
    font-size: 1.05rem;
}

/* ---- Streamlit Widget Touch-ups ---- */
div[data-testid="stButton"] button { 
    border-radius: 10px; 
    font-weight: 600; 
    border: 1px solid var(--border-strong);
    background: var(--surface);
    color: var(--text);
    transition: all 0.2s;
}
div[data-testid="stButton"] button:hover {
    border-color: var(--brand);
    color: var(--brand);
}
div[data-testid="stFormSubmitButton"] button { 
    border-radius: 10px; 
    font-weight: 700; 
    background: var(--brand); 
    color: #FFFFFF !important; 
    border: none; 
    padding: 10px 20px;
    box-shadow: 0 2px 4px rgba(13, 148, 136, 0.2);
    transition: all 0.2s; 
}
div[data-testid="stFormSubmitButton"] button:hover { 
    background: var(--brand-dark); 
    color: #FFFFFF !important; 
    box-shadow: 0 4px 6px rgba(13, 148, 136, 0.3);
}
section[data-testid="stSidebar"] { 
    background: #FFFFFF; 
    border-right: 1px solid var(--border); 
}
div[data-testid="stMetric"] { 
    background: var(--surface); 
    border: 1px solid var(--border); 
    border-radius: 12px; 
    padding: 12px 16px; 
}
hr { 
    border-color: var(--border); 
    margin: 1.2rem 0;
}
</style>
"""
