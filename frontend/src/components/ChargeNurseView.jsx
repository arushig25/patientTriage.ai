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
        <div className="glass-panel p-4 rounded-xl border border-slate-800">
          <div className="text-[11px] font-bold text-slate-400 uppercase tracking-wider">Queue Total</div>
          <div className="text-2xl font-mono font-extrabold text-white mt-1">{stats.total_patients || patients.length}</div>
          <div className="text-[10px] text-teal-400 mt-0.5">Active Arrivals</div>
        </div>

        <div className="glass-panel p-4 rounded-xl border border-red-500/20 bg-red-950/10">
          <div className="text-[11px] font-bold text-red-400 uppercase tracking-wider">Immediate (L1)</div>
          <div className="text-2xl font-mono font-extrabold text-red-400 mt-1">{stats.level_1_resuscitation || 0}</div>
          <div className="text-[10px] text-red-300/70 mt-0.5">Zero Wait Ceiling</div>
        </div>

        <div className="glass-panel p-4 rounded-xl border border-orange-500/20 bg-orange-950/10">
          <div className="text-[11px] font-bold text-orange-400 uppercase tracking-wider">Emergent (L2)</div>
          <div className="text-2xl font-mono font-extrabold text-orange-400 mt-1">{stats.level_2_emergent || 0}</div>
          <div className="text-[10px] text-orange-300/70 mt-0.5">&lt; 10 min Target</div>
        </div>

        <div className="glass-panel p-4 rounded-xl border border-amber-500/20 bg-amber-950/10">
          <div className="text-[11px] font-bold text-amber-400 uppercase tracking-wider">Breaches</div>
          <div className="text-2xl font-mono font-extrabold text-amber-400 mt-1">{stats.safe_wait_breaches || 0}</div>
          <div className="text-[10px] text-amber-300/70 mt-0.5">Reassess Now Alert</div>
        </div>

        <div className="glass-panel p-4 rounded-xl border border-slate-800">
          <div className="text-[11px] font-bold text-slate-400 uppercase tracking-wider">Volume Factor</div>
          <div className="text-2xl font-mono font-extrabold text-white mt-1">{surgeFactor}×</div>
          <div className={`text-[10px] font-bold mt-0.5 ${surgeActive ? 'text-red-400' : 'text-emerald-400'}`}>
            {surgeActive ? 'Surge Protocol' : 'Standard Baselines'}
          </div>
        </div>
      </div>

      {/* Surge Banner */}
      {surgeActive ? (
        <div className="p-4 rounded-xl bg-gradient-to-r from-red-950/80 to-slate-900 border border-red-500/50 text-red-200 flex items-start gap-3 shadow-lg shadow-red-950/30">
          <Flame className="w-5 h-5 text-red-400 shrink-0 mt-0.5 animate-bounce" />
          <div>
            <div className="font-extrabold text-sm text-red-300 flex items-center gap-2">
              <span>SURGE MODE ACTIVE — {surgeFactor}× Normal Department Load</span>
            </div>
            <p className="text-xs text-slate-300 mt-1 leading-relaxed">
              Safe-waiting ceilings have automatically tightened to mitigate waiting-room deterioration. Queue is dynamically re-ordered prioritizing physiological vulnerability and uncertainty escalations.
            </p>
          </div>
        </div>
      ) : (
        <div className="p-3 rounded-xl bg-emerald-950/30 border border-emerald-500/30 text-emerald-300 text-xs flex items-center justify-between">
          <span className="flex items-center gap-2">
            <CheckCircle className="w-4 h-4 text-emerald-400" />
            Normal Department Flow — Standard safe-wait targets in effect across all 5 tiers.
          </span>
          <span className="font-mono text-[11px] text-slate-400">Normal Capacity: 20 beds</span>
        </div>
      )}

      {/* Filter and Search Bar */}
      <div className="flex flex-col sm:flex-row items-center justify-between gap-3 glass-panel p-3.5 rounded-xl">
        <div className="relative w-full sm:w-80">
          <Search className="w-4 h-4 text-slate-400 absolute left-3 top-2.5" />
          <input
            type="text"
            placeholder="Search name, MRN, complaint..."
            value={searchTerm}
            onChange={(e) => setSearchTerm(e.target.value)}
            className="w-full bg-slate-900 text-xs text-white pl-9 pr-3 py-2 rounded-lg border border-slate-700 focus:border-teal-400 focus:outline-none"
          />
        </div>

        <div className="flex items-center gap-2 w-full sm:w-auto">
          <button
            onClick={() => setFilterType('ALL')}
            className={`px-3 py-1.5 rounded-lg text-xs font-bold transition-all ${
              filterType === 'ALL'
                ? 'bg-teal-500 text-white shadow-sm'
                : 'bg-slate-900 text-slate-400 hover:text-white border border-slate-700/60'
            }`}
          >
            All ({patients.length})
          </button>
          <button
            onClick={() => setFilterType('BREACH')}
            className={`px-3 py-1.5 rounded-lg text-xs font-bold transition-all ${
              filterType === 'BREACH'
                ? 'bg-amber-500 text-slate-900 shadow-sm'
                : 'bg-slate-900 text-slate-400 hover:text-white border border-slate-700/60'
            }`}
          >
            Breaches Only ({stats.safe_wait_breaches || 0})
          </button>
          <button
            onClick={() => setFilterType('HIGH_ACUITY')}
            className={`px-3 py-1.5 rounded-lg text-xs font-bold transition-all ${
              filterType === 'HIGH_ACUITY'
                ? 'bg-red-600 text-white shadow-sm'
                : 'bg-slate-900 text-slate-400 hover:text-white border border-slate-700/60'
            }`}
          >
            L1 & L2 Critical ({(stats.level_1_resuscitation || 0) + (stats.level_2_emergent || 0)})
          </button>
        </div>
      </div>

      {/* Live Priority Queue Board */}
      <div className="space-y-2.5">
        {filteredPatients.length === 0 ? (
          <div className="glass-panel p-8 text-center text-slate-400 text-xs">
            No patients match current filter criteria.
          </div>
        ) : (
          filteredPatients.map((p, index) => {
            const cfg = ACUITY_CONFIG[p.triage.acuity];
            const isBreach = p.flow.breach;
            const waitRatio = p.flow.safe_limit_minutes > 0 ? (p.flow.waited_minutes / p.flow.safe_limit_minutes) : 1;

            return (
              <div
                key={p.patient_id}
                className={`glass-panel p-4 rounded-xl border flex flex-col md:flex-row items-start md:items-center justify-between gap-4 transition-all hover:border-slate-600 ${
                  isBreach 
                    ? 'border-red-500/40 bg-red-950/10 shadow-lg shadow-red-950/20' 
                    : 'border-slate-800'
                }`}
              >
                {/* Priority Rank & Patient Identity */}
                <div className="flex items-center gap-3.5 min-w-[240px]">
                  <div className="w-7 h-7 rounded-lg bg-slate-900 border border-slate-800 text-xs font-mono font-black text-slate-400 flex items-center justify-center">
                    #{index + 1}
                  </div>
                  <div>
                    <div className="flex items-center gap-2">
                      <span className="font-mono text-xs font-bold text-teal-400">{p.patient_id}</span>
                      <span className="text-sm font-extrabold text-white">{p.name}</span>
                      <span className="text-xs text-slate-400">({Math.round(p.age)}y)</span>
                    </div>
                    <div className="text-xs text-slate-400 mt-0.5 truncate max-w-xs">
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
                  <div className="flex items-center justify-between text-xs">
                    <span className="text-slate-400">Waited: <b className="font-mono text-white">{p.flow.waited_minutes}m</b></span>
                    <span className="text-slate-400">Safe Target: <b className="font-mono text-white">{p.flow.safe_limit_minutes}m</b></span>
                  </div>
                  <div className="h-1.5 rounded-full bg-slate-900 overflow-hidden border border-slate-800">
                    <div 
                      className={`h-full rounded-full transition-all duration-300 ${
                        isBreach ? 'bg-red-500' : waitRatio > 0.7 ? 'bg-amber-500' : 'bg-teal-500'
                      }`}
                      style={{ width: `${Math.min(100, Math.round(waitRatio * 100))}%` }}
                    />
                  </div>
                </div>

                {/* Status Indicator & Action */}
                <div className="flex items-center justify-between md:justify-end gap-3 w-full md:w-auto">
                  {isBreach ? (
                    <span className="px-2.5 py-1 rounded-full text-[11px] font-extrabold bg-red-500/20 text-red-400 border border-red-500/40 animate-pulse">
                      🚨 REASSESS NOW
                    </span>
                  ) : (
                    <span className="text-xs text-slate-500 font-medium">
                      Within Safe Ceiling
                    </span>
                  )}

                  <button
                    onClick={() => {
                      onSelectPatient(p);
                      setRole('Triage Nurse');
                    }}
                    className="p-1.5 rounded-lg bg-slate-800 hover:bg-teal-600 text-slate-300 hover:text-white transition-colors"
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
