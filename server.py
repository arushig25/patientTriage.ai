"""
server.py -- High-performance FastAPI backend for PatientTriage.ai
Serves the REST API and the modern React Emergency Command Center frontend.
"""

import os
import sys
from pathlib import Path
from typing import Optional, List, Dict, Any
import numpy as np
from pydantic import BaseModel
from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse

from patient_triage.core.engine import (
    Vitals, score_patient, age_band, compute_surge_factor,
    safe_wait_minutes, wait_breach, effective_urgency,
    NORMAL_CAPACITY, SURGE_BANNER_THRESHOLD, PEDS_NORMAL,
    _match_high_risk_complaint
)
from patient_triage.data.simulator import (
    write_csv, surge_patients, base_patients, COLS, get_history
)
from patient_triage.security import audit, privacy

# Ensure database exists
if not os.path.exists("data/patients.csv"):
    write_csv()

app = FastAPI(
    title="PatientTriage.ai API",
    description="Emergency Department Triage & Flow Decision Support System",
    version="2.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ----------------- Request / Response Models -----------------

class VitalsInput(BaseModel):
    hr: Optional[float] = None
    rr: Optional[float] = None
    spo2: Optional[float] = None
    sbp: Optional[float] = None
    temp: Optional[float] = None
    avpu: Optional[str] = "A"
    on_oxygen: Optional[bool] = False

class ScorePatientRequest(BaseModel):
    age: float
    complaint: str
    vitals: VitalsInput
    patient_id: Optional[str] = None

class OverrideRequest(BaseModel):
    patient_id: str
    from_acuity: int
    to_acuity: int
    reason: str
    clinician: str = "RN-1042"

class AuthRequest(BaseModel):
    role: str = "Clinical Lead"
    password: str

# ----------------- Helper Functions -----------------

def _clean(v):
    return None if (v is None or (isinstance(v, float) and np.isnan(v)) or v == "") else v

def rec_to_vitals(rec: Dict[str, Any]) -> Vitals:
    def num(x):
        x = _clean(x)
        return float(x) if x is not None else None
    on_o2 = _clean(rec.get("on_oxygen"))
    if isinstance(on_o2, str):
        on_o2 = on_o2.lower() in ("true", "1", "yes")
    return Vitals(
        hr=num(rec.get("hr")),
        rr=num(rec.get("rr")),
        spo2=num(rec.get("spo2")),
        sbp=num(rec.get("sbp")),
        temp=num(rec.get("temp")),
        avpu=_clean(rec.get("avpu")) or "A",
        on_oxygen=bool(on_o2)
    )

# ----------------- REST Endpoints -----------------

@app.get("/api/health")
def health_check():
    return {
        "status": "healthy",
        "service": "PatientTriage.ai Clinical Engine",
        "hash_chain_intact": audit.verify_chain()
    }

@app.get("/api/patients")
def get_patients(surge: bool = Query(False)):
    """Fetch current arriving patients with full triage scoring, wait times, and queue ranking."""
    rows = surge_patients(3) if surge else base_patients()
    records = [dict(zip(COLS, r)) for r in rows]
    surge_factor = compute_surge_factor(len(records), NORMAL_CAPACITY)
    surge_active = surge_factor > SURGE_BANNER_THRESHOLD

    rng = np.random.default_rng(7)
    scored_patients = []

    for rec in records:
        history = get_history(rec["patient_id"])
        vitals_obj = rec_to_vitals(rec)
        age = float(rec["age"])
        res = score_patient(age, vitals_obj, rec["complaint"], history=history)

        waited = int(rng.integers(0, 90))
        limit = safe_wait_minutes(res.acuity, surge_factor)
        breached = wait_breach(res.acuity, waited, surge_factor)
        urgency = effective_urgency(res.acuity, waited, res.confidence_label)
        cat, phrase = _match_high_risk_complaint(rec["complaint"])

        scored_patients.append({
            "patient_id": rec["patient_id"],
            "name": rec["name"],
            "age": age,
            "age_band": age_band(age),
            "is_pediatric": age_band(age) in PEDS_NORMAL,
            "complaint": rec["complaint"],
            "high_risk_category": cat,
            "high_risk_phrase": phrase,
            "has_history": str(rec.get("has_history")).lower() not in ("false", "0", ""),
            "history": history,
            "vitals": {
                "hr": vitals_obj.hr,
                "rr": vitals_obj.rr,
                "spo2": vitals_obj.spo2,
                "sbp": vitals_obj.sbp,
                "temp": vitals_obj.temp,
                "avpu": vitals_obj.avpu,
                "on_oxygen": vitals_obj.on_oxygen,
            },
            "triage": {
                "acuity": res.acuity,
                "ews_score": res.ews_score,
                "confidence": res.confidence,
                "confidence_label": res.confidence_label,
                "reasons": res.reasons,
                "red_flags": res.red_flags,
                "recommended_action": res.recommended_action,
            },
            "flow": {
                "waited_minutes": waited,
                "safe_limit_minutes": limit,
                "breach": breached,
                "urgency_score": urgency,
            }
        })

    # Sort queue by clinical urgency (lower score = higher priority)
    scored_patients.sort(key=lambda p: p["flow"]["urgency_score"])

    # Aggregate stats
    total = len(scored_patients)
    n_l1 = sum(1 for p in scored_patients if p["triage"]["acuity"] == 1)
    n_l2 = sum(1 for p in scored_patients if p["triage"]["acuity"] == 2)
    n_l3 = sum(1 for p in scored_patients if p["triage"]["acuity"] == 3)
    n_breach = sum(1 for p in scored_patients if p["flow"]["breach"])

    return {
        "surge_active": surge_active,
        "surge_factor": surge_factor,
        "stats": {
            "total_patients": total,
            "level_1_resuscitation": n_l1,
            "level_2_emergent": n_l2,
            "level_3_urgent": n_l3,
            "safe_wait_breaches": n_breach,
        },
        "patients": scored_patients
    }

@app.post("/api/triage/score")
def score_custom_patient(req: ScorePatientRequest):
    """Run real-time ESI scoring for custom vitals and complaint."""
    vitals = Vitals(
        hr=req.vitals.hr,
        rr=req.vitals.rr,
        spo2=req.vitals.spo2,
        sbp=req.vitals.sbp,
        temp=req.vitals.temp,
        avpu=req.vitals.avpu or "A",
        on_oxygen=req.vitals.on_oxygen or False
    )
    history = get_history(req.patient_id) if req.patient_id else None
    res = score_patient(req.age, vitals, req.complaint, history=history)
    cat, phrase = _match_high_risk_complaint(req.complaint)

    return {
        "age": req.age,
        "age_band": age_band(req.age),
        "is_pediatric": age_band(req.age) in PEDS_NORMAL,
        "complaint": req.complaint,
        "high_risk_category": cat,
        "high_risk_phrase": phrase,
        "triage": {
            "acuity": res.acuity,
            "ews_score": res.ews_score,
            "confidence": res.confidence,
            "confidence_label": res.confidence_label,
            "reasons": res.reasons,
            "red_flags": res.red_flags,
            "recommended_action": res.recommended_action,
        }
    }

@app.post("/api/triage/override")
def record_override(req: OverrideRequest):
    """Record clinician override into the tamper-evident audit log."""
    if not req.reason.strip():
        raise HTTPException(status_code=400, detail="Clinical justification is required for override.")

    entry_hash = audit.log_event(
        "OVERRIDE",
        req.patient_id,
        {
            "from_acuity": req.from_acuity,
            "to_acuity": req.to_acuity,
            "reason": req.reason.strip()
        },
        actor=req.clinician
    )
    return {
        "success": True,
        "entry_hash": entry_hash,
        "hash_chain_intact": audit.verify_chain(),
        "message": f"Override confirmed: Level {req.from_acuity} -> Level {req.to_acuity} by {req.clinician}"
    }

@app.get("/api/audit/logs")
def get_audit_logs(role: Optional[str] = None, password: Optional[str] = None):
    """Retrieve audit logs with optional RBAC unmasking for Clinical Lead."""
    authorized = privacy.check_role_access(role or "", password or "") if password else False
    raw_logs = audit.read_log()
    
    logs = []
    for entry in raw_logs[-25:]:
        p_id = entry.get("patient_id", "")
        if authorized and p_id != "SYSTEM":
            p_id = audit.resolve_identity(p_id, role or "Clinical Lead", password or "")
        logs.append({
            "ts": entry.get("ts"),
            "event_type": entry.get("event_type"),
            "patient_id": p_id,
            "actor": entry.get("actor"),
            "payload": entry.get("payload"),
            "entry_hash": entry.get("entry_hash", "")[:12] + "..."
        })

    return {
        "authorized": authorized,
        "chain_intact": audit.verify_chain(),
        "total_events": len(raw_logs),
        "logs": list(reversed(logs))
    }

@app.get("/api/audit/verify")
def verify_audit():
    return {
        "chain_intact": audit.verify_chain(),
        "algorithm": "SHA-256 Hash Chain",
        "encryption": "Fernet AES-128-CBC at rest",
        "pseudonymization": "HMAC-SHA256"
    }

# ----------------- Serve Frontend Static Build -----------------

frontend_dist = Path(__file__).parent / "frontend" / "dist"
if frontend_dist.exists():
    app.mount("/assets", StaticFiles(directory=str(frontend_dist / "assets")), name="assets")
    
    @app.get("/{full_path:path}")
    def serve_frontend(full_path: str):
        file_path = frontend_dist / full_path
        if file_path.is_file():
            return FileResponse(file_path)
        return FileResponse(frontend_dist / "index.html")

def get_local_ip() -> str:
    import socket
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    try:
        s.connect(("8.8.8.8", 80))
        ip = s.getsockname()[0]
    except Exception:
        ip = "127.0.0.1"
    finally:
        s.close()
    return ip

if __name__ == "__main__":
    import uvicorn
    if hasattr(sys.stdout, "reconfigure"):
        try:
            sys.stdout.reconfigure(encoding="utf-8")
        except Exception:
            pass
    ip = get_local_ip()
    print("=" * 70)
    print("PatientTriage.ai - Hospital Emergency Command Center")
    print(f"  > Local URL:   http://localhost:8000")
    print(f"  > Network URL: http://{ip}:8000")
    print("=" * 70)
    uvicorn.run("server:app", host="0.0.0.0", port=8000, reload=False)
