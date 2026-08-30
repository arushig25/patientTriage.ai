"""
data_simulator.py
-----------------
Generates simulated patient intake records for PatientTriage.ai.
Includes the mandated cases:
  - ambiguous presentation
  - pediatric case
  - geriatric case
  - zero-history (first-time) patient
No real patient data is used.
"""

import csv, io, os, random

from patient_triage.security import privacy

random.seed(42)

def base_patients():
    """20 hand-crafted records covering required edge cases."""
    P = []
    # id, name, age, has_history, hr, rr, spo2, sbp, temp, avpu, on_o2, complaint
    P.append(("P01","A. Rivera",54,True,88,16,98,128,36.8,"A",False,"ankle sprain"))
    P.append(("P02","B. Chen",67,True,122,26,89,96,38.7,"V",True,"shortness of breath"))  # sick geriatric
    P.append(("P03","C. Okafor",3,True,168,44,95,None,39.2,"A",False,"fever"))            # pediatric
    P.append(("P04","D. Smith",41,False,72,14,99,None,None,None,None,"laceration"))       # zero-history, sparse
    P.append(("P05","E. Watanabe",78,True,58,12,94,138,36.2,"A",False,"dizziness"))        # geriatric ambiguous
    P.append(("P06","F. Muller",29,True,132,28,90,88,37.1,"P",False,"altered consciousness")) # critical
    P.append(("P07","G. Haddad",35,True,84,18,97,120,37.0,"A",False,"chest pain"))          # complaint-driven
    P.append(("P08","H. Ivanova",6,True,110,24,98,100,37.4,"A",False,"cough"))              # pediatric mild
    P.append(("P09","I. Brooks",50,False,96,20,96,110,37.9,"A",False,"abdominal pain"))     # zero-history ambiguous
    P.append(("P10","J. Costa",62,True,90,17,97,145,36.9,"A",False,"back pain"))
    P.append(("P11","K. Ahmed",19,True,78,15,99,118,36.7,"A",False,"headache"))
    P.append(("P12","L. Nguyen",83,True,104,22,92,98,38.1,"V",False,"confusion"))           # geriatric sepsis-ish
    P.append(("P13","M. Torres",1,True,175,52,94,None,38.9,"A",False,"irritable"))          # infant, sparse BP
    P.append(("P14","N. Green",45,True,80,16,98,124,36.6,"A",False,"wrist pain"))
    P.append(("P15","O. Petrov",70,True,48,14,95,150,36.4,"A",False,"palpitations"))         # bradycardia geriatric
    P.append(("P16","P. Silva",33,False,None,None,None,None,None,None,None,"feels unwell"))  # near-total missing
    P.append(("P17","Q. Adebayo",27,True,140,30,88,None,38.5,"P",True,"seizure"))            # critical peds-adult edge
    P.append(("P18","R. Kim",58,True,92,18,96,132,37.2,"A",False,"nausea"))
    P.append(("P19","S. Lopez",9,True,130,28,93,105,38.6,"A",False,"difficulty breathing"))  # pediatric concerning
    P.append(("P20","T. Fischer",48,True,86,19,97,122,36.9,"A",False,"minor burn"))          # ambiguous stable
    return P

COLS = ["patient_id","name","age","has_history","hr","rr","spo2","sbp",
        "temp","avpu","on_oxygen","complaint"]

