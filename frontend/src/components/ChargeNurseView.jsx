import React, { useState } from 'react';
import { 
  Users, 
  AlertTriangle, 
  Flame, 
  Clock, 
  Search, 
  Filter, 
  Activity,
  CheckCircle,
  ArrowUpRight
} from 'lucide-react';
import AcuityBadge, { ACUITY_CONFIG } from './AcuityBadge';

export default function ChargeNurseView({ 
  patients = [], 
  stats = {}, 
  surgeActive, 
  surgeFactor,
  onSelectPatient,
  setRole
}) {
  const [searchTerm, setSearchTerm] = useState('');
  const [filterType, setFilterType] = useState('ALL'); // 'ALL' | 'BREACH' | 'HIGH_ACUITY'

  const filteredPatients = patients.filter(p => {
    const matchesSearch = 
      p.name.toLowerCase().includes(searchTerm.toLowerCase()) ||
      p.patient_id.toLowerCase().includes(searchTerm.toLowerCase()) ||
      p.complaint.toLowerCase().includes(searchTerm.toLowerCase());
    
    if (!matchesSearch) return false;
    if (filterType === 'BREACH') return p.flow.breach;
    if (filterType === 'HIGH_ACUITY') return p.triage.acuity <= 2;
    return true;
  });

  return (
    <div className="space-y-6">
      {/* Top Department Flow Metrics */}
      <div className="grid grid-cols-2 sm:grid-cols-5 gap-3.5">
        <div className="card-surface p-4">
          <div className="text-[11px] font-black text-clinical-500 uppercase tracking-wider">Queue Total</div>
          <div className="text-2xl font-mono font-black text-clinical-900 dark:text-white mt-1">{stats.total_patients || patients.length}</div>
          <div className="text-[10px] font-bold text-brand-600 dark:text-brand-400 mt-0.5">Active Waiting Arrivals</div>
        </div>

        <div className="card-surface p-4 border-red-200 dark:border-red-500/30 bg-red-50/40 dark:bg-red-950/20">
          <div className="text-[11px] font-black text-red-600 dark:text-red-400 uppercase tracking-wider">Immediate (L1)</div>
          <div className="text-2xl font-mono font-black text-red-600 dark:text-red-400 mt-1">{stats.level_1_resuscitation || 0}</div>
          <div className="text-[10px] font-bold text-red-700/80 dark:text-red-300/70 mt-0.5">Zero Wait Ceiling</div>
        </div>

        <div className="card-surface p-4 border-orange-200 dark:border-orange-500/30 bg-orange-50/40 dark:bg-orange-950/20">
          <div className="text-[11px] font-black text-orange-600 dark:text-orange-400 uppercase tracking-wider">Emergent (L2)</div>
          <div className="text-2xl font-mono font-black text-orange-600 dark:text-orange-400 mt-1">{stats.level_2_emergent || 0}</div>
          <div className="text-[10px] font-bold text-orange-700/80 dark:text-orange-300/70 mt-0.5">&lt; 10 min Target</div>
        </div>

        <div className="card-surface p-4 border-amber-200 dark:border-amber-500/30 bg-amber-50/40 dark:bg-amber-950/20">
          <div className="text-[11px] font-black text-amber-600 dark:text-amber-400 uppercase tracking-wider">Wait Breaches</div>
          <div className="text-2xl font-mono font-black text-amber-600 dark:text-amber-400 mt-1">{stats.safe_wait_breaches || 0}</div>
          <div className="text-[10px] font-bold text-amber-700/80 dark:text-amber-300/70 mt-0.5">Reassess Urgently</div>
        </div>

        <div className="card-surface p-4">
          <div className="text-[11px] font-black text-clinical-500 uppercase tracking-wider">Surge Multiplier</div>
          <div className="text-2xl font-mono font-black text-clinical-900 dark:text-white mt-1">{surgeFactor}×</div>
          <div className={`text-[10px] font-black mt-0.5 ${surgeActive ? 'text-red-600 dark:text-red-400' : 'text-emerald-600 dark:text-emerald-400'}`}>
            {surgeActive ? 'Surge Protocol On' : 'Standard Capacity'}
          </div>
        </div>
      </div>

      {/* Surge Banner */}
      {surgeActive ? (
        <div className="p-4 rounded-2xl bg-gradient-to-r from-red-600 via-rose-600 to-red-700 text-white shadow-lg shadow-red-500/20 flex items-start gap-3">
          <Flame className="w-5 h-5 text-yellow-300 shrink-0 mt-0.5 animate-bounce" />
          <div>
            <div className="font-black text-sm flex items-center gap-2">
              <span>SURGE PROTOCOL ACTIVE — {surgeFactor}× Normal Department Flow</span>
            </div>
            <p className="text-xs text-red-100 mt-1 leading-relaxed font-medium">
              Waiting ceilings have dynamically tightened. The waiting-room priority queue is re-ranked automatically based on clinical urgency and uncertainty penalties.
            </p>
          </div>
        </div>
      ) : (
        <div className="p-3.5 rounded-2xl bg-emerald-50 dark:bg-emerald-950/30 border border-emerald-200 dark:border-emerald-500/30 text-emerald-800 dark:text-emerald-300 text-xs flex items-center justify-between font-bold">
          <span className="flex items-center gap-2">
            <CheckCircle className="w-4 h-4 text-emerald-600 dark:text-emerald-400" />
            Standard Department Flow — Safe-waiting limits active across all 5 clinical tiers.
          </span>
          <span className="font-mono text-[11px] text-clinical-500">Beds: 20 Normal</span>
        </div>
      )}

      {/* Filter and Search Bar */}
      <div className="flex flex-col sm:flex-row items-center justify-between gap-3 card-surface p-3.5">
        <div className="relative w-full sm:w-80">
          <Search className="w-4 h-4 text-clinical-400 absolute left-3 top-2.5" />
          <input
            type="text"
            placeholder="Search patient, MRN, complaint..."
            value={searchTerm}
            onChange={(e) => setSearchTerm(e.target.value)}
            className="w-full bg-clinical-50 dark:bg-clinical-950 text-xs text-clinical-900 dark:text-white pl-9 pr-3 py-2 rounded-xl border border-clinical-200 dark:border-clinical-800 focus:border-brand-500 focus:outline-none"
          />
        </div>

        <div className="flex items-center gap-2 w-full sm:w-auto">
          <button
            onClick={() => setFilterType('ALL')}
            className={`px-3 py-1.5 rounded-xl text-xs font-black transition-all ${
              filterType === 'ALL'
                ? 'bg-brand-600 text-white shadow-xs'
                : 'bg-clinical-50 dark:bg-clinical-900 text-clinical-600 dark:text-clinical-400 hover:text-clinical-900 border border-clinical-200 dark:border-clinical-800'
            }`}
          >
            All ({patients.length})
          </button>
          <button
            onClick={() => setFilterType('BREACH')}
            className={`px-3 py-1.5 rounded-xl text-xs font-black transition-all ${
              filterType === 'BREACH'
                ? 'bg-amber-500 text-white shadow-xs'
                : 'bg-clinical-50 dark:bg-clinical-900 text-clinical-600 dark:text-clinical-400 hover:text-clinical-900 border border-clinical-200 dark:border-clinical-800'
            }`}
          >
            Breaches Only ({stats.safe_wait_breaches || 0})
          </button>
          <button
            onClick={() => setFilterType('HIGH_ACUITY')}
            className={`px-3 py-1.5 rounded-xl text-xs font-black transition-all ${
              filterType === 'HIGH_ACUITY'
                ? 'bg-red-600 text-white shadow-xs'
                : 'bg-clinical-50 dark:bg-clinical-900 text-clinical-600 dark:text-clinical-400 hover:text-clinical-900 border border-clinical-200 dark:border-clinical-800'
            }`}
          >
            L1 & L2 Urgent ({(stats.level_1_resuscitation || 0) + (stats.level_2_emergent || 0)})
          </button>
        </div>
      </div>

      {/* Live Priority Queue Board */}
      <div className="space-y-2.5">
        {filteredPatients.length === 0 ? (
          <div className="card-surface p-8 text-center text-clinical-500 text-xs font-medium">
            No patients match current filter criteria.
          </div>
        ) : (
          filteredPatients.map((p, index) => {
            const isBreach = p.flow.breach;
            const waitRatio = p.flow.safe_limit_minutes > 0 ? (p.flow.waited_minutes / p.flow.safe_limit_minutes) : 1;

            return (
              <div
                key={p.patient_id}
                className={`card-surface p-4 flex flex-col md:flex-row items-start md:items-center justify-between gap-4 card-interactive ${
                  isBreach 
                    ? 'border-red-400 dark:border-red-500/40 bg-red-50/30 dark:bg-red-950/20 shadow-sm' 
                    : ''
                }`}
              >
                {/* Priority Rank & Patient Identity */}
                <div className="flex items-center gap-3.5 min-w-[240px]">
                  <div className="w-8 h-8 rounded-xl bg-clinical-100 dark:bg-clinical-800 text-xs font-mono font-black text-clinical-700 dark:text-clinical-300 flex items-center justify-center border border-clinical-200 dark:border-clinical-700">
                    #{index + 1}
                  </div>
                  <div>
                    <div className="flex items-center gap-2">
                      <span className="font-mono text-xs font-black text-brand-700 dark:text-brand-400">{p.patient_id}</span>
                      <span className="text-sm font-black text-clinical-900 dark:text-white">{p.name}</span>
                      <span className="text-xs text-clinical-500 font-bold">({Math.round(p.age)}y)</span>
                    </div>
                    <div className="text-xs text-clinical-500 dark:text-clinical-400 mt-0.5 truncate max-w-xs font-medium">
                      {p.complaint}
                    </div>
                  </div>
                </div>

                {/* Acuity Level Badge */}
                <div className="min-w-[130px]">
                  <AcuityBadge level={p.triage.acuity} size="sm" />
                </div>

                {/* Wait Time vs Safe Limit */}
                <div className="min-w-[200px] space-y-1">
                  <div className="flex items-center justify-between text-xs font-bold">
                    <span className="text-clinical-500">Waited: <b className="font-mono text-clinical-900 dark:text-white">{p.flow.waited_minutes}m</b></span>
                    <span className="text-clinical-500">Limit: <b className="font-mono text-clinical-900 dark:text-white">{p.flow.safe_limit_minutes}m</b></span>
                  </div>
                  <div className="h-2 rounded-full bg-clinical-100 dark:bg-clinical-950 overflow-hidden border border-clinical-200 dark:border-clinical-800">
                    <div 
                      className={`h-full rounded-full transition-all duration-300 ${
                        isBreach ? 'bg-red-500' : waitRatio > 0.7 ? 'bg-amber-500' : 'bg-brand-500'
                      }`}
                      style={{ width: `${Math.min(100, Math.round(waitRatio * 100))}%` }}
                    />
                  </div>
                </div>

                {/* Status Indicator & Action */}
                <div className="flex items-center justify-between md:justify-end gap-3 w-full md:w-auto">
                  {isBreach ? (
                    <span className="px-2.5 py-1 rounded-full text-[11px] font-black bg-red-100 text-red-700 dark:bg-red-950/60 dark:text-red-300 border border-red-300 dark:border-red-500/40 animate-pulse">
                      🚨 REASSESS NOW
                    </span>
                  ) : (
                    <span className="text-xs text-clinical-500 font-semibold">
                      Within Safe Bounds
                    </span>
                  )}

                  <button
                    onClick={() => {
                      onSelectPatient(p);
                      setRole('Triage Nurse');
                    }}
                    className="p-2 rounded-xl bg-clinical-100 dark:bg-clinical-800 hover:bg-brand-600 hover:text-white text-clinical-700 dark:text-clinical-300 transition-colors shadow-xs"
                    title="Open in Triage Intake"
                  >
                    <ArrowUpRight className="w-4 h-4" />
                  </button>
                </div>
              </div>
            );
          })
        )}
      </div>
    </div>
  );
}
