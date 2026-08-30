import React from 'react';

export const ACUITY_CONFIG = {
  1: {
    label: 'Resuscitation',
    desc: 'Immediate life-threatening emergency',
    badge: 'bg-red-50 text-red-700 border-red-200 dark:bg-red-950/40 dark:text-red-300 dark:border-red-500/40',
    banner: 'bg-gradient-to-r from-red-50 via-rose-50 to-white border-red-400 text-red-900 dark:from-red-950/60 dark:via-red-900/30 dark:to-clinical-900 dark:border-red-500 dark:text-red-200',
    text: 'text-red-600 dark:text-red-400',
    accent: '#DC2626',
    dot: 'bg-red-500',
  },
  2: {
    label: 'Emergent',
    desc: 'Immediate physician assessment required',
    badge: 'bg-orange-50 text-orange-700 border-orange-200 dark:bg-orange-950/40 dark:text-orange-300 dark:border-orange-500/40',
    banner: 'bg-gradient-to-r from-orange-50 via-amber-50 to-white border-orange-400 text-orange-900 dark:from-orange-950/60 dark:via-orange-900/30 dark:to-clinical-900 dark:border-orange-500 dark:text-orange-200',
    text: 'text-orange-600 dark:text-orange-400',
    accent: '#EA580C',
    dot: 'bg-orange-500',
  },
  3: {
    label: 'Urgent',
    desc: 'Timely assessment (< 30 min target)',
    badge: 'bg-amber-50 text-amber-700 border-amber-200 dark:bg-amber-950/40 dark:text-amber-300 dark:border-amber-500/40',
    banner: 'bg-gradient-to-r from-amber-50 via-yellow-50 to-white border-amber-400 text-amber-900 dark:from-amber-950/60 dark:via-amber-900/30 dark:to-clinical-900 dark:border-amber-500 dark:text-amber-200',
    text: 'text-amber-600 dark:text-amber-400',
    accent: '#D97706',
    dot: 'bg-amber-500',
  },
  4: {
    label: 'Less Urgent',
    desc: 'Standard department care stream',
    badge: 'bg-emerald-50 text-emerald-700 border-emerald-200 dark:bg-emerald-950/40 dark:text-emerald-300 dark:border-emerald-500/40',
    banner: 'bg-gradient-to-r from-emerald-50 via-teal-50 to-white border-emerald-400 text-emerald-900 dark:from-emerald-950/60 dark:via-emerald-900/30 dark:to-clinical-900 dark:border-emerald-500 dark:text-emerald-200',
    text: 'text-emerald-600 dark:text-emerald-400',
    accent: '#059669',
    dot: 'bg-emerald-500',
  },
  5: {
    label: 'Non-Urgent',
    desc: 'Fast-track / minor injury clinic',
    badge: 'bg-blue-50 text-blue-700 border-blue-200 dark:bg-blue-950/40 dark:text-blue-300 dark:border-blue-500/40',
    banner: 'bg-gradient-to-r from-blue-50 via-indigo-50 to-white border-blue-400 text-blue-900 dark:from-blue-950/60 dark:via-blue-900/30 dark:to-clinical-900 dark:border-blue-500 dark:text-blue-200',
    text: 'text-blue-600 dark:text-blue-400',
    accent: '#2563EB',
    dot: 'bg-blue-500',
  },
};

export default function AcuityBadge({ level, size = 'md' }) {
  const config = ACUITY_CONFIG[level] || ACUITY_CONFIG[5];
  
  if (size === 'sm') {
    return (
      <span className={`inline-flex items-center gap-1.5 px-2.5 py-0.5 rounded-full text-xs font-bold border shadow-xs ${config.badge}`}>
        <span className={`w-1.5 h-1.5 rounded-full ${config.dot}`}></span>
        L{level} · {config.label}
      </span>
    );
  }

  if (size === 'lg') {
    return (
      <div className={`p-5 rounded-2xl border-l-[6px] border ${config.banner} shadow-sm flex items-center justify-between`}>
        <div className="flex items-center gap-4">
          <div className={`font-mono text-4xl sm:text-5xl font-black tracking-tight ${config.text}`}>
            L{level}
          </div>
          <div>
            <div className={`text-base sm:text-lg font-black uppercase tracking-wider ${config.text}`}>
              Level {level} — {config.label}
            </div>
            <div className="text-xs sm:text-sm font-semibold text-clinical-700 dark:text-clinical-300 mt-0.5">
              {config.desc}
            </div>
          </div>
        </div>
      </div>
    );
  }

  return (
    <span className={`inline-flex items-center gap-2 px-3 py-1 rounded-full text-xs font-black tracking-wider border shadow-xs ${config.badge}`}>
      <span className={`w-2 h-2 rounded-full ${config.dot} animate-pulse`}></span>
      LEVEL {level} · {config.label.toUpperCase()}
    </span>
  );
}
