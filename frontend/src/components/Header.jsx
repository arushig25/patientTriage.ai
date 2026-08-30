import React, { useState, useEffect } from 'react';
import { 
  Activity, 
  AlertTriangle, 
  ShieldCheck, 
  Clock, 
  Users, 
  Flame,
  Stethoscope,
  ChevronRight
} from 'lucide-react';

export default function Header({ 
  currentRole, 
  setRole, 
  surgeActive, 
  setSurge, 
  surgeFactor,
  stats,
  onVerifyChain 
}) {
  const [time, setTime] = useState(new Date());

  useEffect(() => {
    const timer = setInterval(() => setTime(new Date()), 1000);
    return () => clearInterval(timer);
  }, []);

  const roles = [
    { id: 'Triage Nurse', label: 'Triage Nurse', icon: Stethoscope, desc: 'Intake & Vitals' },
    { id: 'Charge Nurse', label: 'Charge Nurse', icon: Users, desc: 'Flow & Waiting Queue' },
    { id: 'Clinical Lead', label: 'Clinical Lead', icon: ShieldCheck, desc: 'Safety & Audit' },
  ];

  return (
    <header className="border-b border-slate-800 bg-[#0B132B]/95 backdrop-blur sticky top-0 z-50">
      {/* Top Banner Bar */}
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-3.5 flex flex-wrap items-center justify-between gap-4">
        {/* Hospital Branding */}
        <div className="flex items-center gap-3.5">
          <div className="w-10 h-10 rounded-xl bg-teal-500/20 border border-teal-500/40 flex items-center justify-center text-teal-400 shadow-lg shadow-teal-500/10">
            <Activity className="w-6 h-6 animate-pulse" />
          </div>
          <div>
            <div className="flex items-center gap-2">
              <h1 className="text-lg font-black tracking-tight text-white flex items-center gap-1.5">
                PatientTriage<span className="text-teal-400">.ai</span>
              </h1>
              <span className="text-[10px] uppercase font-bold tracking-wider px-2 py-0.5 rounded bg-slate-800 text-teal-300 border border-teal-500/30">
                v2.0 Clinical
              </span>
            </div>
            <p className="text-xs text-slate-400 font-medium">
              Emergency Department · Level 1 Trauma Center Pavilion
            </p>
          </div>
        </div>

        {/* System Telemetry & Surge Control */}
        <div className="flex items-center gap-3 sm:gap-4 flex-wrap">
          {/* Surge Toggle Button */}
          <button
            onClick={() => setSurge(!surgeActive)}
            className={`px-3.5 py-1.5 rounded-lg text-xs font-bold transition-all flex items-center gap-2 border shadow-sm ${
              surgeActive
                ? 'bg-red-600/90 text-white border-red-400 animate-pulse shadow-red-500/30'
                : 'bg-slate-800/80 text-slate-300 border-slate-700 hover:border-slate-600 hover:text-white'
            }`}
          >
            <Flame className={`w-4 h-4 ${surgeActive ? 'text-yellow-300' : 'text-slate-400'}`} />
            <span>{surgeActive ? `Surge Mode (${surgeFactor}×)` : 'Normal Flow'}</span>
          </button>

          {/* System Status Pill */}
          <div className="flex items-center gap-2 px-3 py-1.5 rounded-lg bg-emerald-950/40 border border-emerald-500/30 text-emerald-400 text-xs font-semibold">
            <span className="w-2 h-2 rounded-full bg-emerald-400 animate-ping-slow"></span>
            <span className="hidden sm:inline">Engine Online</span>
          </div>

          {/* Digital Clock */}
          <div className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg bg-slate-800/60 border border-slate-700/50 text-slate-300 text-xs font-mono font-medium">
            <Clock className="w-3.5 h-3.5 text-slate-400" />
            <span>{time.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit', second: '2-digit' })}</span>
          </div>
        </div>
      </div>

      {/* Role Navigation Bar */}
      <div className="bg-slate-900/90 border-t border-slate-800/80 px-4 sm:px-6 lg:px-8">
        <div className="max-w-7xl mx-auto flex items-center justify-between">
          <nav className="flex space-x-1 sm:space-x-2 py-1.5">
            {roles.map((role) => {
              const Icon = role.icon;
              const isActive = currentRole === role.id;
              return (
                <button
                  key={role.id}
                  onClick={() => setRole(role.id)}
                  className={`flex items-center gap-2 px-3.5 py-2 rounded-lg text-xs font-bold transition-all ${
                    isActive
                      ? 'bg-teal-500/20 text-teal-300 border border-teal-500/40 shadow-sm'
                      : 'text-slate-400 hover:text-slate-200 hover:bg-slate-800/50'
                  }`}
                >
                  <Icon className={`w-4 h-4 ${isActive ? 'text-teal-400' : 'text-slate-400'}`} />
                  <span>{role.label}</span>
                  <span className="hidden md:inline text-[10px] font-normal text-slate-400">
                    ({role.desc})
                  </span>
                </button>
              );
            })}
          </nav>

          {/* Quick Verification Button */}
          <div className="hidden lg:flex items-center">
            <button
              onClick={onVerifyChain}
              className="text-[11px] font-semibold text-slate-400 hover:text-teal-300 flex items-center gap-1 transition-colors"
            >
              <ShieldCheck className="w-3.5 h-3.5 text-teal-400" />
              <span>SHA-256 Audit Trail Active</span>
            </button>
          </div>
        </div>
      </div>
    </header>
  );
}
