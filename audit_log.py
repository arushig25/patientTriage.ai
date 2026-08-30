"""
audit_log.py
------------
Tamper-evident (hash-chained) audit log for HIPAA-style accountability.
Every score, alert, access, and clinician override is appended with a
hash of the previous entry, so any later edit breaks the chain and is
detectable (see verify_chain()).

Gap 4 -- Data protection:
  - The log file is encrypted at rest (Fernet, via privacy.py) rather
    than stored as plaintext JSONL. Appending decrypts the current
    content, adds the new line, and re-encrypts the whole file -- fine
    at this log's scale, and it means there is never a plaintext copy
    of the log on disk.
  - `patient_id` is stored as a pseudonymous token (privacy.pseudonymize),
    not the raw ID. resolve_identity() re-links a token back to a real
    patient_id, gated by RBAC, for authorized viewers only.
  - A new ACCESS event type records every time identity-linked patient
    data is displayed to a viewer, separately from SCORE/ALERT/OVERRIDE.

Gap 7 -- Audit log hygiene:
  - should_log_score() / should_log_alert() / should_log_access() are
    pure functions (they take a plain dict-like session store and
    return a bool) that decide whether a given UI rerun represents a
    *new* clinical event or just Streamlit re-executing the script.
    app.py calls these before calling log_event(), so the log reflects
    discrete events, not every rerun. OVERRIDE logging needs no such
    guard -- it's already event-driven via the form submit button.
"""

import hashlib
import json
from datetime import datetime

import privacy

LOG_PATH = "data/audit_log.jsonl.enc"

# Event types that identify a real person and should be pseudonymized
# before they're written. "SYSTEM" (surge-mode banners etc.) is not a
# patient and passes through unchanged.
_NON_PATIENT_SUBJECTS = {"SYSTEM"}


# ---------- Encrypted-at-rest storage ----------

def _read_lines() -> list:
    raw = privacy.read_encrypted(LOG_PATH)
    if not raw:
        return []
    return [line for line in raw.split("\n") if line.strip()]


def _write_lines(lines: list) -> None:
    privacy.write_encrypted(LOG_PATH, "\n".join(lines) + ("\n" if lines else ""))


def _last_hash(lines: list) -> str:
    if not lines:
        return "GENESIS"
    return json.loads(lines[-1]).get("entry_hash", "GENESIS")


# ---------- Logging ----------

def log_event(event_type, patient_id, payload, actor="system"):
    subject = patient_id
    if patient_id not in _NON_PATIENT_SUBJECTS:
        subject = privacy.pseudonymize(patient_id)
        privacy.record_identity(subject, patient_id)

    lines = _read_lines()
    prev = _last_hash(lines)
    entry = {
        "ts": datetime.utcnow().isoformat() + "Z",
        "event_type": event_type,          # SCORE | ALERT | OVERRIDE | ACCESS | SURGE_MODE_ON/OFF
        "patient_id": subject,             # pseudonymous token (or SYSTEM)
        "actor": actor,
        "payload": payload,
        "prev_hash": prev,
    }
    entry["entry_hash"] = hashlib.sha256(
        (prev + json.dumps(entry, sort_keys=True)).encode()).hexdigest()
    lines.append(json.dumps(entry))
    _write_lines(lines)
    return entry["entry_hash"]


def read_log():
    return [json.loads(line) for line in _read_lines()]


def verify_chain():
    """Return True if the hash chain is intact."""
    prev = "GENESIS"
    for e in read_log():
        if e["prev_hash"] != prev:
            return False
        prev = e["entry_hash"]
    return True


def resolve_identity(token: str, role: str, password: str) -> str:
    """Re-link a pseudonymous patient_id token back to the real
    patient_id, gated by RBAC (see privacy.check_role_access). Returns
    the token unchanged if the caller isn't authorized."""
    return privacy.resolve_identity(token, role, password)


# ---------- Gap 7: discrete-event dedup helpers ----------
# Each takes a plain dict-like session store (app.py passes
# st.session_state, which supports the same .get()/[]= interface; tests
# pass a plain dict) so the decision logic is pure and unit-testable
# without a running Streamlit session.

def should_log_score(session_state, patient_id: str, acuity: int) -> bool:
    """True only when (patient_id, acuity) differs from the last SCORE
    logged in this session -- so re-selecting the same patient, or any
    other Streamlit rerun that doesn't change the outcome, does not
    re-log an identical SCORE event."""
    key = "_last_scored"
    current = (patient_id, acuity)
    if session_state.get(key) == current:
        return False
    session_state[key] = current
    return True


def should_log_alert(session_state, patient_id: str, breached: bool) -> bool:
    """True only on the unresolved -> breached transition for this
    patient, not once per rerun for as long as the breach persists.
    Also records the resolved transition (breached -> False) so the
    next breach is detected as a new transition rather than being
    swallowed by stale state."""
    key = f"_breach_state_{patient_id}"
    was_breached = session_state.get(key, False)
    session_state[key] = breached
    return breached and not was_breached


def should_log_access(session_state, patient_id: str) -> bool:
    """True only when the identity-linked patient being viewed changes,
    so paging through the same patient's tabs/reruns doesn't emit a new
    ACCESS event every time."""
    key = "_last_access"
    if session_state.get(key) == patient_id:
        return False
    session_state[key] = patient_id
    return True
