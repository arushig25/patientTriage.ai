"""
audit_log.py
------------
Tamper-evident (hash-chained) audit log for HIPAA-style accountability.
Every score, alert, and clinician override is appended with a hash of the
previous entry, so any later edit breaks the chain and is detectable.
"""

import json, hashlib, os
from datetime import datetime

LOG_PATH = "data/audit_log.jsonl"

def _last_hash():
    if not os.path.exists(LOG_PATH):
        return "GENESIS"
    last = None
    with open(LOG_PATH) as f:
        for line in f:
            last = line
    if not last:
        return "GENESIS"
    return json.loads(last).get("entry_hash", "GENESIS")

def log_event(event_type, patient_id, payload, actor="system"):
    os.makedirs(os.path.dirname(LOG_PATH), exist_ok=True)
    prev = _last_hash()
    entry = {
        "ts": datetime.utcnow().isoformat() + "Z",
        "event_type": event_type,          # SCORE | ALERT | OVERRIDE
        "patient_id": patient_id,
        "actor": actor,
        "payload": payload,
        "prev_hash": prev,
    }
    entry["entry_hash"] = hashlib.sha256(
        (prev + json.dumps(entry, sort_keys=True)).encode()).hexdigest()
    with open(LOG_PATH, "a") as f:
        f.write(json.dumps(entry) + "\n")
    return entry["entry_hash"]

def read_log():
    if not os.path.exists(LOG_PATH):
        return []
    with open(LOG_PATH) as f:
        return [json.loads(l) for l in f if l.strip()]

def verify_chain():
    """Return True if the hash chain is intact."""
    prev = "GENESIS"
    for e in read_log():
        if e["prev_hash"] != prev:
            return False
        prev = e["entry_hash"]
    return True
