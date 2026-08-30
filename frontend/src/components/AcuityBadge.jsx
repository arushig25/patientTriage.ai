import React from 'react';

export const ACUITY_CONFIG = {
  1: {
    label: 'Resuscitation',
    desc: 'Immediate life-threatening emergency',
    badge: 'bg-red-500/20 text-red-400 border-red-500/40 shadow-red-500/20',
    banner: 'from-red-950/70 to-red-900/30 border-red-500 text-red-200',
    text: 'text-red-400',
    accent: '#EF4444',
  },
  2: {
    label: 'Emergent',
    desc: 'Immediate physician assessment required',
    badge: 'bg-orange-500/20 text-orange-400 border-orange-500/40 shadow-orange-500/20',
    banner: 'from-orange-950/70 to-orange-900/30 border-orange-500 text-orange-200',
    text: 'text-orange-400',
    accent: '#F97316',
  },
  3: {
    label: 'Urgent',
    desc: 'Timely assessment (< 30 min target)',
    badge: 'bg-amber-500/20 text-amber-400 border-amber-500/40 shadow-amber-500/20',
    banner: 'from-amber-950/70 to-amber-900/30 border-amber-500 text-amber-200',
    text: 'text-amber-400',
    accent: '#F59E0B',
  },
  4: {
    label: 'Less Urgent',
    desc: 'Standard department care stream',
    badge: 'bg-emerald-500/20 text-emerald-400 border-emerald-500/40 shadow-emerald-500/20',
    banner: 'from-emerald-950/70 to-emerald-900/30 border-emerald-500 text-emerald-200',
    text: 'text-emerald-400',
    accent: '#10B981',
  },
  5: {
    label: 'Non-Urgent',
    desc: 'Fast-track / minor injury clinic',
    badge: 'bg-blue-500/20 text-blue-400 border-blue-500/40 shadow-blue-500/20',
    banner: 'from-blue-950/70 to-blue-900/30 border-blue-500 text-blue-200',
    text: 'text-blue-400',
    accent: '#3B82F6',
  },
};

export default function AcuityBadge({ level, size = 'md', showDesc = false }) {
  const config = ACUITY_CONFIG[level] || ACUITY_CONFIG[5];
  
  if (size === 'sm') {
    return (
      <span className={`inline-flex items-center gap-1.5 px-2.5 py-0.5 rounded-full text-xs font-semibold border ${config.badge}`}>
        <span className="w-1.5 h-1.5 rounded-full bg-current"></span>
        L{level} · {config.label}
      </span>
    );
  }

  if (size === 'lg') {
    return (
      <div className={`p-4 rounded-xl border-l-4 border bg-gradient-to-r ${config.banner} shadow-lg flex items-center justify-between`}>
        <div className="flex items-center gap-4">
          <div className="font-mono text-4xl font-extrabold tracking-tight text-white flex items-center gap-2">
            <span>L{level}</span>
          </div>
          <div>
            <div className={`text-base font-extrabold uppercase tracking-wider ${config.text}`}>
              Level {level} — {config.label}
            </div>
            <div className="text-sm font-medium text-slate-200 mt-0.5">
              {config.desc}
            </div>
          </div>
        </div>
      </div>
    );
  }

  return (
    <span className={`inline-flex items-center gap-2 px-3 py-1 rounded-full text-xs font-bold tracking-wide border shadow-sm ${config.badge}`}>
      <span className="w-2 h-2 rounded-full bg-current animate-pulse"></span>
      LEVEL {level} · {config.label.toUpperCase()}
    </span>
  );
}
