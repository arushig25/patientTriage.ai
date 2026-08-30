import React, { useState, useEffect } from 'react';
import { 
  Heart, 
  Wind, 
  Droplets, 
  Gauge, 
  Thermometer, 
  Brain, 
  AlertOctagon, 
  CheckCircle2, 
  Clock, 
  History, 
  Shield, 
  ArrowRight,
  Sparkles,
  UserCheck,
  Search,
  Sliders,
  Check,
  AlertCircle
} from 'lucide-react';
import AcuityBadge, { ACUITY_CONFIG } from './AcuityBadge';
import ECGWaveform from './ECGWaveform';

export default function TriageNurseView({ 
  patients = [], 
  selectedPatient, 
  onSelectPatient, 
  onRecordOverride,
  onUpdatePatient
}) {
  const [activeTab, setActiveTab] = useState('patient');
  const [searchTerm, setSearchTerm] = useState('');
  
  // Override form state
  const patient = selectedPatient || patients[0];
  const [overrideAcuity, setOverrideAcuity] = useState(patient?.triage?.acuity || 3);
  const [overrideReason, setOverrideReason] = useState('');
  const [clinicianId, setClinicianId] = useState('RN-1042');
  const [overrideStatus, setOverrideStatus] = useState(null);

  // Live Vital Edit Mode state
  const [isEditingVitals, setIsEditingVitals] = useState(false);
  const [editHr, setEditHr] = useState(patient?.vitals?.hr || 75);
  const [editRr, setEditRr] = useState(patient?.vitals?.rr || 16);
  const [editSpo2, setEditSpo2] = useState(patient?.vitals?.spo2 || 98);
  const [editSbp, setEditSbp] = useState(patient?.vitals?.sbp || 120);
  const [editTemp, setEditTemp] = useState(patient?.vitals?.temp || 36.8);
  const [editAvpu, setEditAvpu] = useState(patient?.vitals?.avpu || 'A');

  // Keep inputs in sync when selecting another patient
  useEffect(() => {
    if (patient) {
      setOverrideAcuity(patient.triage?.acuity || 3);
      setEditHr(patient.vitals?.hr || 75);
      setEditRr(patient.vitals?.rr || 16);
      setEditSpo2(patient.vitals?.spo2 || 98);
      setEditSbp(patient.vitals?.sbp || 120);
      setEditTemp(patient.vitals?.temp || 36.8);
      setEditAvpu(patient.vitals?.avpu || 'A');
      setOverrideStatus(null);
    }
  }, [patient?.patient_id]);

  // Live simulator state
  const [simAge, setSimAge] = useState(45);
  const [simComplaint, setSimComplaint] = useState('Crushing retrosternal chest pressure');
  const [simHr, setSimHr] = useState(105);
  const [simRr, setSimRr] = useState(24);
  const [simSpo2, setSimSpo2] = useState(93);
  const [simSbp, setSimSbp] = useState(115);
  const [simTemp, setSimTemp] = useState(37.2);
  const [simAvpu, setSimAvpu] = useState('A');
  const [simOxygen, setSimOxygen] = useState(false);
  const [simResult, setSimResult] = useState(null);
  const [simLoading, setSimLoading] = useState(false);

  const filteredPatients = patients.filter(p => 
    p.name.toLowerCase().includes(searchTerm.toLowerCase()) ||
    p.patient_id.toLowerCase().includes(searchTerm.toLowerCase()) ||
    p.complaint.toLowerCase().includes(searchTerm.toLowerCase())
  );

  // Instant real-time override trigger
  const triggerRealtimeOverride = async (targetLevel, reasonText) => {
    if (!patient) return;
    const finalReason = reasonText || overrideReason || 'Direct clinician clinical adjustment';
    setOverrideAcuity(targetLevel);
    setOverrideReason(finalReason);

    setOverrideStatus(`Updating to Level ${targetLevel} in real time...`);
    const res = await onRecordOverride({
      patient_id: patient.patient_id,
      from_acuity: patient.triage.acuity,
      to_acuity: Number(targetLevel),
      reason: finalReason,
      clinician: clinicianId,
    });
    if (res && res.success) {
      setOverrideStatus(`✓ Real-Time Override Active: Assigned Level ${targetLevel} by ${clinicianId}. Authenticated to SHA-256 audit log.`);
    }
  };

  const handleQuickReasonClick = (reasonChip) => {
    setOverrideReason(reasonChip);
    triggerRealtimeOverride(overrideAcuity, reasonChip);
  };

  const handleSaveVitals = async () => {
    if (!patient || !onUpdatePatient) return;
    await onUpdatePatient(patient.patient_id, {
      vitals: {
        hr: Number(editHr),
        rr: Number(editRr),
        spo2: Number(editSpo2),
        sbp: Number(editSbp),
        temp: Number(editTemp),
        avpu: editAvpu,
      }
    });
    setIsEditingVitals(false);
  };

  const simPresets = [
    {
      name: '🚨 Septic Shock (L1)',
      age: 68,
      complaint: 'Altered mental status, shaking chills, fever',
      hr: 138,
      rr: 32,
      spo2: 89,
      sbp: 74,
      temp: 39.4,
      avpu: 'V',
      on_oxygen: true,
    },
    {
      name: '🫀 Acute STEMI (L2)',
      age: 54,
      complaint: 'Crushing retrosternal chest pain with diaphoresis',
      hr: 108,
      rr: 22,
      spo2: 93,
      sbp: 145,
      temp: 37.0,
      avpu: 'A',
      on_oxygen: false,
    },
    {
      name: '🧒 Pediatric Stridor (L2)',
      age: 3,
      complaint: 'Barking cough, inspiratory stridor, retractions',
      hr: 155,
      rr: 44,
      spo2: 91,
      sbp: 95,
      temp: 38.6,
      avpu: 'A',
      on_oxygen: false,
    },
    {
      name: '🧠 Acute Stroke Alert (L2)',
      age: 72,
      complaint: 'Sudden left-sided facial droop and arm weakness',
      hr: 82,
      rr: 18,
      spo2: 97,
      sbp: 178,
      temp: 36.9,
      avpu: 'A',
      on_oxygen: false,
    },
    {
      name: '🩹 Mild Ankle Sprain (L4)',
      age: 26,
      complaint: 'Right lateral ankle pain and mild swelling after twisting',
      hr: 72,
      rr: 15,
      spo2: 99,
      sbp: 118,
      temp: 36.6,
      avpu: 'A',
      on_oxygen: false,
    }
  ];

  const loadPreset = (p) => {
    setSimAge(p.age);
    setSimComplaint(p.complaint);
    setSimHr(p.hr);
    setSimRr(p.rr);
    setSimSpo2(p.spo2);
    setSimSbp(p.sbp);
    setSimTemp(p.temp);
    setSimAvpu(p.avpu);
    setSimOxygen(p.on_oxygen);
  };

  const handleRunSimulator = async () => {
    setSimLoading(true);
    try {
      const res = await fetch('/api/triage/score', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          age: Number(simAge),
          complaint: simComplaint,
          vitals: {
            hr: Number(simHr),
            rr: Number(simRr),
            spo2: Number(simSpo2),
            sbp: Number(simSbp),
            temp: Number(simTemp),
            avpu: simAvpu,
            on_oxygen: simOxygen
          }
        })
      });
      const data = await res.json();
      setSimResult(data);
    } catch (err) {
      console.error(err);
    } finally {
      setSimLoading(false);
    }
  };

  // Auto-calculate simulator output whenever parameters change
  useEffect(() => {
    if (activeTab === 'simulator') {
      const timer = setTimeout(() => {
        handleRunSimulator();
      }, 150);
      return () => clearTimeout(timer);
    }
  }, [activeTab, simAge, simComplaint, simHr, simRr, simSpo2, simSbp, simTemp, simAvpu, simOxygen]);

  if (!patient && patients.length === 0) {
    return <div className="p-8 text-center text-clinical-400 font-bold">Loading emergency patients...</div>;
  }

  const v = patient ? patient.vitals : {};
  const t = patient ? patient.triage : {};
  const isPeds = patient ? patient.is_pediatric : false;
  const isOverridden = patient ? patient.is_overridden : false;

  const quickReasons = [
    'Clinical Gestalt / Intuition',
    'High-Risk Medical History',
    'Deteriorating Presentation',
    'Physician Direct Order',
    'Borderline Vital Parameters',
  ];

  return (
    <div className="space-y-6">
      {/* Sub-navigation tabs */}
      <div className="flex items-center justify-between border-b border-clinical-200 dark:border-clinical-800 pb-3">
        <div className="flex items-center gap-2">
          <button
            onClick={() => setActiveTab('patient')}
            className={`px-4 py-2 rounded-xl text-xs font-black transition-all flex items-center gap-2 ${
              activeTab === 'patient'
                ? 'bg-brand-600 text-white shadow-sm'
                : 'text-clinical-600 dark:text-clinical-400 hover:bg-clinical-100 dark:hover:bg-clinical-900'
            }`}
          >
            <UserCheck className="w-4 h-4" />
            <span>Arriving Patient Intake</span>
          </button>
          <button
            onClick={() => setActiveTab('simulator')}
            className={`px-4 py-2 rounded-xl text-xs font-black transition-all flex items-center gap-2 ${
              activeTab === 'simulator'
                ? 'bg-brand-600 text-white shadow-sm'
                : 'text-clinical-600 dark:text-clinical-400 hover:bg-clinical-100 dark:hover:bg-clinical-900'
            }`}
          >
            <Sparkles className="w-4 h-4 text-amber-500" />
            <span>Live Triage Simulator</span>
          </button>
        </div>

        {activeTab === 'patient' && (
          <div className="text-xs text-clinical-500 font-bold">
            Active ED Arrivals: <span className="text-brand-700 dark:text-brand-400 font-mono">{patients.length}</span>
          </div>
        )}
      </div>

      {activeTab === 'simulator' ? (
        /* LIVE TRIAGE SIMULATOR VIEW */
        <div className="card-surface p-6 space-y-6">
          <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 pb-4 border-b border-clinical-200 dark:border-clinical-800">
            <div>
              <h2 className="text-lg font-black text-clinical-900 dark:text-white flex items-center gap-2">
                <Sparkles className="w-5 h-5 text-brand-600 dark:text-brand-400" />
                <span>Instant Clinical Triage Simulator</span>
              </h2>
              <p className="text-xs text-clinical-500 dark:text-clinical-400 font-medium mt-0.5">
                Real-time ESI scoring calculator. Move any slider or select a clinical preset to see AI recommendations recalculate live.
              </p>
            </div>

            <div className="flex items-center gap-2">
              <span className={`px-2.5 py-1 rounded-full text-xs font-black border flex items-center gap-1.5 ${
                simLoading
                  ? 'bg-amber-50 text-amber-700 border-amber-300 dark:bg-amber-950 dark:text-amber-300'
                  : 'bg-emerald-50 text-emerald-700 border-emerald-300 dark:bg-emerald-950 dark:text-emerald-300'
              }`}>
                <span className={`w-2 h-2 rounded-full ${simLoading ? 'bg-amber-500 animate-ping' : 'bg-emerald-500'}`}></span>
                <span>{simLoading ? 'Calculating...' : 'Live Synced'}</span>
              </span>
            </div>
          </div>

          {/* 1-Click Scenario Presets */}
          <div>
            <span className="text-[11px] font-black uppercase tracking-wider text-clinical-500 block mb-2">
              1-Click Clinical Emergency Presets:
            </span>
            <div className="flex flex-wrap gap-2">
              {simPresets.map((p, i) => (
                <button
                  key={i}
                  type="button"
                  onClick={() => loadPreset(p)}
                  className="px-3 py-1.5 rounded-xl text-xs font-black bg-clinical-100 dark:bg-clinical-900 text-clinical-800 dark:text-slate-200 hover:bg-brand-600 hover:text-white border border-clinical-200 dark:border-clinical-800 transition-all shadow-xs"
                >
                  {p.name}
                </button>
              ))}
            </div>
          </div>

          {/* Interactive Parameters Grid */}
          <div className="grid grid-cols-1 md:grid-cols-3 gap-6 p-4 rounded-2xl bg-clinical-50/50 dark:bg-clinical-950/40 border border-clinical-200 dark:border-clinical-800">
            {/* Column 1: Demographics & Complaint */}
            <div className="space-y-4">
              <label className="block text-xs font-black uppercase tracking-wider text-clinical-500">
                Patient Presentation
              </label>
              <div>
                <div className="flex items-center justify-between text-xs font-bold text-clinical-700 dark:text-clinical-300 mb-1">
                  <span>Age</span>
                  <span className="font-mono text-brand-600 dark:text-brand-400 font-black">{simAge} yrs</span>
                </div>
                <input
                  type="range"
                  min="0"
                  max="100"
                  value={simAge}
                  onChange={(e) => setSimAge(Number(e.target.value))}
                  className="w-full accent-brand-600 h-1.5 bg-clinical-200 dark:bg-clinical-800 rounded-lg cursor-pointer"
                />
                <div className="flex justify-between text-[10px] text-clinical-400 font-bold mt-1">
                  <span>0y (Infant)</span>
                  <span>18y</span>
                  <span>100y</span>
                </div>
              </div>

              <div>
                <span className="text-xs font-bold text-clinical-700 dark:text-clinical-300 block mb-1">Chief Complaint</span>
                <input
                  type="text"
                  value={simComplaint}
                  onChange={(e) => setSimComplaint(e.target.value)}
                  placeholder="e.g. Chest pain, severe SOB..."
                  className="w-full bg-white dark:bg-clinical-900 border border-clinical-200 dark:border-clinical-800 rounded-xl px-3 py-2 text-xs text-clinical-900 dark:text-white focus:border-brand-500 focus:outline-none font-bold"
                />
              </div>

              <div>
                <span className="text-xs font-bold text-clinical-700 dark:text-clinical-300 block mb-1.5">Consciousness (AVPU)</span>
                <div className="grid grid-cols-4 gap-1.5">
                  {['A', 'V', 'P', 'U'].map((scale) => (
                    <button
                      key={scale}
                      type="button"
                      onClick={() => setSimAvpu(scale)}
                      className={`py-2 rounded-xl text-xs font-black border transition-all ${
                        simAvpu === scale
                          ? 'bg-brand-600 text-white border-brand-700 shadow-sm'
                          : 'bg-white dark:bg-clinical-900 text-clinical-700 dark:text-slate-300 border-clinical-200 dark:border-clinical-800 hover:border-brand-400'
                      }`}
                    >
                      {scale}
                    </button>
                  ))}
                </div>
                <div className="text-[10px] text-clinical-400 mt-1">
                  {simAvpu === 'A' ? '✓ Alert' : simAvpu === 'V' ? '⚠️ Responds to Voice' : simAvpu === 'P' ? '🚨 Responds to Pain' : '🚨 Unresponsive'}
                </div>
              </div>
            </div>

            {/* Column 2: Cardiopulmonary Vitals */}
            <div className="space-y-4">
              <label className="block text-xs font-black uppercase tracking-wider text-clinical-500">
                Cardiopulmonary Vitals
              </label>

              {/* Heart Rate */}
              <div>
                <div className="flex items-center justify-between text-xs font-bold text-clinical-700 dark:text-clinical-300 mb-1">
                  <span>Heart Rate</span>
                  <span className="font-mono text-rose-600 font-black">{simHr} bpm</span>
                </div>
                <input
                  type="range"
                  min="30"
                  max="190"
                  value={simHr}
                  onChange={(e) => setSimHr(Number(e.target.value))}
                  className="w-full accent-rose-500 h-1.5 bg-clinical-200 dark:bg-clinical-800 rounded-lg cursor-pointer"
                />
                <div className="flex justify-between text-[10px] text-clinical-400 font-bold mt-1">
                  <span>30</span>
                  <span>60–100 (Normal)</span>
                  <span>190</span>
                </div>
              </div>

              {/* Respiratory Rate */}
              <div>
                <div className="flex items-center justify-between text-xs font-bold text-clinical-700 dark:text-clinical-300 mb-1">
                  <span>Resp. Rate</span>
                  <span className="font-mono text-sky-600 font-black">{simRr} /min</span>
                </div>
                <input
                  type="range"
                  min="8"
                  max="55"
                  value={simRr}
                  onChange={(e) => setSimRr(Number(e.target.value))}
                  className="w-full accent-sky-500 h-1.5 bg-clinical-200 dark:bg-clinical-800 rounded-lg cursor-pointer"
                />
                <div className="flex justify-between text-[10px] text-clinical-400 font-bold mt-1">
                  <span>8</span>
                  <span>12–20 (Normal)</span>
                  <span>55</span>
                </div>
              </div>

              {/* SpO2 */}
              <div>
                <div className="flex items-center justify-between text-xs font-bold text-clinical-700 dark:text-clinical-300 mb-1">
                  <span>Oxygen Saturation</span>
                  <span className={`font-mono font-black ${simSpo2 < 90 ? 'text-red-600' : 'text-teal-600'}`}>
                    {simSpo2}%
                  </span>
                </div>
                <input
                  type="range"
                  min="70"
                  max="100"
                  value={simSpo2}
                  onChange={(e) => setSimSpo2(Number(e.target.value))}
                  className="w-full accent-teal-500 h-1.5 bg-clinical-200 dark:bg-clinical-800 rounded-lg cursor-pointer"
                />
                <div className="flex justify-between text-[10px] text-clinical-400 font-bold mt-1">
                  <span>70% (Severe)</span>
                  <span>95–100% (Adequate)</span>
                </div>
              </div>
            </div>

            {/* Column 3: Hemodynamics & Temperature */}
            <div className="space-y-4">
              <label className="block text-xs font-black uppercase tracking-wider text-clinical-500">
                Hemodynamics & Temp
              </label>

              {/* Systolic BP */}
              <div>
                <div className="flex items-center justify-between text-xs font-bold text-clinical-700 dark:text-clinical-300 mb-1">
                  <span>Systolic BP</span>
                  <span className={`font-mono font-black ${simSbp < 90 ? 'text-red-600' : 'text-indigo-600'}`}>
                    {simSbp} mmHg
                  </span>
                </div>
                <input
                  type="range"
                  min="50"
                  max="230"
                  value={simSbp}
                  onChange={(e) => setSimSbp(Number(e.target.value))}
                  className="w-full accent-indigo-500 h-1.5 bg-clinical-200 dark:bg-clinical-800 rounded-lg cursor-pointer"
                />
                <div className="flex justify-between text-[10px] text-clinical-400 font-bold mt-1">
                  <span>50 (Shock)</span>
                  <span>90–120</span>
                  <span>230 (Crisis)</span>
                </div>
              </div>

              {/* Temperature */}
              <div>
                <div className="flex items-center justify-between text-xs font-bold text-clinical-700 dark:text-clinical-300 mb-1">
                  <span>Temperature</span>
                  <span className="font-mono text-amber-600 font-black">{Number(simTemp).toFixed(1)} °C</span>
                </div>
                <input
                  type="range"
                  min="34.0"
                  max="41.5"
                  step="0.1"
                  value={simTemp}
                  onChange={(e) => setSimTemp(Number(e.target.value))}
                  className="w-full accent-amber-500 h-1.5 bg-clinical-200 dark:bg-clinical-800 rounded-lg cursor-pointer"
                />
                <div className="flex justify-between text-[10px] text-clinical-400 font-bold mt-1">
                  <span>34°C (Hypothermia)</span>
                  <span>37°C</span>
                  <span>41.5°C (Hyperpyrexia)</span>
                </div>
              </div>

              {/* Supplemental O2 */}
              <div className="pt-2">
                <label className="flex items-center gap-3 cursor-pointer p-2.5 rounded-xl bg-white dark:bg-clinical-900 border border-clinical-200 dark:border-clinical-800">
                  <input
                    type="checkbox"
                    checked={simOxygen}
                    onChange={(e) => setSimOxygen(e.target.checked)}
                    className="w-4 h-4 rounded text-brand-600 focus:ring-0"
                  />
                  <span className="text-xs font-bold text-clinical-800 dark:text-slate-200">Supplemental O₂ Supplied</span>
                </label>
              </div>
            </div>
          </div>

          {/* SIMULATOR REAL-TIME AI OUTPUT DISPLAY */}
          {simResult && (
            <div className="space-y-4 pt-2">
              <div className="flex items-center justify-between">
                <span className="text-xs font-black uppercase tracking-wider text-clinical-500">
                  Simulated Clinical Decision Output:
                </span>
                <div className="flex items-center gap-2">
                  <span className="text-xs font-mono font-bold text-clinical-500">
                    EWS Score: <b className="text-brand-700 dark:text-brand-400 font-black text-sm">{simResult.triage.ews_score}</b>
                  </span>
                  <span className="text-xs font-mono font-bold text-clinical-500">
                    Confidence: <b className="text-emerald-600 font-black">{Math.round(simResult.triage.confidence * 100)}%</b>
                  </span>
                </div>
              </div>

              <AcuityBadge level={simResult.triage.acuity} size="lg" />

              {/* Next Action Box */}
              <div className="p-4 rounded-2xl bg-white dark:bg-clinical-900 border border-clinical-200 dark:border-clinical-800 shadow-xs space-y-2">
                <span className="text-[10px] font-black text-clinical-400 uppercase tracking-wider">Mandated Next Clinical Action</span>
                <div className="text-sm font-black text-clinical-900 dark:text-white flex items-start gap-2">
                  <ArrowRight className="w-4 h-4 text-brand-600 dark:text-brand-400 shrink-0 mt-0.5" />
                  <span>{simResult.triage.recommended_action}</span>
                </div>

                {simResult.high_risk_category && (
                  <div className="mt-2 text-xs font-bold text-amber-700 dark:text-amber-300 bg-amber-50 dark:bg-amber-950/60 p-2.5 rounded-xl border border-amber-200 dark:border-amber-500/40 flex items-center gap-2">
                    <AlertOctagon className="w-4 h-4 shrink-0" />
                    <span>Matched High-Risk Complaint: <b>{simResult.high_risk_category}</b> (Phrase: "{simResult.high_risk_phrase}") &rarr; Floor priority locked at Level 2.</span>
                  </div>
                )}

                {simResult.triage.red_flags && simResult.triage.red_flags.length > 0 && (
                  <div className="mt-2 p-2.5 rounded-xl bg-red-50 dark:bg-red-950/60 border border-red-200 dark:border-red-500/40 text-xs text-red-800 dark:text-red-300">
                    <b>Critical Red Flags:</b> {simResult.triage.red_flags.join(' · ')}
                  </div>
                )}

                <div className="pt-2 border-t border-clinical-100 dark:border-clinical-800 text-xs text-clinical-600 dark:text-clinical-400">
                  <b className="text-clinical-900 dark:text-white">Clinical Rationale:</b>
                  <ul className="mt-1 space-y-0.5 list-disc pl-4">
                    {simResult.triage.reasons.map((r, i) => (
                      <li key={i}>{r}</li>
                    ))}
                  </ul>
                </div>
              </div>
            </div>
          )}
        </div>
      ) : (

        /* PATIENT INTAKE WORKSTATION VIEW */
        <div className="grid grid-cols-1 lg:grid-cols-12 gap-6">
          {/* LEFT: Arriving Patients Selector (3 Cols) */}
          <div className="lg:col-span-3 space-y-3">
            <div className="card-surface p-3.5">
              <div className="relative">
                <Search className="w-3.5 h-3.5 text-clinical-400 absolute left-3 top-2.5" />
                <input
                  type="text"
                  placeholder="Search arrivals..."
                  value={searchTerm}
                  onChange={(e) => setSearchTerm(e.target.value)}
                  className="w-full bg-clinical-50 dark:bg-clinical-950 text-xs text-clinical-900 dark:text-white pl-8 pr-3 py-1.5 rounded-xl border border-clinical-200 dark:border-clinical-800 focus:border-brand-500 focus:outline-none"
                />
              </div>

              <div className="mt-3 space-y-1.5 max-h-[620px] overflow-y-auto pr-1">
                {filteredPatients.map((p) => {
                  const isSelected = patient && patient.patient_id === p.patient_id;
                  const cfg = ACUITY_CONFIG[p.triage.acuity];
                  return (
                    <button
                      key={p.patient_id}
                      onClick={() => {
                        onSelectPatient(p);
                        setOverrideAcuity(p.triage.acuity);
                        setOverrideStatus(null);
                      }}
                      className={`w-full text-left p-2.5 rounded-xl border transition-all flex items-center justify-between ${
                        isSelected
                          ? 'bg-brand-50/80 dark:bg-brand-950/40 border-brand-500 shadow-xs'
                          : 'bg-white dark:bg-clinical-950/50 border-clinical-200 dark:border-clinical-800/80 hover:bg-clinical-50 dark:hover:bg-clinical-900'
                      }`}
                    >
                      <div className="truncate mr-2">
                        <div className="flex items-center gap-1.5">
                          <span className="font-mono text-xs font-black text-brand-700 dark:text-brand-400">{p.patient_id}</span>
                          <span className="text-xs font-black text-clinical-900 dark:text-white truncate">{p.name}</span>
                          {p.is_overridden && (
                            <span className="w-1.5 h-1.5 rounded-full bg-amber-500" title="Overridden by clinician"></span>
                          )}
                        </div>
                        <div className="text-[11px] text-clinical-500 dark:text-clinical-400 truncate mt-0.5 font-medium">
                          {p.complaint}
                        </div>
                      </div>
                      <span className={`text-[10px] font-black px-2 py-0.5 rounded-full border ${cfg.badge}`}>
                        L{p.triage.acuity}
                      </span>
                    </button>
                  );
                })}
              </div>
            </div>
          </div>

          {/* CENTER: Patient Card & Measured Vitals (5 Cols) */}
          <div className="lg:col-span-5 space-y-4">
            {/* Patient Identity Header */}
            <div className="card-surface p-5 relative overflow-hidden">
              <div className="flex items-start justify-between">
                <div>
                  <div className="flex items-center gap-2">
                    <h2 className="text-xl font-black text-clinical-900 dark:text-white tracking-tight">{patient.name}</h2>
                    <span className="text-xs px-2 py-0.5 rounded-lg bg-clinical-100 dark:bg-clinical-800 text-brand-700 dark:text-brand-300 font-mono font-black border border-clinical-200 dark:border-clinical-700">
                      {patient.patient_id}
                    </span>
                    {isOverridden && (
                      <span className="px-2 py-0.5 rounded-full bg-amber-100 text-amber-800 dark:bg-amber-950 dark:text-amber-300 border border-amber-300 dark:border-amber-500/40 text-[10px] font-black uppercase">
                        Override Active
                      </span>
                    )}
                  </div>
                  <p className="text-xs text-clinical-500 mt-1 font-medium">
                    Age: <b className="text-clinical-900 dark:text-slate-200">{Math.round(patient.age)} years</b> · Category:{' '}
                    <b className="text-clinical-900 dark:text-slate-200 uppercase">{patient.age_band.replace('_', ' ')}</b>
                  </p>
                </div>
                <AcuityBadge level={patient.triage.acuity} size="sm" />
              </div>

              {/* Chief Complaint */}
              <div className="mt-4 pt-3 border-t border-clinical-200 dark:border-clinical-800">
                <span className="text-[10px] font-black text-clinical-400 uppercase tracking-wider">Chief Complaint</span>
                <div className="text-sm font-black text-brand-700 dark:text-brand-400 capitalize mt-0.5">
                  {patient.complaint}
                </div>
              </div>

              {/* Pediatric Mode Alert */}
              {isPeds && (
                <div className="mt-3 p-3 rounded-xl bg-blue-50 dark:bg-blue-950/40 border border-blue-200 dark:border-blue-500/30 text-xs text-blue-900 dark:text-blue-200 flex items-start gap-2.5">
                  <span className="text-base">🧒</span>
                  <div>
                    <b className="font-extrabold text-blue-800 dark:text-blue-300">Pediatric Vital Scaling Active</b>
                    <p className="text-[11px] text-blue-700 dark:text-slate-300 mt-0.5">
                      Vitals scored against age-calibrated reference intervals (Fleming / Lancet model).
                    </p>
                  </div>
                </div>
              )}

              {/* High Risk Complaint Alert */}
              {patient.high_risk_category && (
                <div className="mt-3 p-3 rounded-xl bg-amber-50 dark:bg-amber-950/40 border border-amber-200 dark:border-amber-500/40 text-xs text-amber-900 dark:text-amber-200 flex items-start gap-2.5">
                  <AlertOctagon className="w-4 h-4 text-amber-600 dark:text-amber-400 mt-0.5 shrink-0" />
                  <div>
                    <b className="font-extrabold text-amber-800 dark:text-amber-300">High-Risk Symptom Trigger: {patient.high_risk_category.replace('_', ' ')}</b>
                    <p className="text-[11px] text-amber-700 dark:text-slate-300 mt-0.5">
                      Matched keyword "{patient.high_risk_phrase}". Safety override establishes minimum priority at Level 2.
                    </p>
                  </div>
                </div>
              )}
            </div>

            {/* Vital Signs Grid with Live Editing capability */}
            <div className="card-surface p-5 space-y-3">
              <div className="flex items-center justify-between mb-2">
                <h3 className="text-xs font-black uppercase tracking-wider text-clinical-500 flex items-center gap-1.5">
                  <Heart className="w-3.5 h-3.5 text-rose-500" />
                  <span>Clinical Vital Telemetry</span>
                </h3>
                <button
                  onClick={() => setIsEditingVitals(!isEditingVitals)}
                  className="text-xs font-bold text-brand-600 dark:text-brand-400 hover:underline flex items-center gap-1"
                >
                  <Sliders className="w-3.5 h-3.5" />
                  <span>{isEditingVitals ? 'Done Editing' : 'Adjust Vitals Live'}</span>
                </button>
              </div>

              {isEditingVitals ? (
                /* Live Vital Adjustment Panel */
                <div className="p-4 rounded-xl bg-clinical-50 dark:bg-clinical-950 border border-brand-300 dark:border-brand-500/40 space-y-3">
                  <div className="text-xs font-black text-brand-700 dark:text-brand-400">
                    Live Vitals Editor (Recalculates AI in Real-Time):
                  </div>
                  <div className="grid grid-cols-2 sm:grid-cols-3 gap-3 text-xs">
                    <div>
                      <span className="font-bold text-clinical-600">Heart Rate (bpm)</span>
                      <input
                        type="number"
                        value={editHr}
                        onChange={(e) => setEditHr(e.target.value)}
                        className="w-full mt-1 bg-white dark:bg-clinical-900 border border-clinical-200 dark:border-clinical-800 rounded-lg px-2 py-1 font-mono font-bold"
                      />
                    </div>
                    <div>
                      <span className="font-bold text-clinical-600">Resp. Rate (/min)</span>
                      <input
                        type="number"
                        value={editRr}
                        onChange={(e) => setEditRr(e.target.value)}
                        className="w-full mt-1 bg-white dark:bg-clinical-900 border border-clinical-200 dark:border-clinical-800 rounded-lg px-2 py-1 font-mono font-bold"
                      />
                    </div>
                    <div>
                      <span className="font-bold text-clinical-600">SpO₂ (%)</span>
                      <input
                        type="number"
                        value={editSpo2}
                        onChange={(e) => setEditSpo2(e.target.value)}
                        className="w-full mt-1 bg-white dark:bg-clinical-900 border border-clinical-200 dark:border-clinical-800 rounded-lg px-2 py-1 font-mono font-bold"
                      />
                    </div>
                    <div>
                      <span className="font-bold text-clinical-600">Systolic BP (mmHg)</span>
                      <input
                        type="number"
                        value={editSbp}
                        onChange={(e) => setEditSbp(e.target.value)}
                        className="w-full mt-1 bg-white dark:bg-clinical-900 border border-clinical-200 dark:border-clinical-800 rounded-lg px-2 py-1 font-mono font-bold"
                      />
                    </div>
                    <div>
                      <span className="font-bold text-clinical-600">Temp (°C)</span>
                      <input
                        type="number"
                        step="0.1"
                        value={editTemp}
                        onChange={(e) => setEditTemp(e.target.value)}
                        className="w-full mt-1 bg-white dark:bg-clinical-900 border border-clinical-200 dark:border-clinical-800 rounded-lg px-2 py-1 font-mono font-bold"
                      />
                    </div>
                    <div>
                      <span className="font-bold text-clinical-600">AVPU</span>
                      <select
                        value={editAvpu}
                        onChange={(e) => setEditAvpu(e.target.value)}
                        className="w-full mt-1 bg-white dark:bg-clinical-900 border border-clinical-200 dark:border-clinical-800 rounded-lg px-2 py-1 font-bold"
                      >
                        <option value="A">Alert (A)</option>
                        <option value="V">Voice (V)</option>
                        <option value="P">Pain (P)</option>
                        <option value="U">Unresponsive (U)</option>
                      </select>
                    </div>
                  </div>
                  <div className="pt-2 flex justify-end">
                    <button
                      onClick={handleSaveVitals}
                      className="px-4 py-1.5 rounded-lg bg-brand-600 hover:bg-brand-500 text-white font-bold text-xs shadow-xs"
                    >
                      Save & Recalculate AI Output
                    </button>
                  </div>
                </div>
              ) : (
                <div className="grid grid-cols-2 sm:grid-cols-3 gap-2.5">
                  {/* Heart Rate */}
                  <div className="card-surface-subtle p-3">
                    <div className="flex items-center justify-between text-[11px] text-clinical-500 font-semibold">
                      <span>Heart Rate</span>
                      <Heart className="w-3 h-3 text-rose-500" />
                    </div>
                    <div className="text-lg font-mono font-black text-clinical-900 dark:text-white mt-1">
                      {v.hr ? `${Math.round(v.hr)}` : '—'}{' '}
                      <span className="text-[10px] font-medium text-clinical-400">bpm</span>
                    </div>
                    <div className="mt-2">
                      <ECGWaveform hr={v.hr} isCritical={v.hr >= 140 || v.hr < 45} isWarning={v.hr >= 100} />
                    </div>
                  </div>

                  {/* Respiratory Rate */}
                  <div className="card-surface-subtle p-3">
                    <div className="flex items-center justify-between text-[11px] text-clinical-500 font-semibold">
                      <span>Resp. Rate</span>
                      <Wind className="w-3 h-3 text-sky-500" />
                    </div>
                    <div className="text-lg font-mono font-black text-clinical-900 dark:text-white mt-1">
                      {v.rr ? `${Math.round(v.rr)}` : '—'}{' '}
                      <span className="text-[10px] font-medium text-clinical-400">/min</span>
                    </div>
                    <span className={`text-[10px] font-black ${v.rr >= 24 ? 'text-amber-600 dark:text-amber-400' : 'text-emerald-600 dark:text-emerald-400'}`}>
                      {v.rr >= 30 ? '🚨 Tachypnea' : v.rr >= 24 ? '⚠️ High' : '✓ Normal'}
                    </span>
                  </div>

                  {/* SpO2 */}
                  <div className="card-surface-subtle p-3">
                    <div className="flex items-center justify-between text-[11px] text-clinical-500 font-semibold">
                      <span>Oxygen Sat.</span>
                      <Droplets className="w-3 h-3 text-teal-500" />
                    </div>
                    <div className="text-lg font-mono font-black text-clinical-900 dark:text-white mt-1">
                      {v.spo2 ? `${Math.round(v.spo2)}` : '—'}{' '}
                      <span className="text-[10px] font-medium text-clinical-400">%</span>
                    </div>
                    <span className={`text-[10px] font-black ${v.spo2 < 90 ? 'text-red-600 dark:text-red-400' : v.spo2 < 94 ? 'text-amber-600 dark:text-amber-400' : 'text-emerald-600 dark:text-emerald-400'}`}>
                      {v.spo2 < 90 ? '🚨 Critical Hypoxia' : v.spo2 < 94 ? '⚠️ Low' : '✓ Adequate'}
                    </span>
                  </div>

                  {/* Systolic BP */}
                  <div className="card-surface-subtle p-3">
                    <div className="flex items-center justify-between text-[11px] text-clinical-500 font-semibold">
                      <span>Blood Pressure</span>
                      <Gauge className="w-3 h-3 text-indigo-500" />
                    </div>
                    <div className="text-lg font-mono font-black text-clinical-900 dark:text-white mt-1">
                      {v.sbp ? `${Math.round(v.sbp)}` : '—'}{' '}
                      <span className="text-[10px] font-medium text-clinical-400">mmHg</span>
                    </div>
                    <span className={`text-[10px] font-black ${v.sbp < 90 ? 'text-red-600 dark:text-red-400' : 'text-clinical-500'}`}>
                      {v.sbp < 90 ? '🚨 Hypotensive' : 'Systolic'}
                    </span>
                  </div>

                  {/* Temperature */}
                  <div className="card-surface-subtle p-3">
                    <div className="flex items-center justify-between text-[11px] text-clinical-500 font-semibold">
                      <span>Temperature</span>
                      <Thermometer className="w-3 h-3 text-amber-500" />
                    </div>
                    <div className="text-lg font-mono font-black text-clinical-900 dark:text-white mt-1">
                      {v.temp ? `${v.temp.toFixed(1)}` : '—'}{' '}
                      <span className="text-[10px] font-medium text-clinical-400">°C</span>
                    </div>
                    <span className={`text-[10px] font-black ${v.temp >= 38.5 ? 'text-amber-600 dark:text-amber-400' : 'text-clinical-500'}`}>
                      {v.temp >= 38.5 ? '⚠️ Febrile' : 'Normothermic'}
                    </span>
                  </div>

                  {/* AVPU */}
                  <div className="card-surface-subtle p-3">
                    <div className="flex items-center justify-between text-[11px] text-clinical-500 font-semibold">
                      <span>Consciousness</span>
                      <Brain className="w-3 h-3 text-purple-500" />
                    </div>
                    <div className="text-lg font-mono font-black text-clinical-900 dark:text-white mt-1">
                      {v.avpu || 'A'}{' '}
                      <span className="text-[10px] font-medium text-clinical-400">(AVPU)</span>
                    </div>
                    <span className={`text-[10px] font-black ${v.avpu && v.avpu !== 'A' ? 'text-red-600 dark:text-red-400' : 'text-emerald-600 dark:text-emerald-400'}`}>
                      {v.avpu && v.avpu !== 'A' ? '🚨 Altered' : '✓ Alert'}
                    </span>
                  </div>
                </div>
              )}
            </div>

            {/* Historical EHR Baseline */}
            <div className="card-surface p-4 text-xs space-y-2">
              <div className="flex items-center justify-between text-clinical-800 dark:text-clinical-200 font-bold">
                <span className="flex items-center gap-1.5">
                  <History className="w-4 h-4 text-brand-600 dark:text-brand-400" />
                  Prior Institutional EHR History
                </span>
                {patient.has_history ? (
                  <span className="text-brand-700 dark:text-brand-400 text-[11px] font-bold">Returning Patient</span>
                ) : (
                  <span className="text-clinical-400 text-[11px]">First-Time Patient</span>
                )}
              </div>
              {patient.history ? (
                <div className="p-3 rounded-xl bg-brand-50/60 dark:bg-brand-950/20 border border-brand-200 dark:border-brand-500/20 text-clinical-800 dark:text-clinical-300 space-y-1">
                  <div>
                    Baseline HR: <b>{patient.history.baseline_hr} bpm</b> · Baseline SBP: <b>{patient.history.baseline_sbp} mmHg</b>
                  </div>
                  <div>
                    Documented Chronic: <b>{patient.history.chronic_conditions.join(', ') || 'None on file'}</b>
                  </div>
                  <div className="text-[11px] text-clinical-500 dark:text-clinical-400">
                    Last Encounter: {patient.history.last_visit_date} (Assigned Level {patient.history.last_visit_acuity})
                  </div>
                </div>
              ) : (
                <div className="text-clinical-500 text-[11px]">
                  No prior institutional records. Evaluated strictly against standard clinical bounds.
                </div>
              )}
            </div>
          </div>

          {/* RIGHT: AI Recommendation & Real-Time Override (4 Cols) */}
          <div className="lg:col-span-4 space-y-4">
            <div className="space-y-2">
              <div className="flex items-center justify-between">
                <div className="text-xs font-black uppercase tracking-wider text-clinical-500 flex items-center gap-1.5">
                  <CheckCircle2 className="w-3.5 h-3.5 text-brand-600 dark:text-brand-400" />
                  <span>Current Assigned Level</span>
                </div>
                {isOverridden && (
                  <span className="text-[10px] font-bold text-amber-600 dark:text-amber-400 bg-amber-50 dark:bg-amber-950 px-2 py-0.5 rounded-full border border-amber-300">
                    AI Suggested: L{t.model_acuity || t.acuity}
                  </span>
                )}
              </div>
              <AcuityBadge level={t.acuity} size="lg" />
            </div>

            {/* Recommended Next Action */}
            <div className="card-surface p-4">
              <span className="text-[10px] font-black text-clinical-400 uppercase tracking-wider">Mandated Clinical Action</span>
              <div className="text-sm font-black text-clinical-900 dark:text-white mt-1 flex items-start gap-2">
                <ArrowRight className="w-4 h-4 text-brand-600 dark:text-brand-400 shrink-0 mt-0.5" />
                <span>{t.recommended_action}</span>
              </div>
            </div>

            {/* Red Flags Alert */}
            {t.red_flags && t.red_flags.length > 0 && (
              <div className="p-4 rounded-2xl bg-red-50 dark:bg-red-950/40 border border-red-200 dark:border-red-500/40 text-red-900 dark:text-red-200">
                <div className="flex items-center gap-2 font-black text-xs text-red-700 dark:text-red-400 mb-2">
                  <AlertOctagon className="w-4 h-4" />
                  <span>Red-Flag Safety Escalation ({t.red_flags.length})</span>
                </div>
                <ul className="text-xs space-y-1 pl-4 list-disc marker:text-red-500 text-red-800 dark:text-slate-300 font-medium">
                  {t.red_flags.map((flag, idx) => (
                    <li key={idx}>{flag}</li>
                  ))}
                </ul>
              </div>
            )}

            {/* Assessment Confidence Gauge */}
            <div className="card-surface p-4 space-y-2">
              <div className="flex items-center justify-between text-xs font-bold">
                <span className="text-clinical-700 dark:text-slate-300">Confidence Metric</span>
                <span className={`font-mono font-black ${
                  t.confidence_label === 'High' ? 'text-emerald-600 dark:text-emerald-400' :
                  t.confidence_label === 'Moderate' ? 'text-amber-600 dark:text-amber-400' : 'text-red-600 dark:text-red-400'
                }`}>
                  {Math.round(t.confidence * 100)}% · {t.confidence_label}
                </span>
              </div>
              <div className="h-2 rounded-full bg-clinical-100 dark:bg-clinical-950 overflow-hidden border border-clinical-200 dark:border-clinical-800">
                <div 
                  className={`h-full rounded-full transition-all duration-500 ${
                    t.confidence_label === 'High' ? 'bg-emerald-500' :
                    t.confidence_label === 'Moderate' ? 'bg-amber-500' : 'bg-red-500'
                  }`}
                  style={{ width: `${Math.round(t.confidence * 100)}%` }}
                />
              </div>
              {t.confidence_label === 'Low' && (
                <div className="text-[11px] font-bold text-amber-800 dark:text-amber-300 bg-amber-50 dark:bg-amber-950/40 p-2 rounded-lg border border-amber-200 dark:border-amber-500/30">
                  ⚠️ Uncertainty Escalation: Priority escalated due to incomplete vitals.
                </div>
              )}
            </div>

            {/* Decision Rationale */}
            <div className="card-surface p-4 space-y-2">
              <div className="text-xs font-black text-clinical-800 dark:text-slate-200">Clinical Rationale</div>
              <ul className="text-[11px] text-clinical-600 dark:text-clinical-400 space-y-1 pl-4 list-disc font-medium">
                {t.reasons.map((r, i) => (
                  <li key={i} className="leading-relaxed">{r}</li>
                ))}
              </ul>
            </div>

            {/* REAL-TIME CLINICIAN CONFIRMATION & OVERRIDE WORKBENCH */}
            <div className="card-surface p-5 space-y-4 border-brand-300 dark:border-brand-500/40 shadow-sm">
              <div className="flex items-center justify-between pb-2 border-b border-clinical-200 dark:border-clinical-800">
                <div className="flex items-center gap-2">
                  <Shield className="w-4 h-4 text-brand-600 dark:text-brand-400" />
                  <span className="text-xs font-black text-clinical-900 dark:text-white uppercase tracking-wider">
                    Clinician Confirmation & Override
                  </span>
                </div>
                <span className="text-[10px] text-brand-700 dark:text-brand-400 font-mono font-bold bg-brand-50 dark:bg-brand-950 px-2 py-0.5 rounded-full border border-brand-200 dark:border-brand-500/30">
                  Real-Time Active
                </span>
              </div>

              {overrideStatus && (
                <div className="p-3 rounded-xl bg-emerald-50 dark:bg-emerald-950/60 border border-emerald-300 dark:border-emerald-500/40 text-emerald-800 dark:text-emerald-200 text-xs font-bold flex items-start gap-2 animate-pulse">
                  <Check className="w-4 h-4 text-emerald-600 mt-0.5 shrink-0" />
                  <span>{overrideStatus}</span>
                </div>
              )}

              {/* 1-Click Interactive Level Selector */}
              <div>
                <label className="text-[11px] font-black text-clinical-600 dark:text-clinical-400 uppercase tracking-wider block mb-2">
                  Select Assigned ESI Acuity (Updates Instantly):
                </label>
                <div className="grid grid-cols-5 gap-1.5">
                  {[1, 2, 3, 4, 5].map((lvl) => {
                    const isCurrent = t.acuity === lvl;
                    const cfg = ACUITY_CONFIG[lvl];
                    return (
                      <button
                        key={lvl}
                        type="button"
                        onClick={() => triggerRealtimeOverride(lvl)}
                        className={`py-2 px-1 rounded-xl text-center font-black transition-all flex flex-col items-center justify-center border ${
                          isCurrent
                            ? 'bg-brand-600 text-white border-brand-700 shadow-md ring-2 ring-brand-400 scale-105'
                            : 'bg-clinical-50 dark:bg-clinical-950 text-clinical-700 dark:text-clinical-300 border-clinical-200 dark:border-clinical-800 hover:border-brand-400 hover:bg-clinical-100'
                        }`}
                      >
                        <span className="text-sm font-mono">L{lvl}</span>
                        <span className="text-[9px] font-semibold truncate w-full mt-0.5">
                          {cfg.label.split(' ')[0]}
                        </span>
                      </button>
                    );
                  })}
                </div>
              </div>

              {/* Quick Reason Chips */}
              <div>
                <span className="text-[10px] font-black text-clinical-500 uppercase tracking-wider block mb-1.5">
                  1-Click Quick Justifications:
                </span>
                <div className="flex flex-wrap gap-1.5">
                  {quickReasons.map((chip, idx) => (
                    <button
                      key={idx}
                      type="button"
                      onClick={() => handleQuickReasonClick(chip)}
                      className="px-2.5 py-1 rounded-lg text-[10px] font-bold bg-clinical-100 dark:bg-clinical-900 text-clinical-700 dark:text-clinical-300 hover:bg-brand-100 dark:hover:bg-brand-950 hover:text-brand-700 border border-clinical-200 dark:border-clinical-800 transition-colors"
                    >
                      + {chip}
                    </button>
                  ))}
                </div>
              </div>

              {/* Custom Justification and Clinician ID */}
              <div className="space-y-2 pt-1">
                <div>
                  <label className="text-[11px] font-bold text-clinical-600 dark:text-clinical-400">
                    Clinical Justification (Press Enter or Commit):
                  </label>
                  <input
                    type="text"
                    placeholder="Enter clinical rationale..."
                    value={overrideReason}
                    onChange={(e) => setOverrideReason(e.target.value)}
                    onKeyDown={(e) => {
                      if (e.key === 'Enter') {
                        e.preventDefault();
                        triggerRealtimeOverride(overrideAcuity, overrideReason);
                      }
                    }}
                    className="w-full mt-1 bg-clinical-50 dark:bg-clinical-950 border border-clinical-200 dark:border-clinical-800 rounded-xl px-3 py-2 text-xs text-clinical-900 dark:text-white focus:border-brand-500 focus:outline-none"
                  />
                </div>

                <div className="flex items-center gap-2 pt-1">
                  <div className="relative">
                    <input
                      type="text"
                      value={clinicianId}
                      onChange={(e) => setClinicianId(e.target.value)}
                      className="w-24 bg-clinical-50 dark:bg-clinical-950 border border-clinical-200 dark:border-clinical-800 rounded-xl px-2 py-2 text-xs text-clinical-700 dark:text-slate-300 font-mono font-bold text-center"
                      title="Clinician ID"
                    />
                  </div>
                  <button
                    type="button"
                    onClick={() => triggerRealtimeOverride(overrideAcuity, overrideReason)}
                    className="flex-1 py-2 px-3 rounded-xl bg-brand-600 hover:bg-brand-500 text-white text-xs font-black transition-colors shadow-xs flex items-center justify-center gap-1.5"
                  >
                    <Check className="w-4 h-4" />
                    <span>Commit Override Now</span>
                  </button>
                </div>
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
