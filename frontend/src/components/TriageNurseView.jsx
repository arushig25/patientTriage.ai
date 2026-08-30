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
  const [activeTab, setActiveTab] = useState('patient'); // 'patient' | 'simulator'
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
      setOverrideStatus(`✓ Override committed: Level ${patient.triage.acuity} → Level ${overrideAcuity} by ${clinicianId}. Recorded in SHA-256 audit log.`);
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
    return <div className="p-8 text-center text-slate-400">Loading emergency patients...</div>;
  }

  const v = patient ? patient.vitals : {};
  const t = patient ? patient.triage : {};
  const isPeds = patient ? patient.is_pediatric : false;

  return (
    <div className="space-y-6">
      {/* Sub-navigation tabs */}
      <div className="flex items-center justify-between border-b border-slate-800 pb-3">
        <div className="flex items-center gap-3">
          <button
            onClick={() => setActiveTab('patient')}
            className={`px-4 py-2 rounded-lg text-xs font-bold transition-all flex items-center gap-2 ${
              activeTab === 'patient'
                ? 'bg-teal-500 text-white shadow-lg shadow-teal-500/20'
                : 'text-slate-400 hover:text-slate-200 hover:bg-slate-800/60'
            }`}
          >
            <UserCheck className="w-4 h-4" />
            <span>Arriving Patient Intake</span>
          </button>
          <button
            onClick={() => setActiveTab('simulator')}
            className={`px-4 py-2 rounded-lg text-xs font-bold transition-all flex items-center gap-2 ${
              activeTab === 'simulator'
                ? 'bg-teal-500 text-white shadow-lg shadow-teal-500/20'
                : 'text-slate-400 hover:text-slate-200 hover:bg-slate-800/60'
            }`}
          >
            <Sparkles className="w-4 h-4 text-amber-300" />
            <span>Live Triage Simulator</span>
          </button>
        </div>

        {activeTab === 'patient' && (
          <div className="text-xs text-slate-400 font-medium">
            Active ED Queue: <b className="text-white">{patients.length}</b> arrivals
          </div>
        )}
      </div>

      {activeTab === 'simulator' ? (
        /* LIVE TRIAGE SIMULATOR VIEW */
        <div className="glass-panel p-6 rounded-2xl border border-slate-800">
          <div className="flex items-center justify-between mb-6 pb-4 border-b border-slate-800">
            <div>
              <h2 className="text-lg font-bold text-white flex items-center gap-2">
                <Sparkles className="w-5 h-5 text-teal-400" />
                <span>Instant Clinical Triage Calculator</span>
              </h2>
              <p className="text-xs text-slate-400">
                Test custom vital combinations, pediatric ranges, and symptom phrases through the clinical decision engine.
              </p>
            </div>
            <button
              onClick={handleRunSimulator}
              disabled={simLoading}
              className="px-5 py-2.5 rounded-xl bg-teal-500 hover:bg-teal-400 text-white text-xs font-extrabold shadow-lg shadow-teal-500/25 transition-all flex items-center gap-2"
            >
              {simLoading ? 'Scoring...' : 'Compute AI Recommendation'}
              <ArrowRight className="w-4 h-4" />
            </button>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
            <div className="space-y-4">
              <label className="block text-xs font-bold uppercase tracking-wider text-slate-400">
                Demographics & Mental Status
              </label>
              <div>
                <span className="text-xs text-slate-300">Age (years)</span>
                <input
                  type="number"
                  value={simAge}
                  onChange={(e) => setSimAge(e.target.value)}
                  className="w-full mt-1 bg-slate-900 border border-slate-700 rounded-lg px-3 py-2 text-sm text-white focus:border-teal-400 focus:outline-none"
                />
              </div>
              <div>
                <span className="text-xs text-slate-300">Chief Complaint</span>
                <input
                  type="text"
                  value={simComplaint}
                  onChange={(e) => setSimComplaint(e.target.value)}
                  className="w-full mt-1 bg-slate-900 border border-slate-700 rounded-lg px-3 py-2 text-sm text-white focus:border-teal-400 focus:outline-none"
                />
              </div>
              <div>
                <span className="text-xs text-slate-300">AVPU Consciousness Scale</span>
                <select
                  value={simAvpu}
                  onChange={(e) => setSimAvpu(e.target.value)}
                  className="w-full mt-1 bg-slate-900 border border-slate-700 rounded-lg px-3 py-2 text-sm text-white focus:border-teal-400 focus:outline-none"
                >
                  <option value="A">Alert (A)</option>
                  <option value="V">Responds to Voice (V)</option>
                  <option value="P">Responds to Pain (P)</option>
                  <option value="U">Unresponsive (U)</option>
                </select>
              </div>
            </div>

            <div className="space-y-4">
              <label className="block text-xs font-bold uppercase tracking-wider text-slate-400">
                Cardiopulmonary Vitals
              </label>
              <div>
                <span className="text-xs text-slate-300">Heart Rate (bpm)</span>
                <input
                  type="number"
                  value={simHr}
                  onChange={(e) => setSimHr(e.target.value)}
                  className="w-full mt-1 bg-slate-900 border border-slate-700 rounded-lg px-3 py-2 text-sm text-white focus:border-teal-400 focus:outline-none"
                />
              </div>
              <div>
                <span className="text-xs text-slate-300">Respiratory Rate (/min)</span>
                <input
                  type="number"
                  value={simRr}
                  onChange={(e) => setSimRr(e.target.value)}
                  className="w-full mt-1 bg-slate-900 border border-slate-700 rounded-lg px-3 py-2 text-sm text-white focus:border-teal-400 focus:outline-none"
                />
              </div>
              <div>
                <span className="text-xs text-slate-300">SpO₂ (%)</span>
                <input
                  type="number"
                  value={simSpo2}
                  onChange={(e) => setSimSpo2(e.target.value)}
                  className="w-full mt-1 bg-slate-900 border border-slate-700 rounded-lg px-3 py-2 text-sm text-white focus:border-teal-400 focus:outline-none"
                />
              </div>
            </div>

            <div className="space-y-4">
              <label className="block text-xs font-bold uppercase tracking-wider text-slate-400">
                Hemodynamics & Temp
              </label>
              <div>
                <span className="text-xs text-slate-300">Systolic Blood Pressure (mmHg)</span>
                <input
                  type="number"
                  value={simSbp}
                  onChange={(e) => setSimSbp(e.target.value)}
                  className="w-full mt-1 bg-slate-900 border border-slate-700 rounded-lg px-3 py-2 text-sm text-white focus:border-teal-400 focus:outline-none"
                />
              </div>
              <div>
                <span className="text-xs text-slate-300">Temperature (°C)</span>
                <input
                  type="number"
                  step="0.1"
                  value={simTemp}
                  onChange={(e) => setSimTemp(e.target.value)}
                  className="w-full mt-1 bg-slate-900 border border-slate-700 rounded-lg px-3 py-2 text-sm text-white focus:border-teal-400 focus:outline-none"
                />
              </div>
              <div className="pt-5">
                <label className="flex items-center gap-3 cursor-pointer">
                  <input
                    type="checkbox"
                    checked={simOxygen}
                    onChange={(e) => setSimOxygen(e.target.checked)}
                    className="w-4 h-4 rounded border-slate-700 text-teal-500 focus:ring-0 bg-slate-900"
                  />
                  <span className="text-xs font-medium text-slate-300">Receiving Supplemental Oxygen</span>
                </label>
              </div>
            </div>
          </div>

          {simResult && (
            <div className="mt-8 pt-6 border-t border-slate-800">
              <AcuityBadge level={simResult.triage.acuity} size="lg" />
              <div className="mt-4 p-4 rounded-xl bg-slate-900/80 border border-slate-800 text-sm">
                <div className="font-bold text-teal-400 mb-2">Recommended Next Action:</div>
                <div className="text-slate-200">{simResult.triage.recommended_action}</div>
                <div className="mt-3 text-xs text-slate-400">
                  <b>Clinical Reasons:</b> {simResult.triage.reasons.join(' · ')}
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
            <div className="glass-panel p-3.5 rounded-xl">
              <div className="relative">
                <Search className="w-3.5 h-3.5 text-slate-400 absolute left-3 top-2.5" />
                <input
                  type="text"
                  placeholder="Filter arrivals..."
                  value={searchTerm}
                  onChange={(e) => setSearchTerm(e.target.value)}
                  className="w-full bg-slate-900/90 text-xs text-white pl-8 pr-3 py-1.5 rounded-lg border border-slate-700/60 focus:border-teal-400 focus:outline-none"
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
                          ? 'bg-slate-800/90 border-teal-500/80 shadow-md'
                          : 'bg-slate-900/40 border-slate-800/70 hover:bg-slate-800/40 hover:border-slate-700'
                      }`}
                    >
                      <div className="truncate mr-2">
                        <div className="flex items-center gap-1.5">
                          <span className="font-mono text-xs font-bold text-slate-300">{p.patient_id}</span>
                          <span className="text-xs font-extrabold text-white truncate">{p.name}</span>
                        </div>
                        <div className="text-[11px] text-slate-400 truncate mt-0.5">
                          {p.complaint}
                        </div>
                      </div>
                      <span className={`text-[10px] font-extrabold px-2 py-0.5 rounded-full border ${cfg.badge}`}>
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
            <div className="glass-panel p-5 rounded-2xl relative overflow-hidden">
              <div className="flex items-start justify-between">
                <div>
                  <div className="flex items-center gap-2">
                    <h2 className="text-xl font-black text-white tracking-tight">{patient.name}</h2>
                    <span className="text-xs px-2 py-0.5 rounded bg-slate-800 text-teal-300 font-mono font-bold border border-slate-700">
                      {patient.patient_id}
                    </span>
                  </div>
                  <p className="text-xs text-slate-400 mt-1">
                    Age: <b className="text-slate-200">{Math.round(patient.age)} years</b> · Category:{' '}
                    <b className="text-slate-200 uppercase">{patient.age_band.replace('_', ' ')}</b>
                  </p>
                </div>
                <AcuityBadge level={patient.triage.acuity} size="sm" />
              </div>

              {/* Chief Complaint Tag */}
              <div className="mt-4 pt-3 border-t border-slate-800">
                <span className="text-[10px] font-bold text-slate-400 uppercase tracking-wider">Chief Complaint</span>
                <div className="text-sm font-bold text-teal-300 capitalize mt-0.5">
                  {patient.complaint}
                </div>
              </div>

              {/* Pediatric Mode Alert */}
              {isPeds && (
                <div className="mt-3 p-3 rounded-xl bg-blue-950/40 border border-blue-500/30 text-xs text-blue-200 flex items-start gap-2.5">
                  <span className="text-base">🧒</span>
                  <div>
                    <b className="font-bold text-blue-300">Pediatric Vital Scaling Applied</b>
                    <p className="text-[11px] text-slate-300 mt-0.5">
                      Vitals scored against age-calibrated reference intervals (Fleming / Lancet pediatric model).
                    </p>
                  </div>
                </div>
              )}

              {/* Recognized High-Risk Complaint Alert */}
              {patient.high_risk_category && (
                <div className="mt-3 p-3 rounded-xl bg-amber-950/40 border border-amber-500/40 text-xs text-amber-200 flex items-start gap-2.5">
                  <AlertOctagon className="w-4 h-4 text-amber-400 mt-0.5 shrink-0" />
                  <div>
                    <b className="font-bold text-amber-300">High-Risk Symptom Trigger: {patient.high_risk_category.replace('_', ' ')}</b>
                    <p className="text-[11px] text-slate-300 mt-0.5">
                      Matched keyword "{patient.high_risk_phrase}". Safety override sets baseline urgency at Level 2.
                    </p>
                  </div>
                </div>
              )}
            </div>

            {/* Telemetry & Vital Signs Grid */}
            <div className="glass-panel p-5 rounded-2xl space-y-3">
              <div className="flex items-center justify-between mb-2">
                <h3 className="text-xs font-bold uppercase tracking-wider text-slate-400 flex items-center gap-1.5">
                  <Heart className="w-3.5 h-3.5 text-rose-400" />
                  <span>Clinical Vital Telemetry</span>
                </h3>
                <span className="text-[10px] text-slate-400 font-mono">6 Parameters Observed</span>
              </div>

              <div className="grid grid-cols-2 sm:grid-cols-3 gap-3">
                {/* Heart Rate */}
                <div className="p-3 rounded-xl bg-slate-900/80 border border-slate-800 relative overflow-hidden">
                  <div className="flex items-center justify-between text-[11px] text-slate-400">
                    <span>Heart Rate</span>
                    <Heart className="w-3 h-3 text-rose-400" />
                  </div>
                  <div className="text-lg font-mono font-extrabold text-white mt-1">
                    {v.hr ? `${Math.round(v.hr)}` : '—'}{' '}
                    <span className="text-[10px] font-normal text-slate-400">bpm</span>
                  </div>
                  <div className="mt-2">
                    <ECGWaveform hr={v.hr} isCritical={v.hr >= 140 || v.hr < 45} isWarning={v.hr >= 100} />
                  </div>
                </div>

                {/* Respiratory Rate */}
                <div className="p-3 rounded-xl bg-slate-900/80 border border-slate-800">
                  <div className="flex items-center justify-between text-[11px] text-slate-400">
                    <span>Resp. Rate</span>
                    <Wind className="w-3 h-3 text-sky-400" />
                  </div>
                  <div className="text-lg font-mono font-extrabold text-white mt-1">
                    {v.rr ? `${Math.round(v.rr)}` : '—'}{' '}
                    <span className="text-[10px] font-normal text-slate-400">/min</span>
                  </div>
                  <span className={`text-[10px] font-bold ${v.rr >= 24 ? 'text-amber-400' : 'text-emerald-400'}`}>
                    {v.rr >= 30 ? '🚨 Severe Tachypnea' : v.rr >= 24 ? '⚠️ Elevated' : '✓ Normal'}
                  </span>
                </div>

                {/* SpO2 */}
                <div className="p-3 rounded-xl bg-slate-900/80 border border-slate-800">
                  <div className="flex items-center justify-between text-[11px] text-slate-400">
                    <span>Oxygen Sat.</span>
                    <Droplets className="w-3 h-3 text-teal-400" />
                  </div>
                  <div className="text-lg font-mono font-extrabold text-white mt-1">
                    {v.spo2 ? `${Math.round(v.spo2)}` : '—'}{' '}
                    <span className="text-[10px] font-normal text-slate-400">%</span>
                  </div>
                  <span className={`text-[10px] font-bold ${v.spo2 < 90 ? 'text-red-400' : v.spo2 < 94 ? 'text-amber-400' : 'text-emerald-400'}`}>
                    {v.spo2 < 90 ? '🚨 Critical Hypoxia' : v.spo2 < 94 ? '⚠️ Low Saturation' : '✓ Adequate'}
                  </span>
                </div>

                {/* Systolic BP */}
                <div className="p-3 rounded-xl bg-slate-900/80 border border-slate-800">
                  <div className="flex items-center justify-between text-[11px] text-slate-400">
                    <span>Blood Pressure</span>
                    <Gauge className="w-3 h-3 text-indigo-400" />
                  </div>
                  <div className="text-lg font-mono font-extrabold text-white mt-1">
                    {v.sbp ? `${Math.round(v.sbp)}` : '—'}{' '}
                    <span className="text-[10px] font-normal text-slate-400">mmHg</span>
                  </div>
                  <span className={`text-[10px] font-bold ${v.sbp < 90 ? 'text-red-400' : 'text-slate-400'}`}>
                    {v.sbp < 90 ? '🚨 Hypotensive' : 'Systolic'}
                  </span>
                </div>

                {/* Temperature */}
                <div className="p-3 rounded-xl bg-slate-900/80 border border-slate-800">
                  <div className="flex items-center justify-between text-[11px] text-slate-400">
                    <span>Temperature</span>
                    <Thermometer className="w-3 h-3 text-amber-400" />
                  </div>
                  <div className="text-lg font-mono font-extrabold text-white mt-1">
                    {v.temp ? `${v.temp.toFixed(1)}` : '—'}{' '}
                    <span className="text-[10px] font-normal text-slate-400">°C</span>
                  </div>
                  <span className={`text-[10px] font-bold ${v.temp >= 38.5 ? 'text-amber-400' : 'text-slate-400'}`}>
                    {v.temp >= 38.5 ? '⚠️ Febrile' : 'Normothermic'}
                  </span>
                </div>

                {/* Consciousness AVPU */}
                <div className="p-3 rounded-xl bg-slate-900/80 border border-slate-800">
                  <div className="flex items-center justify-between text-[11px] text-slate-400">
                    <span>Consciousness</span>
                    <Brain className="w-3 h-3 text-purple-400" />
                  </div>
                  <div className="text-lg font-mono font-extrabold text-white mt-1">
                    {v.avpu || 'A'}{' '}
                    <span className="text-[10px] font-normal text-slate-400">(AVPU)</span>
                  </div>
                  <span className={`text-[10px] font-bold ${v.avpu && v.avpu !== 'A' ? 'text-red-400' : 'text-emerald-400'}`}>
                    {v.avpu && v.avpu !== 'A' ? '🚨 Altered Status' : '✓ Alert'}
                  </span>
                </div>
              </div>
            </div>

            {/* Historical EHR Baseline */}
            <div className="glass-panel p-4 rounded-xl text-xs space-y-2">
              <div className="flex items-center justify-between text-slate-300 font-bold">
                <span className="flex items-center gap-1.5">
                  <History className="w-4 h-4 text-teal-400" />
                  Prior EHR Institutional History
                </span>
                {patient.has_history ? (
                  <span className="text-teal-400 text-[11px] font-semibold">Returning Patient</span>
                ) : (
                  <span className="text-slate-500 text-[11px]">First-Time Patient</span>
                )}
              </div>
              {patient.history ? (
                <div className="p-3 rounded-lg bg-teal-950/20 border border-teal-500/20 text-slate-300 space-y-1">
                  <div>
                    Baseline HR: <b>{patient.history.baseline_hr} bpm</b> · Baseline SBP: <b>{patient.history.baseline_sbp} mmHg</b>
                  </div>
                  <div>
                    Documented Chronic: <b>{patient.history.chronic_conditions.join(', ') || 'None on file'}</b>
                  </div>
                  <div className="text-[11px] text-slate-400">
                    Last Encounter: {patient.history.last_visit_date} (Assigned Level {patient.history.last_visit_acuity})
                  </div>
                </div>
              ) : (
                <div className="text-slate-400 text-[11px]">
                  No prior baseline on file. Assessed strictly against standard population reference bounds.
                </div>
              )}
            </div>
          </div>

          {/* RIGHT: AI Recommendation & Override (4 Cols) */}
          <div className="lg:col-span-4 space-y-4">
            {/* Acuity Level Hero Banner */}
            <div className="space-y-3">
              <div className="text-xs font-bold uppercase tracking-wider text-slate-400 flex items-center gap-1.5">
                <CheckCircle2 className="w-3.5 h-3.5 text-teal-400" />
                <span>Decision Support Output</span>
              </div>
              <AcuityBadge level={t.acuity} size="lg" />
            </div>

            {/* Recommended Next Action */}
            <div className="glass-panel p-4 rounded-xl border border-slate-800">
              <span className="text-[10px] font-bold text-slate-400 uppercase tracking-wider">Mandated Action</span>
              <div className="text-sm font-bold text-white mt-1 flex items-start gap-2">
                <ArrowRight className="w-4 h-4 text-teal-400 shrink-0 mt-0.5" />
                <span>{t.recommended_action}</span>
              </div>
            </div>

            {/* Red Flags Alert */}
            {t.red_flags && t.red_flags.length > 0 && (
              <div className="p-4 rounded-xl bg-red-950/40 border border-red-500/40 text-red-200">
                <div className="flex items-center gap-2 font-bold text-xs text-red-400 mb-2">
                  <AlertOctagon className="w-4 h-4" />
                  <span>Red-Flag Safety Triggers ({t.red_flags.length})</span>
                </div>
                <ul className="text-xs space-y-1 pl-4 list-disc marker:text-red-400 text-slate-300">
                  {t.red_flags.map((flag, idx) => (
                    <li key={idx}>{flag}</li>
                  ))}
                </ul>
              </div>
            )}

            {/* Assessment Confidence Gauge */}
            <div className="glass-panel p-4 rounded-xl space-y-2">
              <div className="flex items-center justify-between text-xs">
                <span className="font-bold text-slate-300">Confidence Score</span>
                <span className={`font-mono font-bold ${
                  t.confidence_label === 'High' ? 'text-emerald-400' :
                  t.confidence_label === 'Moderate' ? 'text-amber-400' : 'text-red-400'
                }`}>
                  {Math.round(t.confidence * 100)}% · {t.confidence_label}
                </span>
              </div>
              <div className="h-2 rounded-full bg-slate-900 overflow-hidden border border-slate-800">
                <div 
                  className={`h-full transition-all duration-500 ${
                    t.confidence_label === 'High' ? 'bg-emerald-500' :
                    t.confidence_label === 'Moderate' ? 'bg-amber-500' : 'bg-red-500'
                  }`}
                  style={{ width: `${Math.round(t.confidence * 100)}%` }}
                />
              </div>
              {t.confidence_label === 'Low' && (
                <div className="text-[11px] text-amber-300 bg-amber-950/40 p-2 rounded border border-amber-500/30">
                  ⚠️ Uncertainty Escalation: Acuity raised by +1 due to sparse vitals.
                </div>
              )}
            </div>

            {/* Decision Rationale */}
            <div className="glass-panel p-4 rounded-xl space-y-2">
              <div className="text-xs font-bold text-slate-300">Decision Rationale</div>
              <ul className="text-[11px] text-slate-400 space-y-1 pl-4 list-disc">
                {t.reasons.map((r, i) => (
                  <li key={i} className="leading-relaxed">{r}</li>
                ))}
              </ul>
            </div>

            {/* Clinician Override Form */}
            <div className="glass-panel p-4 rounded-xl border border-slate-800 space-y-3">
              <div className="flex items-center justify-between">
                <span className="text-xs font-bold text-white flex items-center gap-1.5">
                  <Shield className="w-3.5 h-3.5 text-teal-400" />
                  Clinician Confirmation & Override
                </span>
                <span className="text-[10px] text-slate-400 font-mono">Logged to Audit</span>
              </div>

              {overrideStatus && (
                <div className="p-2.5 rounded bg-emerald-950/40 border border-emerald-500/40 text-emerald-300 text-xs">
                  {overrideStatus}
                </div>
              )}

              <form onSubmit={handleOverrideSubmit} className="space-y-2.5">
                <div>
                  <label className="text-[11px] text-slate-400">Assigned ESI Level</label>
                  <select
                    value={overrideAcuity}
                    onChange={(e) => setOverrideAcuity(e.target.value)}
                    className="w-full mt-1 bg-slate-900 border border-slate-700 rounded-lg px-2.5 py-1.5 text-xs text-white focus:border-teal-400 focus:outline-none font-bold"
                  >
                    <option value={1}>Level 1 — Resuscitation</option>
                    <option value={2}>Level 2 — Emergent</option>
                    <option value={3}>Level 3 — Urgent</option>
                    <option value={4}>Level 4 — Less Urgent</option>
                    <option value={5}>Level 5 — Non-Urgent</option>
                  </select>
                </div>

                <div>
                  <label className="text-[11px] text-slate-400">Clinical Override Justification</label>
                  <input
                    type="text"
                    placeholder="Reason required for override..."
                    value={overrideReason}
                    onChange={(e) => setOverrideReason(e.target.value)}
                    className="w-full mt-1 bg-slate-900 border border-slate-700 rounded-lg px-2.5 py-1.5 text-xs text-white focus:border-teal-400 focus:outline-none"
                  />
                </div>

                <div className="flex items-center gap-2 pt-1">
                  <input
                    type="text"
                    value={clinicianId}
                    onChange={(e) => setClinicianId(e.target.value)}
                    className="w-24 bg-slate-900 border border-slate-700 rounded-lg px-2 py-1.5 text-xs text-slate-300 font-mono text-center"
                  />
                  <button
                    type="submit"
                    className="flex-1 py-1.5 px-3 rounded-lg bg-teal-600 hover:bg-teal-500 text-white text-xs font-bold transition-colors shadow"
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
