HOSPITAL_CSS = """
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&family=JetBrains+Mono:wght@500;600&display=swap');

:root {
  --bg: #F1F5F9;
  --surface: #FFFFFF;
  --surface-alt: #F8FAFC;
  --border: #E2E8F0;
  --text: #1E293B;
  --muted: #64748B;
  --brand: #0D9488;
  --brand-dark: #0F766E;
  
  --l1: #DC2626; --l1-bg: #FEF2F2; --l1-bd: #FECACA;
  --l2: #EA580C; --l2-bg: #FFF7ED; --l2-bd: #FED7AA;
  --l3: #D97706; --l3-bg: #FFFBEB; --l3-bd: #FDE68A;
  --l4: #059669; --l4-bg: #ECFDF5; --l4-bd: #A7F3D0;
  --l5: #2563EB; --l5-bg: #EFF6FF; --l5-bd: #BFDBFE;
}

html, body, [class*="css"] { 
    font-family: 'Inter', -apple-system, sans-serif; 
    color: var(--text); 
}
.stApp { background: var(--bg); }
.mono { font-family: 'JetBrains Mono', monospace; }
#MainMenu, footer, header[data-testid="stHeader"] { visibility: hidden; height: 0; }
.block-container { padding-top: 1.2rem; max-width: 1240px; }

/* ---- App header bar ---- */
.pt-header {
  display: flex; justify-content: space-between; align-items: center;
  background: linear-gradient(135deg, #0F172A 0%, #1E293B 100%); color: #fff; border-radius: 16px;
  padding: 20px 28px; margin-bottom: 24px;
  box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1), 0 2px 4px -1px rgba(0, 0, 0, 0.06);
}
.pt-header .brand { font-weight: 800; font-size: 1.35rem; letter-spacing: -0.01em; }
.pt-header .dept { font-size: 0.85rem; color: #94A3B8; font-weight: 500; margin-top: 2px; }
.pt-header-right { display: flex; align-items: center; gap: 12px; }
.pt-status { display: flex; align-items: center; gap: 8px; font-size: 0.8rem; font-weight: 600; color: #6EE7B7; }

@keyframes pulse {
    0% { transform: scale(1); opacity: 1; }
    50% { transform: scale(1.4); opacity: 0.7; }
    100% { transform: scale(1); opacity: 1; }
}
.pt-status .dot { width: 8px; height: 8px; border-radius: 50%; background: #10B981; animation: pulse 2s infinite; }
.pt-pill { background: rgba(255,255,255,0.1); border: 1px solid rgba(255,255,255,0.15); padding: 6px 14px; border-radius: 20px; font-size: 0.8rem; font-weight: 600; }
.pt-pill-surge { background: rgba(220, 38, 38, 0.85); border: 1px solid rgba(255,255,255,0.2); }

/* ---- Stat strip ---- */
.stat-row { display: flex; gap: 16px; margin-bottom: 24px; flex-wrap: wrap; }
.stat-card { 
    flex: 1; min-width: 140px; background: var(--surface); 
    border-radius: 16px; padding: 18px 20px; 
    box-shadow: 0 1px 3px rgba(0,0,0,0.08), 0 1px 2px rgba(0,0,0,0.06);
    border-top: 4px solid var(--border);
}
.stat-card .n { font-family: 'JetBrains Mono', monospace; font-size: 2rem; font-weight: 700; line-height: 1; }
.stat-card .l { font-size: 0.75rem; color: var(--muted); font-weight: 600; text-transform: uppercase; letter-spacing: 0.05em; margin-top: 6px; }
.stat-card.l1 { border-top-color: var(--l1); } .stat-card.l1 .n { color: var(--l1); } 
.stat-card.l2 { border-top-color: var(--l2); } .stat-card.l2 .n { color: var(--l2); }
.stat-card.l3 { border-top-color: var(--l3); } .stat-card.l3 .n { color: var(--l3); } 
.stat-card.neutral { border-top-color: var(--muted); } .stat-card.neutral .n { color: var(--text); }

/* ---- Section label ---- */
.sec-label { font-size: 0.8rem; font-weight: 700; text-transform: uppercase; letter-spacing: 0.06em; color: var(--muted); margin: 4px 0 12px 0; }

/* ---- Acuity banner (the triage result) ---- */
.acuity-banner { 
    display: flex; gap: 24px; align-items: center; border-radius: 16px; 
    padding: 24px 28px; border: 1px solid var(--BD); 
    border-left: 8px solid var(--COL); background: var(--BGC); margin-bottom: 16px; 
    box-shadow: 0 1px 3px rgba(0,0,0,0.08), 0 1px 2px rgba(0,0,0,0.06);
}
.acuity-banner .lvl { font-family: 'JetBrains Mono', monospace; font-weight: 700; font-size: 3rem; color: var(--COL); line-height: 1; }
.acuity-banner .rt { flex: 1; }
.acuity-banner .lbl { font-weight: 800; font-size: 1.1rem; letter-spacing: 0.02em; color: var(--COL); text-transform: uppercase; }
.acuity-banner .act { font-size: 1.05rem; font-weight: 500; color: var(--text); margin-top: 6px; }

/* ---- Chips ---- */
.chip { display: inline-block; padding: 4px 12px; border-radius: 20px; font-size: 0.75rem; font-weight: 700; letter-spacing: 0.02em; }
.chip-l1 { background: var(--l1-bg); color: var(--l1); } .chip-l2 { background: var(--l2-bg); color: var(--l2); }
.chip-l3 { background: var(--l3-bg); color: var(--l3); } .chip-l4 { background: var(--l4-bg); color: var(--l4); }
.chip-l5 { background: var(--l5-bg); color: var(--l5); }

/* ---- Cards ---- */
.card { 
    background: var(--surface); border-radius: 16px; padding: 20px 24px; margin-bottom: 16px; 
    box-shadow: 0 1px 3px rgba(0,0,0,0.08), 0 1px 2px rgba(0,0,0,0.06);
}
.card-title { font-weight: 700; font-size: 1rem; margin-bottom: 12px; }

/* ---- Patient / queue card ---- */
.pcard { 
    display: flex; align-items: center; gap: 16px; background: var(--surface); 
    border-radius: 16px; padding: 16px 20px; margin-bottom: 12px; 
    border-left: 5px solid var(--COL);
    box-shadow: 0 1px 3px rgba(0,0,0,0.08), 0 1px 2px rgba(0,0,0,0.06);
    transition: transform 0.2s, box-shadow 0.2s;
}
.pcard:hover { transform: translateY(-2px); box-shadow: 0 4px 6px -1px rgba(0,0,0,0.1), 0 2px 4px -1px rgba(0,0,0,0.06); }
.pcard .pid { font-family: 'JetBrains Mono', monospace; font-size: 0.8rem; color: var(--muted); font-weight: 600; min-width: 50px; }
.pcard .who { min-width: 200px; }
.pcard .who .nm { font-weight: 700; font-size: 1rem; }
.pcard .who .cc { font-size: 0.85rem; color: var(--muted); margin-top: 2px; }
.pcard .lvl { font-family: 'JetBrains Mono', monospace; font-weight: 700; color: var(--COL); font-size: 0.9rem; min-width: 110px; }
.pcard .wait { font-size: 0.85rem; color: var(--text); min-width: 120px; }
.pcard .wait b { font-family: 'JetBrains Mono', monospace; }
.pcard .flagbadge { margin-left: auto; }

/* ---- Vitals grid ---- */
.vgrid { display: grid; grid-template-columns: repeat(3, 1fr); gap: 12px; }
.vitem { background: var(--surface-alt); border-radius: 12px; padding: 12px 14px; }
.vitem .lab { font-size: 0.75rem; color: var(--muted); font-weight: 600; text-transform: uppercase; letter-spacing: 0.04em; }
.vitem .val { font-family: 'JetBrains Mono', monospace; font-weight: 700; font-size: 1.25rem; margin-top: 4px; }
.vitem.warn .val { color: var(--l2); } .vitem.crit .val { color: var(--l1); }
.vitem .flag { font-size: 0.75rem; font-weight: 700; margin-top: 4px; }
.vitem.warn .flag { color: var(--l2); } .vitem.crit .flag { color: var(--l1); }

/* ---- Reasons list ---- */
.reasons { list-style: none; margin: 0; padding: 0; }
.reasons li { padding: 8px 0 8px 20px; border-bottom: 1px solid var(--border); font-size: 0.95rem; position: relative; }
.reasons li:last-child { border-bottom: none; }
.reasons li::before { content: "•"; position: absolute; left: 4px; color: var(--brand); font-weight: 700; font-size: 1.2em; }

/* ---- Confidence bar ---- */
.conf-track { background: var(--surface-alt); border-radius: 6px; height: 10px; width: 100%; overflow: hidden; }
.conf-fill { height: 100%; border-radius: 6px; }

/* ---- Alert / banner boxes ---- */
.abox { border-radius: 12px; padding: 14px 18px; font-size: 0.9rem; margin-bottom: 12px; border-left: 4px solid; }
.abox-crit { background: var(--l1-bg); border-color: var(--l1); color: #7F1D1D; }
.abox-warn { background: var(--l2-bg); border-color: var(--l2); color: #7C2D12; }
.abox-info { background: var(--surface-alt); border-color: var(--muted); color: var(--text); }
.abox-ok { background: var(--l4-bg); border-color: var(--l4); color: #064E3B; }
.abox b { display: block; margin-bottom: 4px; }

/* ---- Checklist ---- */
.checklist { display: grid; grid-template-columns: repeat(2, 1fr); gap: 12px; }
.checkitem { display: flex; gap: 10px; align-items: flex-start; font-size: 0.95rem; background: var(--surface-alt); border-radius: 12px; padding: 12px 14px; }
.checkitem .tick { color: var(--brand); font-weight: 800; }

/* ---- Streamlit widget touch-ups ---- */
div[data-testid="stButton"] button { border-radius: 10px; font-weight: 600; }
div[data-testid="stFormSubmitButton"] button { border-radius: 10px; font-weight: 700; background: var(--brand); color: #fff; border: none; transition: background 0.2s; }
div[data-testid="stFormSubmitButton"] button:hover { background: var(--brand-dark); color: #fff; }
section[data-testid="stSidebar"] { background: var(--surface); border-right: 1px solid var(--border); }
div[data-testid="stMetric"] { background: var(--surface); border: 1px solid var(--border); border-radius: 12px; padding: 12px 16px; }
hr { border-color: var(--border); }
</style>
"""