# ---------- Gap 2: simulated prior-visit history ----------
# Represents what a hospital EHR would already hold for a *subset* of
# returning (has_history=True) patients -- not every returning patient has
# a fully documented baseline on file (e.g. a prior encounter that didn't
# capture full vitals), which is realistic and preserves the distinction
# between "has_history flag set" and "usable baseline available." Patients
# not listed here fall back to the original (pre-Gap-2) scoring behavior.
#
# Three intentionally-varied demo cases are included among the eight:
#   - P02: chronic COPD -- shows the red-flag SpO2 floor lowering.
#   - P15: current HR is within 10% of documented baseline -- shows the
#     population-abnormal score being eased down (known-abnormal-for-them).
#   - P11: current HR is 30% above documented baseline while still
#     population-normal -- shows the new-deviation awareness bump.
# The rest (P07, P10, P14, P18, P20) are realistic "unremarkable" history
# entries -- most returning-patient visits don't change the outcome, and a
# feature that only ever fires dramatically wouldn't be honest about that.
HISTORY = {
    "P02": {"baseline_hr": 95,  "baseline_sbp": 100, "chronic_conditions": ["COPD"],
            "last_visit_acuity": 3, "last_visit_date": "2026-05-14"},
    "P07": {"baseline_hr": 82,  "baseline_sbp": 118, "chronic_conditions": [],
            "last_visit_acuity": 4, "last_visit_date": "2026-07-02"},
    "P10": {"baseline_hr": 88,  "baseline_sbp": 140, "chronic_conditions": ["cardiac"],
            "last_visit_acuity": 3, "last_visit_date": "2026-06-20"},
    "P11": {"baseline_hr": 60,  "baseline_sbp": 116, "chronic_conditions": [],
            "last_visit_acuity": 5, "last_visit_date": "2026-02-11"},
    "P14": {"baseline_hr": 78,  "baseline_sbp": 120, "chronic_conditions": [],
            "last_visit_acuity": 4, "last_visit_date": "2026-01-30"},
    "P15": {"baseline_hr": 46,  "baseline_sbp": 148, "chronic_conditions": ["cardiac"],
            "last_visit_acuity": 4, "last_visit_date": "2026-06-05"},
    "P18": {"baseline_hr": 90,  "baseline_sbp": 130, "chronic_conditions": [],
            "last_visit_acuity": 4, "last_visit_date": "2026-03-22"},
    "P20": {"baseline_hr": 84,  "baseline_sbp": 120, "chronic_conditions": [],
            "last_visit_acuity": 5, "last_visit_date": "2026-04-18"},
}


def get_history(patient_id):
    """Return the documented history dict for a patient, or None if no
    baseline is on file (zero-history patients and returning patients
    without a captured baseline both return None). Accepts surge-suffixed
    IDs (e.g. "P02-s1") by resolving back to the base patient's history."""
    return HISTORY.get(base_patient_id(patient_id))


def base_patient_id(patient_id):
    """Strip the "-sN" surge-replica suffix added by surge_patients(),
    e.g. "P02-s1" -> "P02". IDs without a suffix pass through unchanged."""
    return patient_id.split("-s")[0] if "-s" in patient_id else patient_id

def write_csv(path="data/patients.csv"):
    """Write the base patient dataset, encrypted at rest (Gap 4) -- the
    file on disk is a Fernet blob, never plaintext CSV. Use
    read_csv_decrypted() to get the rows back."""
    os.makedirs(os.path.dirname(path), exist_ok=True)
    buf = io.StringIO()
    w = csv.writer(buf)
    w.writerow(COLS)
    for row in base_patients():
        w.writerow(row)
    privacy.write_encrypted(path, buf.getvalue())
    return path


def read_csv_decrypted(path="data/patients.csv"):
    """Return the base patient dataset as a list of dicts, decrypting
    the at-rest file written by write_csv(). Raises FileNotFoundError
    if write_csv() hasn't been run yet."""
    raw = privacy.read_encrypted(path)
    if not raw:
        raise FileNotFoundError(f"{path} not found -- run write_csv() first")
    return list(csv.DictReader(io.StringIO(raw)))

def surge_patients(multiplier=3):
    """Return base patients replicated & jittered to simulate a surge."""
    out = []
    base = base_patients()
    for m in range(multiplier):
        for r in base:
            r = list(r)
            r[0] = f"{r[0]}-s{m}"
            for i in (4,5,6,7):  # jitter hr, rr, spo2, sbp if present
                if r[i] is not None:
                    r[i] = max(0, r[i] + random.randint(-6, 6))
            out.append(tuple(r))
    return out

if __name__ == "__main__":
    print("Wrote", write_csv())

