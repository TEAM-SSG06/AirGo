import React, { useState } from 'react';
import { Plane, Activity, BarChart3, Database, Search, ArrowRight, ShieldCheck, Sparkles } from 'lucide-react';

function App() {
  const [selectedRoute, setSelectedRoute] = useState('DEL-BOM');

  return (
    <div className="min-h-screen bg-slate-950 text-slate-100 flex flex-col font-sans">
      {/* Top Navbar */}
      <header className="border-b border-slate-800 bg-slate-900/60 backdrop-blur-md sticky top-0 z-50">
        <div className="max-w-7xl mx-auto px-6 h-16 flex items-center justify-between">
          <div className="flex items-center gap-3">
            <div className="w-10 h-10 rounded-xl bg-gradient-to-tr from-brand-600 to-brand-400 flex items-center justify-center shadow-lg shadow-brand-500/20">
              <Plane className="w-5 h-5 text-white" />
            </div>
            <div>
              <div className="flex items-center gap-2">
                <span className="font-bold text-lg tracking-tight text-white">AirGo</span>
                <span className="text-[10px] uppercase font-semibold tracking-wider bg-brand-500/20 text-brand-400 border border-brand-500/30 px-2 py-0.5 rounded-full">
                  CPI Inflation Engine
                </span>
              </div>
              <p className="text-xs text-slate-400">MoSPI / NSO Real-time Airfare Price Index (APIx)</p>
            </div>
          </div>

          <div className="flex items-center gap-4">
            <div className="flex items-center gap-2 text-xs text-slate-400 bg-slate-800/80 border border-slate-700/60 px-3 py-1.5 rounded-lg">
              <span className="w-2 h-2 rounded-full bg-emerald-400 animate-pulse"></span>
              Live Scrapers Active
            </div>
          </div>
        </div>
      </header>

      {/* Main Content Area */}
      <main className="max-w-7xl mx-auto px-6 py-8 flex-1 w-full space-y-8">
        {/* Hero / Overview Banner */}
        <div className="relative overflow-hidden rounded-2xl bg-gradient-to-r from-brand-950 via-slate-900 to-slate-900 border border-brand-800/40 p-8 shadow-2xl">
          <div className="relative z-10 max-w-2xl space-y-3">
            <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full bg-brand-500/10 border border-brand-500/20 text-brand-400 text-xs font-medium">
              <Sparkles className="w-3.5 h-3.5" /> Next-Gen High Frequency Retail Price Index
            </div>
            <h1 className="text-3xl font-extrabold text-white tracking-tight">
              Real-Time Airfare Price Index Dashboard
            </h1>
            <p className="text-slate-300 text-sm leading-relaxed">
              Multi-source automated web scraping engine monitoring Cleartrip, EaseMyTrip, Google Flights, and scheduled airlines across representative DGCA city pairs.
            </p>
          </div>
        </div>

        {/* Stats Grid */}
        <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
          {[
            { label: 'Current APIx Index', value: '118.42', change: '+3.14% WoW', icon: Activity, color: 'text-brand-400' },
            { label: 'Active Routes Monitored', value: '15 Sectors', change: 'DGCA High Traffic', icon: Plane, color: 'text-emerald-400' },
            { label: 'Advance Windows', value: 'T+1 to T+45', change: '5 Purchase Horizons', icon: BarChart3, color: 'text-indigo-400' },
            { label: 'Live Data Sources', value: 'Cleartrip & EaseMyTrip', change: '100% Real DOM Quotes', icon: Database, color: 'text-amber-400' },
          ].map((stat, idx) => (
            <div key={idx} className="bg-slate-900/80 border border-slate-800 p-5 rounded-xl hover:border-slate-700 transition-all">
              <div className="flex items-center justify-between text-slate-400 mb-2">
                <span className="text-xs font-medium uppercase tracking-wider">{stat.label}</span>
                <stat.icon className={`w-4 h-4 ${stat.color}`} />
              </div>
              <div className="text-2xl font-bold text-white">{stat.value}</div>
              <div className="text-xs text-slate-400 mt-1">{stat.change}</div>
            </div>
          ))}
        </div>
      </main>

      {/* Footer */}
      <footer className="border-t border-slate-900 bg-slate-950 py-6 text-center text-xs text-slate-500">
        AirGo Platform • Ministry of Statistics and Programme Implementation (MoSPI) CPI Modernization Framework
      </footer>
    </div>
  );
}

export default App;
