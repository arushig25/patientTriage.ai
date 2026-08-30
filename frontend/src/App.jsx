import React, { useState, useEffect } from 'react';
import Header from './components/Header';
import TriageNurseView from './components/TriageNurseView';
import ChargeNurseView from './components/ChargeNurseView';
import ClinicalLeadView from './components/ClinicalLeadView';

export default function App() {
  const [currentRole, setRole] = useState('Triage Nurse');
  const [surgeActive, setSurge] = useState(false);
  const [data, setData] = useState({ patients: [], stats: {}, surge_factor: 1.0 });
  const [selectedPatient, setSelectedPatient] = useState(null);
  const [loading, setLoading] = useState(true);
  
  // Theme state: defaults to clean clinical light mode (can toggle to dark)
  const [darkMode, setDarkMode] = useState(() => {
    const saved = localStorage.getItem('pt_theme');
    return saved ? saved === 'dark' : false;
  });

  useEffect(() => {
    if (darkMode) {
      document.documentElement.classList.add('dark');
      localStorage.setItem('pt_theme', 'dark');
    } else {
      document.documentElement.classList.remove('dark');
      localStorage.setItem('pt_theme', 'light');
    }
  }, [darkMode]);

  const fetchPatients = async (surge = false) => {
    try {
      setLoading(true);
      const res = await fetch(`/api/patients?surge=${surge}`);
      const json = await res.json();
      setData(json);
      if (json.patients && json.patients.length > 0) {
        setSelectedPatient(prev => {
          if (!prev) return json.patients[0];
          const found = json.patients.find(p => p.patient_id === prev.patient_id);
          return found || json.patients[0];
        });
      }
    } catch (err) {
      console.error('Failed to load patients:', err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchPatients(surgeActive);
  }, [surgeActive]);

  // Real-time Override Handler with Optimistic UI updates
  const handleRecordOverride = async (overrideData) => {
    const { patient_id, from_acuity, to_acuity, reason, clinician } = overrideData;
    const safeReason = reason && reason.trim() ? reason.trim() : 'Direct clinician clinical override';

    // 1. Optimistic UI update in real time
    setData(prev => {
      const updatedPatients = prev.patients.map(p => {
        if (p.patient_id === patient_id) {
          return {
            ...p,
            is_overridden: true,
            override_info: {
              acuity: to_acuity,
              from_acuity,
              reason: safeReason,
              clinician
            },
            triage: {
              ...p.triage,
              acuity: to_acuity,
              reasons: [
                `[CLINICIAN OVERRIDE] Adjusted to Level ${to_acuity}: ${safeReason} (by ${clinician})`,
                ...p.triage.reasons
              ],
              recommended_action: `Assigned Level ${to_acuity} care stream via clinician override (${clinician}).`
            }
          };
        }
        return p;
      });
      return { ...prev, patients: updatedPatients };
    });

    setSelectedPatient(prev => {
      if (prev && prev.patient_id === patient_id) {
        return {
          ...prev,
          is_overridden: true,
          override_info: {
            acuity: to_acuity,
            from_acuity,
            reason: safeReason,
            clinician
          },
          triage: {
            ...prev.triage,
            acuity: to_acuity,
            reasons: [
              `[CLINICIAN OVERRIDE] Adjusted to Level ${to_acuity}: ${safeReason} (by ${clinician})`,
              ...prev.triage.reasons
            ],
            recommended_action: `Assigned Level ${to_acuity} care stream via clinician override (${clinician}).`
          }
        };
      }
      return prev;
    });

    // 2. Synchronize to server and audit chain
    try {
      const res = await fetch('/api/triage/override', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          patient_id,
          from_acuity,
          to_acuity,
          reason: safeReason,
          clinician: clinician || 'RN-1042'
        }),
      });
      const json = await res.json();
      return json;
    } catch (err) {
      console.error('Failed to record override:', err);
      return { success: false };
    }
  };

  // Real-time Patient Data Update Handler (Vitals & Complaints)
  const handleUpdatePatient = async (patientId, updatePayload) => {
    try {
      await fetch('/api/patient/update', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          patient_id: patientId,
          ...updatePayload
        }),
      });
      // Re-fetch to get new calculated scores and queue ranks in real time
      await fetchPatients(surgeActive);
    } catch (err) {
      console.error('Failed to update patient:', err);
    }
  };

  const handleVerifyChain = async () => {
    try {
      const res = await fetch('/api/audit/verify');
      const json = await res.json();
      alert(`Audit Chain Status: ${json.chain_intact ? '✓ INTACT' : '❌ COMPROMISED'}\nAlgorithm: ${json.algorithm}\nEncryption: ${json.encryption}`);
    } catch (err) {
      alert('Failed to verify audit hash chain.');
    }
  };

  return (
    <div className="min-h-screen bg-clinical-50 dark:bg-clinical-950 text-clinical-900 dark:text-slate-100 flex flex-col font-sans transition-colors duration-200">
      <Header
        currentRole={currentRole}
        setRole={setRole}
        surgeActive={surgeActive}
        setSurge={setSurge}
        surgeFactor={data.surge_factor || 1.0}
        stats={data.stats || {}}
        darkMode={darkMode}
        setDarkMode={setDarkMode}
        onVerifyChain={handleVerifyChain}
      />

      <main className="flex-1 max-w-7xl w-full mx-auto px-4 sm:px-6 lg:px-8 py-6">
        {loading && data.patients.length === 0 ? (
          <div className="flex flex-col items-center justify-center py-24 space-y-3">
            <div className="w-10 h-10 border-4 border-brand-500/30 border-t-brand-600 rounded-full animate-spin"></div>
            <p className="text-sm font-bold text-clinical-500">Loading Clinical Command Center...</p>
          </div>
        ) : (
          <>
            {currentRole === 'Triage Nurse' && (
              <TriageNurseView
                patients={data.patients || []}
                selectedPatient={selectedPatient}
                onSelectPatient={setSelectedPatient}
                onRecordOverride={handleRecordOverride}
                onUpdatePatient={handleUpdatePatient}
              />
            )}

            {currentRole === 'Charge Nurse' && (
              <ChargeNurseView
                patients={data.patients || []}
                stats={data.stats || {}}
                surgeActive={surgeActive}
                surgeFactor={data.surge_factor || 1.0}
                onSelectPatient={setSelectedPatient}
                setRole={setRole}
              />
            )}

            {currentRole === 'Clinical Lead' && (
              <ClinicalLeadView
                patients={data.patients || []}
              />
            )}
          </>
        )}
      </main>

      <footer className="border-t border-clinical-200 dark:border-clinical-800/80 bg-white dark:bg-clinical-950/80 py-3.5 px-4 sm:px-8 text-center text-xs text-clinical-500 font-medium">
        PatientTriage.ai &middot; Clinical Emergency Department Decision Support System &middot; HIPAA Security Architecture &middot; Clinician Judgment Supersedes All Model Recommendations
      </footer>
    </div>
  );
}
