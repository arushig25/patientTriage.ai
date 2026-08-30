import React, { useState, useEffect } from 'react';
import { 
  Activity, 
  ShieldCheck, 
  Clock, 
  Users, 
  Flame,
  Stethoscope,
  Sun,
  Moon
} from 'lucide-react';

export default function Header({ 
  currentRole, 
  setRole, 
  surgeActive, 
  setSurge, 
  surgeFactor,
  darkMode,
  setDarkMode,
  onVerifyChain 
}) {
  const [time, setTime] = useState(new Date());

  useEffect(() => {
    const timer = setInterval(() => setTime(new Date()), 1000);
    return () => clearInterval(timer);
  }, []);

  const roles = [
    { id: 'Triage Nurse', label: 'Triage Nurse', icon: Stethoscope, desc: 'Intake & Vitals' },
    { id: 'Charge Nurse', label: 'Charge Nurse', icon: Users, desc: 'Queue & Flow' },
    { id: 'Clinical Lead', label: 'Clinical Lead', icon: ShieldCheck, desc: 'Safety & Audit' },
  ];

  return (
    <header className="border-b border-clinical-200 dark:border-clinical-800 bg-white/95 dark:bg-clinical-950/95 backdrop-blur sticky top-0 z-50 transition-colors">
      {/* Top Banner Bar */}
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-3.5 flex flex-wrap items-center justify-between gap-4">
        {/* Hospital Branding */}
        <div className="flex items-center gap-3.5">
          <div className="w-10 h-10 rounded-xl bg-brand-500/15 border border-brand-500/30 flex items-center justify-center text-brand-600 dark:text-brand-400 shadow-sm">
            <Activity className="w-6 h-6 animate-pulse" />
          </div>
          <div>
            <div className="flex items-center gap-2">
              <h1 className="text-lg font-black tracking-tight text-clinical-900 dark:text-white flex items-center gap-1">
                PatientTriage<span className="text-brand-600 dark:text-brand-400">.ai</span>
              </h1>
              <span className="text-[10px] uppercase font-black tracking-wider px-2 py-0.5 rounded bg-brand-50 dark:bg-brand-950/80 text-brand-700 dark:text-brand-300 border border-brand-200 dark:border-brand-500/30">
                Hospital Command Center
              </span>
            </div>
            <p className="text-xs text-clinical-500 dark:text-clinical-400 font-medium">
              Emergency Department · Trauma Center Pavilion
            </p>
          </div>
        </div>

        {/* Telemetry & Controls */}
        <div className="flex items-center gap-3 flex-wrap">
          {/* Surge Toggle */}
          <button
            onClick={() => setSurge(!surgeActive)}
            className={`px-3.5 py-1.5 rounded-xl text-xs font-black transition-all flex items-center gap-2 border shadow-xs ${
              surgeActive
                ? 'bg-red-600 text-white border-red-500 animate-pulse shadow-red-500/30'
                : 'bg-clinical-50 dark:bg-clinical-900 text-clinical-700 dark:text-clinical-300 border-clinical-200 dark:border-clinical-700 hover:border-brand-400'
            }`}
          >
            <Flame className={`w-4 h-4 ${surgeActive ? 'text-yellow-300' : 'text-clinical-400'}`} />
            <span>{surgeActive ? `Surge Mode (${surgeFactor}×)` : 'Normal Load'}</span>
          </button>

          {/* Engine Status */}
          <div className="flex items-center gap-2 px-3 py-1.5 rounded-xl bg-emerald-50 dark:bg-emerald-950/40 border border-emerald-200 dark:border-emerald-500/30 text-emerald-700 dark:text-emerald-400 text-xs font-bold">
            <span className="w-2 h-2 rounded-full bg-emerald-500 animate-ping"></span>
            <span className="hidden sm:inline">Engine Active</span>
          </div>

          {/* Digital Clock */}
          <div className="flex items-center gap-1.5 px-3 py-1.5 rounded-xl bg-clinical-50 dark:bg-clinical-900 border border-clinical-200 dark:border-clinical-800 text-clinical-600 dark:text-clinical-300 text-xs font-mono font-bold">
            <Clock className="w-3.5 h-3.5 text-clinical-400" />
            <span>{time.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit', second: '2-digit' })}</span>
          </div>

          {/* Theme Toggle (Light / Dark) */}
          <button
            onClick={() => setDarkMode(!darkMode)}
            className="p-2 rounded-xl bg-clinical-50 dark:bg-clinical-900 border border-clinical-200 dark:border-clinical-800 text-clinical-600 dark:text-clinical-300 hover:text-brand-600 transition-all shadow-xs"
            title={darkMode ? "Switch to Clean Light Theme" : "Switch to Dark Command Theme"}
          >
            {darkMode ? <Sun className="w-4 h-4 text-amber-400" /> : <Moon className="w-4 h-4 text-clinical-600" />}
          </button>
        </div>
      </div>

      {/* Role Navigation Bar */}
      <div className="bg-clinical-50/70 dark:bg-clinical-900/60 border-t border-clinical-200 dark:border-clinical-800/80 px-4 sm:px-6 lg:px-8">
        <div className="max-w-7xl mx-auto flex items-center justify-between">
          <nav className="flex space-x-1 sm:space-x-2 py-1.5">
            {roles.map((role) => {
              const Icon = role.icon;
              const isActive = currentRole === role.id;
              return (
                <button
                  key={role.id}
                  onClick={() => setRole(role.id)}
                  className={`flex items-center gap-2 px-3.5 py-1.5 rounded-xl text-xs font-black transition-all ${
                    isActive
                      ? 'bg-white dark:bg-clinical-800 text-brand-700 dark:text-brand-300 border border-brand-300 dark:border-brand-500/50 shadow-xs'
                      : 'text-clinical-500 dark:text-clinical-400 hover:text-clinical-900 dark:hover:text-white'
                  }`}
                >
                  <Icon className={`w-4 h-4 ${isActive ? 'text-brand-600 dark:text-brand-400' : 'text-clinical-400'}`} />
                  <span>{role.label}</span>
                  <span className="hidden md:inline text-[10px] font-medium text-clinical-400">
                    ({role.desc})
                  </span>
                </button>
              );
            })}
          </nav>

          <div className="hidden lg:flex items-center">
            <button
              onClick={onVerifyChain}
              className="text-[11px] font-bold text-clinical-500 dark:text-clinical-400 hover:text-brand-600 dark:hover:text-brand-300 flex items-center gap-1.5 transition-colors"
            >
              <ShieldCheck className="w-4 h-4 text-brand-600 dark:text-brand-400" />
              <span>SHA-256 Audit Intact</span>
            </button>
          </div>
        </div>
      </div>
    </header>
  );
}
