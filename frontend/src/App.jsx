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

  const handleRecordOverride = async (overrideData) => {
    try {
      const res = await fetch('/api/triage/override', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(overrideData),
      });
      const json = await res.json();
      fetchPatients(surgeActive);
      return json;
    } catch (err) {
      console.error('Failed to record override:', err);
      return { success: false };
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
