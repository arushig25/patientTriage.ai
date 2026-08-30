import React, { useState, useEffect } from 'react';
import { 
  ShieldCheck, 
  Lock, 
  Unlock, 
  BarChart3, 
  FileText, 
  CheckCircle2, 
  AlertCircle,
  KeyRound,
  Eye,
  Clock
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

  // Compute acuity distribution counts
  const distribution = [1, 2, 3, 4, 5].map(lvl => ({
    level: lvl,
    count: patients.filter(p => p.triage.acuity === lvl).length,
    config: ACUITY_CONFIG[lvl]
  }));
  const maxCount = Math.max(...distribution.map(d => d.count), 1);

  const guardrails = [
    { title: 'Age-Aware Pediatric Scaling', desc: 'Fleming/Lancet pediatric percentiles applied dynamically' },
    { title: 'Red-Flag Upward Overrides', desc: 'Critical flags can only escalate acuity, never relax' },
    { title: 'Uncertainty Safety Escalation', desc: 'Low completeness raises acuity by +1 tier' },
    { title: 'Explainable NLP Matching', desc: 'Synonym-mapped high-risk symptom matching with phrase attribution' },
    { title: 'Mandated Override Auditing', desc: 'All clinician overrides require reason and are cryptographically hashed' },
    { title: 'HMAC-SHA256 Pseudonymization', desc: 'Patient MRNs masked in audit trail to protect PHI' },
    { title: 'Tamper-Evident Hash Chain', desc: 'Block-chained audit log with cryptographic forward integrity' },
    { title: 'Personal Baseline Scoring', desc: 'EHR historical normal comparison prevents over/under-triage' },
  ];

  return (
    <div className="space-y-6">
      {/* Top Grid: Distribution & Guardrails */}
      <div className="grid grid-cols-1 lg:grid-cols-12 gap-6">
        {/* Acuity Distribution Chart (7 Cols) */}
        <div className="lg:col-span-7 glass-panel p-5 rounded-2xl space-y-4">
          <div className="flex items-center justify-between pb-3 border-b border-slate-800">
            <div>
              <h3 className="text-sm font-extrabold text-white flex items-center gap-2">
                <BarChart3 className="w-4 h-4 text-teal-400" />
                <span>Department Acuity Distribution (ESI Levels 1–5)</span>
              </h3>
              <p className="text-xs text-slate-400">Total active patient population across urgency tiers</p>
            </div>
            <span className="text-xs font-mono text-slate-400 font-bold">{patients.length} Evaluated</span>
          </div>

          {/* Bar Chart Visualization */}
          <div className="space-y-3 pt-2">
            {distribution.map(({ level, count, config }) => {
              const pct = Math.round((count / maxCount) * 100);
              return (
                <div key={level} className="space-y-1">
                  <div className="flex items-center justify-between text-xs">
                    <span className="font-extrabold text-white flex items-center gap-2">
                      <span className="w-2 h-2 rounded-full" style={{ backgroundColor: config.accent }}></span>
                      Level {level} · {config.label}
                    </span>
                    <span className="font-mono font-bold text-slate-300">
                      {count} <span className="text-[10px] text-slate-500 font-normal">patients</span>
                    </span>
                  </div>
                  <div className="h-4 rounded-lg bg-slate-900 overflow-hidden border border-slate-800 flex items-center p-0.5">
                    <div
                      className="h-full rounded-md transition-all duration-500 flex items-center justify-end pr-2 text-[10px] font-mono font-bold text-white shadow-sm"
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
        <div className="lg:col-span-5 glass-panel p-5 rounded-2xl space-y-3">
          <div className="pb-3 border-b border-slate-800">
            <h3 className="text-sm font-extrabold text-white flex items-center gap-2">
              <ShieldCheck className="w-4 h-4 text-teal-400" />
              <span>Clinical Safety & Guardrails</span>
            </h3>
            <p className="text-xs text-slate-400">Deterministic model constraints & regulatory controls</p>
          </div>

          <div className="space-y-2 max-h-[320px] overflow-y-auto pr-1">
            {guardrails.map((g, i) => (
              <div key={i} className="p-2.5 rounded-xl bg-slate-900/70 border border-slate-800 text-xs flex items-start gap-2.5">
                <CheckCircle2 className="w-4 h-4 text-teal-400 shrink-0 mt-0.5" />
                <div>
                  <div className="font-extrabold text-white">{g.title}</div>
                  <div className="text-[11px] text-slate-400 leading-snug mt-0.5">{g.desc}</div>
                </div>
              </div>
            ))}
          </div>
        </div>
      </div>

      {/* Audit Vault & Verification Section */}
      <div className="glass-panel p-6 rounded-2xl space-y-4">
        <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-3 pb-4 border-b border-slate-800">
          <div>
            <div className="flex items-center gap-2">
              <h3 className="text-base font-extrabold text-white flex items-center gap-2">
                <Lock className="w-4 h-4 text-teal-400" />
                <span>Tamper-Evident SHA-256 Audit Log</span>
              </h3>
              <span className={`text-[10px] font-bold px-2 py-0.5 rounded-full border ${
                logsData.chain_intact
                  ? 'bg-emerald-950 text-emerald-400 border-emerald-500/40'
                  : 'bg-red-950 text-red-400 border-red-500/40'
              }`}>
                {logsData.chain_intact ? '✓ HASH CHAIN INTACT' : '❌ CHAIN BROKEN'}
              </span>
            </div>
            <p className="text-xs text-slate-400 mt-1">
              Every score, override, alert, and access event is cryptographically hash-chained with SHA-256 and encrypted at rest.
            </p>
          </div>

          {/* Authorization Form */}
          <form onSubmit={handleUnlock} className="flex items-center gap-2 w-full sm:w-auto">
            <div className="relative">
              <KeyRound className="w-3.5 h-3.5 text-slate-400 absolute left-2.5 top-2.5" />
              <input
                type="password"
                placeholder="Password: triage-lead-2026"
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                className="bg-slate-900 text-xs text-white pl-8 pr-3 py-1.5 rounded-lg border border-slate-700 focus:border-teal-400 focus:outline-none w-48"
              />
            </div>
            <button
              type="submit"
              disabled={loading}
              className={`px-3.5 py-1.5 rounded-lg text-xs font-bold transition-all flex items-center gap-1.5 ${
                logsData.authorized
                  ? 'bg-emerald-600 text-white shadow-sm'
                  : 'bg-teal-600 hover:bg-teal-500 text-white shadow-sm'
              }`}
            >
              {logsData.authorized ? <Unlock className="w-3.5 h-3.5" /> : <Lock className="w-3.5 h-3.5" />}
              <span>{logsData.authorized ? 'Authorized' : 'Authorize Re-link'}</span>
            </button>
          </form>
        </div>

        {authError && (
          <div className="p-3 rounded-lg bg-red-950/40 border border-red-500/40 text-red-300 text-xs flex items-center gap-2">
            <AlertCircle className="w-4 h-4 shrink-0" />
            <span>Invalid authorization credentials. Access restricted to protected pseudonymized mode.</span>
          </div>
        )}

        {logsData.authorized && (
          <div className="p-3 rounded-lg bg-emerald-950/40 border border-emerald-500/40 text-emerald-300 text-xs flex items-center gap-2">
            <Unlock className="w-4 h-4 shrink-0" />
            <span>Identity re-linking active for Clinical Lead review. Protected patient MRNs unmasked below.</span>
          </div>
        )}

        {/* Audit Log Table */}
        <div className="overflow-x-auto rounded-xl border border-slate-800">
          <table className="w-full text-left text-xs">
            <thead className="bg-slate-900/80 text-slate-400 uppercase tracking-wider font-bold border-b border-slate-800">
              <tr>
                <th className="py-2.5 px-3">Timestamp (UTC)</th>
                <th className="py-2.5 px-3">Event Type</th>
                <th className="py-2.5 px-3">Patient Identifier</th>
                <th className="py-2.5 px-3">Actor / Clinician</th>
                <th className="py-2.5 px-3">Payload Summary</th>
                <th className="py-2.5 px-3 font-mono">Hash Preview</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-800/80 text-slate-300 font-medium">
              {logsData.logs.map((log, i) => (
                <tr key={i} className="hover:bg-slate-800/30 transition-colors">
                  <td className="py-2 px-3 text-slate-400 font-mono text-[11px]">
                    {log.ts ? log.ts.replace('T', ' ').replace('Z', '') : '---'}
                  </td>
                  <td className="py-2 px-3">
                    <span className={`px-2 py-0.5 rounded text-[10px] font-extrabold uppercase ${
                      log.event_type === 'OVERRIDE' ? 'bg-amber-500/20 text-amber-300 border border-amber-500/40' :
                      log.event_type === 'ALERT' ? 'bg-red-500/20 text-red-300 border border-red-500/40' :
                      log.event_type === 'SCORE' ? 'bg-teal-500/20 text-teal-300 border border-teal-500/40' :
                      'bg-slate-800 text-slate-300'
                    }`}>
                      {log.event_type}
                    </span>
                  </td>
                  <td className="py-2 px-3 font-mono font-bold text-white">
                    {log.patient_id}
                  </td>
                  <td className="py-2 px-3 text-slate-400">
                    {log.actor || 'SYSTEM'}
                  </td>
                  <td className="py-2 px-3 text-slate-400 max-w-xs truncate text-[11px]">
                    {JSON.stringify(log.payload)}
                  </td>
                  <td className="py-2 px-3 text-slate-500 font-mono text-[10px]">
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
