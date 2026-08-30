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

import csv, os, random

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

def write_csv(path="data/patients.csv"):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", newline="") as f:
        w = csv.writer(f)
        w.writerow(COLS)
        for row in base_patients():
            w.writerow(row)
    return path

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
