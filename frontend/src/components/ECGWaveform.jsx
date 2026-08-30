import React from 'react';

export default function ECGWaveform({ hr = 75, isCritical = false, isWarning = false }) {
  const strokeColor = isCritical ? '#EF4444' : isWarning ? '#F97316' : '#10B981';
  
  return (
    <div className="relative h-9 w-24 overflow-hidden rounded bg-slate-900/60 border border-slate-700/50 flex items-center">
      <svg className="w-full h-full" viewBox="0 0 100 40" preserveAspectRatio="none">
        <path
          d="M 0 20 L 20 20 L 25 10 L 30 30 L 35 5 L 40 35 L 45 20 L 60 20 L 65 14 L 70 24 L 75 20 L 100 20"
          fill="none"
          stroke={strokeColor}
          strokeWidth="1.8"
          strokeLinecap="round"
          strokeLinejoin="round"
          className="animate-[pulse_1.5s_ease-in-out_infinite]"
        />
      </svg>
      <div className="absolute right-1 bottom-0.5 text-[9px] font-mono font-bold text-slate-400">
        {hr ? `${Math.round(hr)} bpm` : '---'}
      </div>
    </div>
  );
}
