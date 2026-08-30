import React, { useState } from 'react';
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
  Search
} from 'lucide-react';
import AcuityBadge, { ACUITY_CONFIG } from './AcuityBadge';
import ECGWaveform from './ECGWaveform';

export default function TriageNurseView({ 
  patients = [], 
  selectedPatient, 
  onSelectPatient, 
  onRecordOverride 
}) {
  const [activeTab, setActiveTab] = useState('patient');
  const [searchTerm, setSearchTerm] = useState('');
  
  // Override form state
  const [overrideAcuity, setOverrideAcuity] = useState(3);
  const [overrideReason, setOverrideReason] = useState('');
  const [clinicianId, setClinicianId] = useState('RN-1042');
  const [overrideStatus, setOverrideStatus] = useState(null);

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

  const patient = selectedPatient || patients[0];

  const handleOverrideSubmit = async (e) => {
    e.preventDefault();
    if (!patient) return;
    if (!overrideReason.trim()) {
      alert('A clinical justification is required for an override.');
      return;
    }
    const res = await onRecordOverride({
      patient_id: patient.patient_id,
      from_acuity: patient.triage.acuity,
      to_acuity: Number(overrideAcuity),
      reason: overrideReason,
      clinician: clinicianId,
    });
    if (res && res.success) {
      setOverrideStatus(`✓ Override recorded: Level ${patient.triage.acuity} → Level ${overrideAcuity} by ${clinicianId}. Authenticated into SHA-256 audit log.`);
      setOverrideReason('');
    }
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

  if (!patient && patients.length === 0) {
    return <div className="p-8 text-center text-clinical-400">Loading emergency patients...</div>;
  }

  const v = patient ? patient.vitals : {};
  const t = patient ? patient.triage : {};
  const isPeds = patient ? patient.is_pediatric : false;

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
        <div className="card-surface p-6">
          <div className="flex items-center justify-between mb-6 pb-4 border-b border-clinical-200 dark:border-clinical-800">
            <div>
              <h2 className="text-lg font-black text-clinical-900 dark:text-white flex items-center gap-2">
                <Sparkles className="w-5 h-5 text-brand-600 dark:text-brand-400" />
                <span>Instant Clinical Triage Calculator</span>
              </h2>
              <p className="text-xs text-clinical-500 dark:text-clinical-400 font-medium">
                Test custom vital combinations, pediatric ranges, and symptom phrases through the clinical decision engine.
              </p>
            </div>
            <button
              onClick={handleRunSimulator}
              disabled={simLoading}
              className="px-5 py-2.5 rounded-xl bg-brand-600 hover:bg-brand-500 text-white text-xs font-black shadow-sm transition-all flex items-center gap-2"
            >
              {simLoading ? 'Scoring...' : 'Compute AI Recommendation'}
              <ArrowRight className="w-4 h-4" />
            </button>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
            <div className="space-y-4">
              <label className="block text-xs font-black uppercase tracking-wider text-clinical-500">
                Demographics & Mental Status
              </label>
              <div>
                <span className="text-xs font-bold text-clinical-700 dark:text-clinical-300">Age (years)</span>
                <input
                  type="number"
                  value={simAge}
                  onChange={(e) => setSimAge(e.target.value)}
                  className="w-full mt-1 bg-clinical-50 dark:bg-clinical-950 border border-clinical-200 dark:border-clinical-800 rounded-xl px-3 py-2 text-sm text-clinical-900 dark:text-white focus:border-brand-500 focus:outline-none"
                />
              </div>
              <div>
                <span className="text-xs font-bold text-clinical-700 dark:text-clinical-300">Chief Complaint</span>
                <input
                  type="text"
                  value={simComplaint}
                  onChange={(e) => setSimComplaint(e.target.value)}
                  className="w-full mt-1 bg-clinical-50 dark:bg-clinical-950 border border-clinical-200 dark:border-clinical-800 rounded-xl px-3 py-2 text-sm text-clinical-900 dark:text-white focus:border-brand-500 focus:outline-none"
                />
              </div>
              <div>
                <span className="text-xs font-bold text-clinical-700 dark:text-clinical-300">AVPU Scale</span>
                <select
                  value={simAvpu}
                  onChange={(e) => setSimAvpu(e.target.value)}
                  className="w-full mt-1 bg-clinical-50 dark:bg-clinical-950 border border-clinical-200 dark:border-clinical-800 rounded-xl px-3 py-2 text-sm text-clinical-900 dark:text-white focus:border-brand-500 focus:outline-none"
                >
                  <option value="A">Alert (A)</option>
                  <option value="V">Responds to Voice (V)</option>
                  <option value="P">Responds to Pain (P)</option>
                  <option value="U">Unresponsive (U)</option>
                </select>
              </div>
            </div>

            <div className="space-y-4">
              <label className="block text-xs font-black uppercase tracking-wider text-clinical-500">
                Cardiopulmonary Vitals
              </label>
              <div>
                <span className="text-xs font-bold text-clinical-700 dark:text-clinical-300">Heart Rate (bpm)</span>
                <input
                  type="number"
                  value={simHr}
                  onChange={(e) => setSimHr(e.target.value)}
                  className="w-full mt-1 bg-clinical-50 dark:bg-clinical-950 border border-clinical-200 dark:border-clinical-800 rounded-xl px-3 py-2 text-sm text-clinical-900 dark:text-white focus:border-brand-500 focus:outline-none"
                />
              </div>
              <div>
                <span className="text-xs font-bold text-clinical-700 dark:text-clinical-300">Respiratory Rate (/min)</span>
                <input
                  type="number"
                  value={simRr}
                  onChange={(e) => setSimRr(e.target.value)}
                  className="w-full mt-1 bg-clinical-50 dark:bg-clinical-950 border border-clinical-200 dark:border-clinical-800 rounded-xl px-3 py-2 text-sm text-clinical-900 dark:text-white focus:border-brand-500 focus:outline-none"
                />
              </div>
              <div>
                <span className="text-xs font-bold text-clinical-700 dark:text-clinical-300">SpO₂ (%)</span>
                <input
                  type="number"
                  value={simSpo2}
                  onChange={(e) => setSimSpo2(e.target.value)}
                  className="w-full mt-1 bg-clinical-50 dark:bg-clinical-950 border border-clinical-200 dark:border-clinical-800 rounded-xl px-3 py-2 text-sm text-clinical-900 dark:text-white focus:border-brand-500 focus:outline-none"
                />
              </div>
            </div>

            <div className="space-y-4">
              <label className="block text-xs font-black uppercase tracking-wider text-clinical-500">
                Hemodynamics & Temp
              </label>
              <div>
                <span className="text-xs font-bold text-clinical-700 dark:text-clinical-300">Systolic BP (mmHg)</span>
                <input
                  type="number"
                  value={simSbp}
                  onChange={(e) => setSimSbp(e.target.value)}
                  className="w-full mt-1 bg-clinical-50 dark:bg-clinical-950 border border-clinical-200 dark:border-clinical-800 rounded-xl px-3 py-2 text-sm text-clinical-900 dark:text-white focus:border-brand-500 focus:outline-none"
                />
              </div>
              <div>
                <span className="text-xs font-bold text-clinical-700 dark:text-clinical-300">Temperature (°C)</span>
                <input
                  type="number"
                  step="0.1"
                  value={simTemp}
                  onChange={(e) => setSimTemp(e.target.value)}
                  className="w-full mt-1 bg-clinical-50 dark:bg-clinical-950 border border-clinical-200 dark:border-clinical-800 rounded-xl px-3 py-2 text-sm text-clinical-900 dark:text-white focus:border-brand-500 focus:outline-none"
                />
              </div>
              <div className="pt-5">
                <label className="flex items-center gap-3 cursor-pointer">
                  <input
                    type="checkbox"
                    checked={simOxygen}
                    onChange={(e) => setSimOxygen(e.target.checked)}
                    className="w-4 h-4 rounded text-brand-600 focus:ring-0"
                  />
                  <span className="text-xs font-bold text-clinical-700 dark:text-clinical-300">Receiving Supplemental O₂</span>
                </label>
              </div>
            </div>
          </div>

          {simResult && (
            <div className="mt-8 pt-6 border-t border-clinical-200 dark:border-clinical-800">
              <AcuityBadge level={simResult.triage.acuity} size="lg" />
              <div className="mt-4 p-4 rounded-2xl bg-clinical-50 dark:bg-clinical-950 border border-clinical-200 dark:border-clinical-800 text-sm">
                <div className="font-extrabold text-brand-700 dark:text-brand-400 mb-1">Recommended Next Action:</div>
                <div className="text-clinical-800 dark:text-clinical-200 font-semibold">{simResult.triage.recommended_action}</div>
                <div className="mt-2 text-xs text-clinical-500">
                  <b>Reasons:</b> {simResult.triage.reasons.join(' · ')}
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

            {/* Vital Signs Grid */}
            <div className="card-surface p-5 space-y-3">
              <div className="flex items-center justify-between mb-2">
                <h3 className="text-xs font-black uppercase tracking-wider text-clinical-500 flex items-center gap-1.5">
                  <Heart className="w-3.5 h-3.5 text-rose-500" />
                  <span>Clinical Vital Telemetry</span>
                </h3>
                <span className="text-[10px] text-clinical-400 font-mono font-bold">6 Observed</span>
              </div>

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

          {/* RIGHT: AI Recommendation & Override (4 Cols) */}
          <div className="lg:col-span-4 space-y-4">
            <div className="space-y-2">
              <div className="text-xs font-black uppercase tracking-wider text-clinical-500 flex items-center gap-1.5">
                <CheckCircle2 className="w-3.5 h-3.5 text-brand-600 dark:text-brand-400" />
                <span>Decision Support Output</span>
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

            {/* Clinician Override Form */}
            <div className="card-surface p-4 space-y-3">
              <div className="flex items-center justify-between">
                <span className="text-xs font-black text-clinical-900 dark:text-white flex items-center gap-1.5">
                  <Shield className="w-3.5 h-3.5 text-brand-600 dark:text-brand-400" />
                  Clinician Confirmation & Override
                </span>
                <span className="text-[10px] text-clinical-400 font-mono font-bold">Encrypted Audit</span>
              </div>

              {overrideStatus && (
                <div className="p-2.5 rounded-xl bg-emerald-50 dark:bg-emerald-950/40 border border-emerald-200 dark:border-emerald-500/40 text-emerald-800 dark:text-emerald-300 text-xs font-bold">
                  {overrideStatus}
                </div>
              )}

              <form onSubmit={handleOverrideSubmit} className="space-y-2.5">
                <div>
                  <label className="text-[11px] font-bold text-clinical-600 dark:text-clinical-400">Assigned ESI Level</label>
                  <select
                    value={overrideAcuity}
                    onChange={(e) => setOverrideAcuity(e.target.value)}
                    className="w-full mt-1 bg-clinical-50 dark:bg-clinical-950 border border-clinical-200 dark:border-clinical-800 rounded-xl px-2.5 py-1.5 text-xs text-clinical-900 dark:text-white focus:border-brand-500 focus:outline-none font-bold"
                  >
                    <option value={1}>Level 1 — Resuscitation</option>
                    <option value={2}>Level 2 — Emergent</option>
                    <option value={3}>Level 3 — Urgent</option>
                    <option value={4}>Level 4 — Less Urgent</option>
                    <option value={5}>Level 5 — Non-Urgent</option>
                  </select>
                </div>

                <div>
                  <label className="text-[11px] font-bold text-clinical-600 dark:text-clinical-400">Clinical Justification for Override</label>
                  <input
                    type="text"
                    placeholder="Mandatory reason for override..."
                    value={overrideReason}
                    onChange={(e) => setOverrideReason(e.target.value)}
                    className="w-full mt-1 bg-clinical-50 dark:bg-clinical-950 border border-clinical-200 dark:border-clinical-800 rounded-xl px-2.5 py-1.5 text-xs text-clinical-900 dark:text-white focus:border-brand-500 focus:outline-none"
                  />
                </div>

                <div className="flex items-center gap-2 pt-1">
                  <input
                    type="text"
                    value={clinicianId}
                    onChange={(e) => setClinicianId(e.target.value)}
                    className="w-24 bg-clinical-50 dark:bg-clinical-950 border border-clinical-200 dark:border-clinical-800 rounded-xl px-2 py-1.5 text-xs text-clinical-700 dark:text-slate-300 font-mono font-bold text-center"
                  />
                  <button
                    type="submit"
                    className="flex-1 py-1.5 px-3 rounded-xl bg-brand-600 hover:bg-brand-500 text-white text-xs font-black transition-colors shadow-xs"
                  >
                    Commit Decision
                  </button>
                </div>
              </form>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
