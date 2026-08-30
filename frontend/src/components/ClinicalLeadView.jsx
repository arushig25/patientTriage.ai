import React, { useState, useEffect } from 'react';
import { 
  ShieldCheck, 
  Lock, 
  Unlock, 
  BarChart3, 
  CheckCircle2, 
  AlertCircle,
  KeyRound
} from 'lucide-react';
import { ACUITY_CONFIG } from './AcuityBadge';

export default function ClinicalLeadView({ patients = [] }) {
  const [password, setPassword] = useState('');
  const [logsData, setLogsData] = useState({ logs: [], authorized: false, chain_intact: true });
  const [loading, setLoading] = useState(false);
  const [authError, setAuthError] = useState(false);

  const fetchLogs = async (pw = '') => {
    setLoading(true);
    setAuthError(false);
    try {
      const url = pw 
        ? `/api/audit/logs?role=Clinical%20Lead&password=${encodeURIComponent(pw)}`
        : `/api/audit/logs`;
      const res = await fetch(url);
      const data = await res.json();
      setLogsData(data);
      if (pw && !data.authorized) {
        setAuthError(true);
      }
    } catch (err) {
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchLogs();
  }, []);

  const handleUnlock = (e) => {
    e.preventDefault();
    fetchLogs(password);
  };

  const distribution = [1, 2, 3, 4, 5].map(lvl => ({
    level: lvl,
    count: patients.filter(p => p.triage.acuity === lvl).length,
    config: ACUITY_CONFIG[lvl]
  }));
  const maxCount = Math.max(...distribution.map(d => d.count), 1);

  const guardrails = [
    { title: 'Age-Aware Pediatric Reference Scaling', desc: 'Fleming / Lancet pediatric model dynamically applied to all vitals' },
    { title: 'Red-Flag Upward Overrides Only', desc: 'Critical clinical indicators can only escalate acuity, never downgrade' },
    { title: 'Uncertainty Escalation Guardrail', desc: 'Low completeness automatically raises patient priority by +1 tier' },
    { title: 'Explainable NLP Synonym Matching', desc: 'Symptom matching with phrase attribution and transparent reasoning' },
    { title: 'Mandated Override Auditing', desc: 'Clinician override requires clinical justification and cryptographic signing' },
    { title: 'HMAC-SHA256 Pseudonymization', desc: 'Patient identifiers masked at rest in compliance with data protection laws' },
    { title: 'Tamper-Evident SHA-256 Hash Chain', desc: 'Block-chained forward integrity guarantees audit trail immutability' },
    { title: 'Personal EHR Baseline Integration', desc: 'Patient historical vitals comparison avoids erroneous escalation' },
  ];

  return (
    <div className="space-y-6">
      {/* Top Grid: Distribution & Guardrails */}
      <div className="grid grid-cols-1 lg:grid-cols-12 gap-6">
        {/* Acuity Distribution Chart (7 Cols) */}
        <div className="lg:col-span-7 card-surface p-5 space-y-4">
          <div className="flex items-center justify-between pb-3 border-b border-clinical-200 dark:border-clinical-800">
            <div>
              <h3 className="text-sm font-black text-clinical-900 dark:text-white flex items-center gap-2">
                <BarChart3 className="w-4 h-4 text-brand-600 dark:text-brand-400" />
                <span>Department Acuity Distribution (ESI Levels 1–5)</span>
              </h3>
              <p className="text-xs text-clinical-500 font-medium">Breakdown of evaluated patients across clinical tiers</p>
            </div>
            <span className="text-xs font-mono font-black text-brand-700 dark:text-brand-400 bg-brand-50 dark:bg-brand-950/60 px-2.5 py-1 rounded-lg border border-brand-200 dark:border-brand-500/30">
              {patients.length} Evaluated
            </span>
          </div>

          {/* Bar Chart */}
          <div className="space-y-3 pt-2">
            {distribution.map(({ level, count, config }) => {
              const pct = Math.round((count / maxCount) * 100);
              return (
                <div key={level} className="space-y-1">
                  <div className="flex items-center justify-between text-xs">
                    <span className="font-black text-clinical-900 dark:text-white flex items-center gap-2">
                      <span className="w-2.5 h-2.5 rounded-full" style={{ backgroundColor: config.accent }}></span>
                      Level {level} — {config.label}
                    </span>
                    <span className="font-mono font-black text-clinical-700 dark:text-slate-300">
                      {count} <span className="text-[10px] text-clinical-400 font-normal">patients</span>
                    </span>
                  </div>
                  <div className="h-4 rounded-xl bg-clinical-100 dark:bg-clinical-950 overflow-hidden border border-clinical-200 dark:border-clinical-800 flex items-center p-0.5">
                    <div
                      className="h-full rounded-lg transition-all duration-500 flex items-center justify-end pr-2 text-[10px] font-mono font-black text-white shadow-xs"
                      style={{ 
                        width: `${Math.max(pct, 6)}%`, 
                        backgroundColor: config.accent 
                      }}
                    >
                      {count > 0 && count}
                    </div>
                  </div>
                </div>
              );
            })}
          </div>
        </div>

        {/* Clinical Guardrails & Safety Mechanisms (5 Cols) */}
        <div className="lg:col-span-5 card-surface p-5 space-y-3">
          <div className="pb-3 border-b border-clinical-200 dark:border-clinical-800">
            <h3 className="text-sm font-black text-clinical-900 dark:text-white flex items-center gap-2">
              <ShieldCheck className="w-4 h-4 text-brand-600 dark:text-brand-400" />
              <span>Clinical Safety & Guardrails</span>
            </h3>
            <p className="text-xs text-clinical-500 font-medium">Deterministic constraints enforced on model inference</p>
          </div>

          <div className="space-y-2 max-h-[320px] overflow-y-auto pr-1">
            {guardrails.map((g, i) => (
              <div key={i} className="p-2.5 rounded-xl bg-clinical-50 dark:bg-clinical-950/60 border border-clinical-200 dark:border-clinical-800/80 text-xs flex items-start gap-2.5">
                <CheckCircle2 className="w-4 h-4 text-brand-600 dark:text-brand-400 shrink-0 mt-0.5" />
                <div>
                  <div className="font-black text-clinical-900 dark:text-white">{g.title}</div>
                  <div className="text-[11px] text-clinical-500 dark:text-clinical-400 leading-snug mt-0.5 font-medium">{g.desc}</div>
                </div>
              </div>
            ))}
          </div>
        </div>
      </div>

      {/* Audit Vault & Verification Section */}
      <div className="card-surface p-6 space-y-4">
        <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-3 pb-4 border-b border-clinical-200 dark:border-clinical-800">
          <div>
            <div className="flex items-center gap-2">
              <h3 className="text-base font-black text-clinical-900 dark:text-white flex items-center gap-2">
                <Lock className="w-4 h-4 text-brand-600 dark:text-brand-400" />
                <span>Tamper-Evident SHA-256 Audit Trail</span>
              </h3>
              <span className={`text-[10px] font-black px-2.5 py-0.5 rounded-full border ${
                logsData.chain_intact
                  ? 'bg-emerald-50 text-emerald-700 border-emerald-200 dark:bg-emerald-950 dark:text-emerald-400 dark:border-emerald-500/40'
                  : 'bg-red-50 text-red-700 border-red-200 dark:bg-red-950 dark:text-red-400 dark:border-red-500/40'
              }`}>
                {logsData.chain_intact ? '✓ HASH CHAIN VALID' : '❌ CHAIN TAMPERED'}
              </span>
            </div>
            <p className="text-xs text-clinical-500 font-medium mt-1">
              Every score, override, and access event is cryptographically hash-chained with SHA-256 and encrypted at rest with Fernet.
            </p>
          </div>

          {/* Authorization Form */}
          <form onSubmit={handleUnlock} className="flex items-center gap-2 w-full sm:w-auto">
            <div className="relative">
              <KeyRound className="w-3.5 h-3.5 text-clinical-400 absolute left-2.5 top-2.5" />
              <input
                type="password"
                placeholder="Pass: triage-lead-2026"
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                className="bg-clinical-50 dark:bg-clinical-950 text-xs text-clinical-900 dark:text-white pl-8 pr-3 py-1.5 rounded-xl border border-clinical-200 dark:border-clinical-800 focus:border-brand-500 focus:outline-none w-48"
              />
            </div>
            <button
              type="submit"
              disabled={loading}
              className={`px-3.5 py-1.5 rounded-xl text-xs font-black transition-all flex items-center gap-1.5 ${
                logsData.authorized
                  ? 'bg-emerald-600 text-white shadow-xs'
                  : 'bg-brand-600 hover:bg-brand-500 text-white shadow-xs'
              }`}
            >
              {logsData.authorized ? <Unlock className="w-3.5 h-3.5" /> : <Lock className="w-3.5 h-3.5" />}
              <span>{logsData.authorized ? 'Authorized' : 'Authorize Re-link'}</span>
            </button>
          </form>
        </div>

        {authError && (
          <div className="p-3 rounded-xl bg-red-50 dark:bg-red-950/40 border border-red-200 dark:border-red-500/40 text-red-700 dark:text-red-300 text-xs flex items-center gap-2 font-bold">
            <AlertCircle className="w-4 h-4 shrink-0" />
            <span>Invalid password. Patient identifiers remain protected under HMAC-SHA256 pseudonymization.</span>
          </div>
        )}

        {logsData.authorized && (
          <div className="p-3 rounded-xl bg-emerald-50 dark:bg-emerald-950/40 border border-emerald-200 dark:border-emerald-500/40 text-emerald-800 dark:text-emerald-300 text-xs flex items-center gap-2 font-bold">
            <Unlock className="w-4 h-4 shrink-0" />
            <span>Identity re-linking active for Clinical Lead. Protected patient identifiers unmasked below.</span>
          </div>
        )}

        {/* Table */}
        <div className="overflow-x-auto rounded-2xl border border-clinical-200 dark:border-clinical-800">
          <table className="w-full text-left text-xs">
            <thead className="bg-clinical-50 dark:bg-clinical-950 text-clinical-500 uppercase tracking-wider font-black border-b border-clinical-200 dark:border-clinical-800">
              <tr>
                <th className="py-2.5 px-3">Timestamp (UTC)</th>
                <th className="py-2.5 px-3">Event Type</th>
                <th className="py-2.5 px-3">Patient Identifier</th>
                <th className="py-2.5 px-3">Actor / Clinician</th>
                <th className="py-2.5 px-3">Payload Summary</th>
                <th className="py-2.5 px-3 font-mono">Hash Preview</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-clinical-200 dark:divide-clinical-800/80 text-clinical-800 dark:text-clinical-200 font-semibold">
              {logsData.logs.map((log, i) => (
                <tr key={i} className="hover:bg-clinical-50 dark:hover:bg-clinical-900/40 transition-colors">
                  <td className="py-2 px-3 text-clinical-500 font-mono text-[11px]">
                    {log.ts ? log.ts.replace('T', ' ').replace('Z', '') : '---'}
                  </td>
                  <td className="py-2 px-3">
                    <span className={`px-2 py-0.5 rounded-full text-[10px] font-black uppercase ${
                      log.event_type === 'OVERRIDE' ? 'bg-amber-100 text-amber-800 dark:bg-amber-950/60 dark:text-amber-300 border border-amber-300 dark:border-amber-500/40' :
                      log.event_type === 'ALERT' ? 'bg-red-100 text-red-800 dark:bg-red-950/60 dark:text-red-300 border border-red-300 dark:border-red-500/40' :
                      log.event_type === 'SCORE' ? 'bg-brand-100 text-brand-800 dark:bg-brand-950/60 dark:text-brand-300 border border-brand-300 dark:border-brand-500/40' :
                      'bg-clinical-100 text-clinical-700 dark:bg-clinical-800 dark:text-slate-300'
                    }`}>
                      {log.event_type}
                    </span>
                  </td>
                  <td className="py-2 px-3 font-mono font-black text-clinical-900 dark:text-white">
                    {log.patient_id}
                  </td>
                  <td className="py-2 px-3 text-clinical-500">
                    {log.actor || 'SYSTEM'}
                  </td>
                  <td className="py-2 px-3 text-clinical-500 max-w-xs truncate text-[11px] font-medium">
                    {JSON.stringify(log.payload)}
                  </td>
                  <td className="py-2 px-3 text-clinical-400 font-mono text-[10px]">
                    {log.entry_hash}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
}
