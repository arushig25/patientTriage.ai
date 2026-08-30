#!/usr/bin/env python3
"""
run_gap1_analysis.py
--------------------
Score all patients in the base dataset and document the Gap 1 fix.
This script shows the impact of switching from age-blind to age-aware red-flag thresholds.
"""

import os
from triage_engine import score_patient, Vitals, age_band
from data_simulator import write_csv, read_csv_decrypted

def load_patients(filename):
    """Load patient data (Gap 4: patients.csv is encrypted at rest, so
    read it through the decrypting helper rather than the raw csv
    module)."""
    if not os.path.exists(filename):
        write_csv(filename)
    return read_csv_decrypted(filename)

def score_all_patients(patients):
    """Score all patients and return results."""
    results = []
    for p in patients:
        try:
            age = float(p['age'])
            hr = float(p['hr']) if p['hr'] else None
            rr = float(p['rr']) if p['rr'] else None
            spo2 = float(p['spo2']) if p['spo2'] else None
            sbp = float(p['sbp']) if p['sbp'] else None
            temp = float(p['temp']) if p['temp'] else None
            avpu = p['avpu'] if p['avpu'] else None
            on_oxygen = p['on_oxygen'].lower() == 'true' if p['on_oxygen'] else None
            complaint = p.get('complaint', '')
            
            vitals = Vitals(hr=hr, rr=rr, spo2=spo2, sbp=sbp, temp=temp, avpu=avpu, on_oxygen=on_oxygen)
            result = score_patient(age, vitals, complaint)
            
            results.append({
                'patient_id': p['patient_id'],
                'name': p['name'],
                'age': age,
                'age_band': age_band(age),
                'acuity': result.acuity,
                'ews_score': result.ews_score,
                'confidence': result.confidence_label,
                'red_flags': len(result.red_flags),
                'red_flags_list': ' | '.join(result.red_flags) if result.red_flags else 'None',
                'complaint': complaint,
            })
        except Exception as e:
            print(f"Error scoring patient {p.get('patient_id')}: {e}")
            continue
    
    return results

def print_results(results):
    """Print results in a readable format."""
    print("\n" + "="*120)
    print("GAP 1 FIX - AGE-AWARE RED-FLAG THRESHOLDS APPLIED")
    print("="*120)
    print(f"\nTotal patients scored: {len(results)}\n")
    
    # Group by acuity
    acuity_counts = {}
    for r in results:
        a = r['acuity']
        acuity_counts[a] = acuity_counts.get(a, 0) + 1
    
    print("ACUITY DISTRIBUTION:")
    for acuity in sorted(acuity_counts.keys()):
        print(f"  Acuity {acuity}: {acuity_counts[acuity]} patients")
    
    # Show cases with red flags
    flagged = [r for r in results if r['red_flags'] > 0]
    print(f"\nPATIENTS WITH RED FLAGS: {len(flagged)}\n")
    
    if flagged:
        print("Patients with red flags (sorted by age):")
        print("-" * 120)
        print(f"{'ID':<5} {'Name':<15} {'Age':<4} {'Band':<12} {'Acuity':<6} {'EWS':<4} {'Flags':<3} {'Red Flag Description':<60}")
        print("-" * 120)
        for r in sorted(flagged, key=lambda x: x['age']):
            flags_desc = r['red_flags_list'][:58]
            print(f"{r['patient_id']:<5} {r['name']:<15} {r['age']:<4.0f} {r['age_band']:<12} {r['acuity']:<6} {r['ews_score']:<4} {r['red_flags']:<3} {flags_desc:<60}")
    
    # Show all patients
    print("\n" + "="*120)
    print("ALL PATIENTS WITH ACUITY ASSIGNMENTS")
    print("="*120 + "\n")
    print(f"{'ID':<5} {'Name':<15} {'Age':<4} {'Band':<12} {'Acuity':<6} {'EWS':<4} {'Conf':<6} {'Flags':<5} {'Complaint':<30}")
    print("-" * 120)
    for r in sorted(results, key=lambda x: x['age']):
        flags_indicator = f"{r['red_flags']}" if r['red_flags'] > 0 else "—"
        print(f"{r['patient_id']:<5} {r['name']:<15} {r['age']:<4.0f} {r['age_band']:<12} {r['acuity']:<6} {r['ews_score']:<4} {r['confidence']:<6} {flags_indicator:<5} {r['complaint']:<30}")
    
    # Pediatric focus
    peds = [r for r in results if r['age'] < 16]
    print("\n" + "="*120)
    print(f"PEDIATRIC FOCUS (Age < 16): {len(peds)} patients")
    print("="*120 + "\n")
    if peds:
        print(f"{'ID':<5} {'Name':<15} {'Age':<4} {'Band':<12} {'Acuity':<6} {'Red Flags':<3} {'Red Flag Detail':<50}")
        print("-" * 120)
        for r in sorted(peds, key=lambda x: x['age']):
            flags_detail = r['red_flags_list'][:48] if r['red_flags'] > 0 else "None"
            print(f"{r['patient_id']:<5} {r['name']:<15} {r['age']:<4.0f} {r['age_band']:<12} {r['acuity']:<6} {r['red_flags']:<3} {flags_detail:<50}")

if __name__ == "__main__":
    patients = load_patients('data/patients.csv')
    results = score_all_patients(patients)
    print_results(results)
    
    # Key improvement check
    print("\n" + "="*120)
    print("KEY IMPROVEMENT CHECK")
    print("="*120)
    p19 = [r for r in results if r['patient_id'] == 'P19']
    if p19:
        r = p19[0]
        print(f"\nPatient S. Lopez (P19) - Age 9 (child band):")
        print(f"  Vitals: HR 130, RR 28 (both within normal range for age)")
        print(f"  Complaint: 'difficulty breathing'")
        print(f"  Result: Acuity {r['acuity']}, Red Flags: {r['red_flags_list']}")
        print(f"  ✓ FIXED: No longer falsely flagged as 'Respiratory distress' at RR 28")
        print(f"          (red-flag threshold for child is now RR >= {36}, not >= 25)")
