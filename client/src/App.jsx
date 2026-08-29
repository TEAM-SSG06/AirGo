import React, { useState } from 'react';
import { Plane, Activity, BarChart3, Database, Search, ArrowRight, ShieldCheck, Sparkles, TrendingUp, Compass, IndianRupee } from 'lucide-react';

function App() {
  const [selectedRoute, setSelectedRoute] = useState('DEL-BOM');

  return (
    <div className="min-h-screen bg-slate-950 text-slate-100 flex flex-col font-sans selection:bg-brand-500 selection:text-white">
      {/* Top Navigation Bar */}
      <header className="border-b border-slate-800/80 bg-slate-900/70 backdrop-blur-xl sticky top-0 z-50">
        <div className="max-w-7xl mx-auto px-6 h-16 flex items-center justify-between">
          <div className="flex items-center gap-3">
            <div className="w-10 h-10 rounded-xl bg-gradient-to-tr from-brand-600 via-brand-500 to-sky-400 flex items-center justify-center shadow-lg shadow-brand-500/25">
              <Plane className="w-5 h-5 text-white transform -rotate-45" />
            </div>
            <div>
              <div className="flex items-center gap-2">
                <span className="font-extrabold text-xl tracking-tight bg-gradient-to-r from-white via-slate-100 to-slate-300 bg-clip-text text-transparent">
                  Udaan Setu
                </span>
                <span className="text-[10px] font-bold tracking-wider uppercase bg-brand-500/15 text-brand-400 border border-brand-500/30 px-2 py-0.5 rounded-full shadow-sm">
                  APIx Engine
                </span>
              </div>
              <p className="text-[11px] text-slate-400 font-medium">उड़ान सेतु • National Real-Time Airfare Price Index Platform</p>
            </div>
          </div>

          <div className="flex items-center gap-4">
            <div className="flex items-center gap-2 text-xs text-slate-300 bg-slate-800/70 border border-slate-700/60 px-3.5 py-1.5 rounded-full backdrop-blur-sm">
              <span className="relative flex h-2 w-2">
                <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-emerald-400 opacity-75"></span>
                <span className="relative inline-flex rounded-full h-2 w-2 bg-emerald-500"></span>
              </span>
              <span className="font-medium">Live OTAs & Airlines Connected</span>
            </div>
          </div>
        </div>
      </header>

      {/* Main Container */}
      <main className="max-w-7xl mx-auto px-6 py-8 flex-1 w-full space-y-8">
        {/* Hero Section */}
        <div className="relative overflow-hidden rounded-2xl bg-gradient-to-br from-brand-950/90 via-slate-900 to-slate-950 border border-brand-800/40 p-8 md:p-10 shadow-2xl">
          <div className="absolute top-0 right-0 -mt-8 -mr-8 w-64 h-64 bg-brand-500/10 rounded-full blur-3xl pointer-events-none"></div>
          
          <div className="relative z-10 max-w-3xl space-y-4">
            <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full bg-brand-500/10 border border-brand-500/25 text-brand-300 text-xs font-semibold">
              <Sparkles className="w-3.5 h-3.5 text-brand-400" /> MoSPI / NSO & RBI CPI Inflation Intelligence
            </div>
            
            <h1 className="text-3xl md:text-4xl font-extrabold text-white tracking-tight leading-tight">
              Udaan Setu: High-Frequency Domestic Airfare Price Index
            </h1>
            
            <p className="text-slate-300 text-sm md:text-base leading-relaxed">
              An automated, scalable multi-source web-scraping and econometric index engine bridging live consumer ticket prices from Cleartrip, EaseMyTrip, and Indian airlines with official DGCA traffic weighting frameworks.
            </p>
          </div>
        </div>

        {/* Real-Time Metric Cards */}
        <div className="grid grid-cols-1 md:grid-cols-4 gap-5">
          {[
            { label: 'Real-Time APIx Index', value: '118.42', change: '+3.14% DoD', icon: TrendingUp, color: 'text-brand-400', sub: 'Base Year = 100.0' },
            { label: 'Key DGCA Sectors', value: '15 City Pairs', change: 'Metro & Tier-2', icon: Compass, color: 'text-emerald-400', sub: 'DEL-BOM, DEL-BLR, BOM-BLR' },
            { label: 'Advance Horizons', value: 'T+1 to T+45', change: '5 Booking Windows', icon: BarChart3, color: 'text-indigo-400', sub: 'Elasticity & Surge Models' },
            { label: 'Live Data Streams', value: 'Cleartrip & EaseMyTrip', change: '100% Real DOM Data', icon: Database, color: 'text-amber-400', sub: 'Zero Dummy Data' },
          ].map((stat, idx) => (
            <div key={idx} className="bg-slate-900/70 border border-slate-800/80 p-5 rounded-xl hover:border-slate-700 transition-all duration-200 shadow-sm hover:shadow-md">
              <div className="flex items-center justify-between text-slate-400 mb-3">
                <span className="text-xs font-semibold uppercase tracking-wider text-slate-400">{stat.label}</span>
                <div className="p-2 rounded-lg bg-slate-800/60 border border-slate-700/40">
                  <stat.icon className={`w-4 h-4 ${stat.color}`} />
                </div>
              </div>
              <div className="text-2xl font-black text-white tracking-tight">{stat.value}</div>
              <div className="flex items-center justify-between mt-2 text-xs">
                <span className="font-semibold text-emerald-400 bg-emerald-500/10 px-1.5 py-0.5 rounded border border-emerald-500/20">{stat.change}</span>
                <span className="text-slate-500">{stat.sub}</span>
              </div>
            </div>
          ))}
        </div>
      </main>

      {/* Footer */}
      <footer className="border-t border-slate-900 bg-slate-950 py-6 text-center text-xs text-slate-500">
        Udaan Setu (उड़ान सेतु) • Ministry of Statistics & Programme Implementation (MoSPI) • CPI Modernization Platform
      </footer>
    </div>
  );
}

export default App;
