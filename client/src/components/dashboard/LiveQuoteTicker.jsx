import React, { useState } from 'react';
import { Radio, ArrowUpRight, ArrowDownRight, RefreshCw, Zap, ShieldCheck } from 'lucide-react';

const LIVE_QUOTES = [
  { id: 1, flight: '6E-204', carrier: 'IndiGo', route: 'DEL → BOM', fare: '₹4,890', change: '-2.1%', isUp: false, horizon: 'T+7', time: '1m ago' },
  { id: 2, flight: 'AI-887', carrier: 'Air India', route: 'BOM → BLR', fare: '₹5,120', change: '+1.4%', isUp: true, horizon: 'T+15', time: '2m ago' },
  { id: 3, flight: 'QP-1312', carrier: 'Akasa Air', route: 'DEL → BLR', fare: '₹4,350', change: '-0.8%', isUp: false, horizon: 'T+30', time: '3m ago' },
  { id: 4, flight: 'SG-8169', carrier: 'SpiceJet', route: 'CCU → DEL', fare: '₹6,210', change: '+14.2%', isUp: true, horizon: 'T+1', time: '4m ago' },
  { id: 5, flight: '6E-512', carrier: 'IndiGo', route: 'HYD → DEL', fare: '₹5,450', change: '+3.2%', isUp: true, horizon: 'T+7', time: '5m ago' },
  { id: 6, flight: 'AI-541', carrier: 'Air India', route: 'MAA → DEL', fare: '₹7,890', change: '+8.6%', isUp: true, horizon: 'T+1', time: '6m ago' },
  { id: 7, flight: 'QP-1402', carrier: 'Akasa Air', route: 'AMD → BOM', fare: '₹3,450', change: '-1.5%', isUp: false, horizon: 'T+15', time: '7m ago' },
  { id: 8, flight: '6E-678', carrier: 'IndiGo', route: 'BLR → GOI', fare: '₹3,920', change: '+0.5%', isUp: true, horizon: 'T+30', time: '8m ago' },
];

export const LiveQuoteTicker = () => {
  const [isPaused, setIsPaused] = useState(false);

  return (
    <div className="bg-slate-900 border border-slate-800 rounded-xl px-4 py-2.5 shadow-sm text-white flex flex-col md:flex-row items-center justify-between gap-3 overflow-hidden">
      {/* Live Badge and Label */}
      <div className="flex items-center gap-2.5 shrink-0">
        <div className="flex items-center gap-1.5 bg-emerald-500/20 border border-emerald-500/30 px-2.5 py-0.5 rounded-full">
          <span className="w-2 h-2 rounded-full bg-emerald-400 animate-ping"></span>
          <span className="text-[10px] font-bold text-emerald-300 uppercase tracking-wider">Live Stream</span>
        </div>
        <span className="text-xs font-semibold text-slate-300 hidden sm:inline">
          High-Frequency OTA & Airline Harvest Feed:
        </span>
      </div>

      {/* Scrolling Stream / Flex Strip */}
      <div 
        className="flex-1 overflow-x-auto no-scrollbar w-full"
        onMouseEnter={() => setIsPaused(true)}
        onMouseLeave={() => setIsPaused(false)}
      >
        <div className="flex items-center gap-3 w-max">
          {LIVE_QUOTES.map((q) => (
            <div 
              key={q.id}
              className="bg-slate-800/80 hover:bg-slate-800 border border-slate-700/70 rounded-lg px-3 py-1 flex items-center gap-2 text-xs transition-colors shrink-0"
            >
              <span className="font-bold text-slate-100">{q.route}</span>
              <span className="text-[10px] px-1 py-0.2 rounded bg-slate-700 text-slate-300 font-mono">
                {q.horizon}
              </span>
              <span className="font-extrabold text-white">{q.fare}</span>
              <span className={`text-[10px] font-bold flex items-center ${q.isUp ? 'text-red-400' : 'text-emerald-400'}`}>
                {q.isUp ? <ArrowUpRight className="w-3 h-3" /> : <ArrowDownRight className="w-3 h-3" />}
                {q.change}
              </span>
              <span className="text-[9px] text-slate-400">{q.carrier}</span>
            </div>
          ))}
        </div>
      </div>

      {/* Status Cadence */}
      <div className="shrink-0 flex items-center gap-2 text-[10px] text-slate-400 font-medium">
        <span className="inline-block w-1.5 h-1.5 rounded-full bg-blue-400"></span>
        <span>15m auto-sync</span>
      </div>
    </div>
  );
};
