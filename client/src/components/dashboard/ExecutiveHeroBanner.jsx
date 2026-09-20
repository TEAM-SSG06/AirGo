import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { 
  Building2, 
  TrendingUp, 
  Activity, 
  Download, 
  ArrowRight, 
  Layers, 
  Cpu, 
  FileText,
  ShieldCheck,
  CheckCircle2,
  Share2
} from 'lucide-react';

export const ExecutiveHeroBanner = () => {
  const navigate = useNavigate();
  const [downloaded, setDownloaded] = useState(false);

  const handleExportBriefing = () => {
    setDownloaded(true);
    const summary = {
      title: "National Airfare Price Index (APIx) - Executive Briefing",
      timestamp: new Date().toISOString(),
      indexValue: 128.6,
      baseYear: "Jan 2024 = 100.0",
      routesMonitored: 486,
      passengerTraffic: "12.84 Cr",
      spreadVsDgca: "+2.3 pts",
      keyFindings: [
        "Dynamic pricing causes +82.2% surge at T+1 vs T+45 baseline",
        "Top 5 trunk routes account for 38.4% of all passenger traffic",
        "Empirical high-frequency index eliminates 30-day manual CPI lag"
      ]
    };
    const blob = new Blob([JSON.stringify(summary, null, 2)], { type: "application/json" });
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = `APIx_Executive_Briefing_${new Date().toISOString().split('T')[0]}.json`;
    a.click();
    URL.revokeObjectURL(url);
    setTimeout(() => setDownloaded(false), 3000);
  };

  return (
    <div className="bg-gradient-to-br from-slate-900 via-slate-800 to-blue-950 rounded-2xl p-6 text-white shadow-lg border border-slate-700/60 relative overflow-hidden">
      {/* Background Decorative Rings */}
      <div className="absolute -right-20 -top-20 w-80 h-80 rounded-full bg-blue-500/10 blur-3xl pointer-events-none"></div>
      <div className="absolute right-1/3 -bottom-24 w-60 h-60 rounded-full bg-indigo-500/10 blur-2xl pointer-events-none"></div>

      <div className="relative z-10 flex flex-col lg:flex-row items-start lg:items-center justify-between gap-6">
        {/* Left Column: Title & Mission */}
        <div className="space-y-3 max-w-2xl">
          {/* Institutional Badges */}
          <div className="flex flex-wrap items-center gap-2">
            <span className="inline-flex items-center gap-1.5 bg-blue-500/20 border border-blue-400/30 text-blue-300 text-[11px] font-bold px-2.5 py-1 rounded-full backdrop-blur-sm">
              <Building2 className="w-3.5 h-3.5" />
              MoSPI & DGCA Regulatory Framework
            </span>
            <span className="inline-flex items-center gap-1 bg-emerald-500/20 border border-emerald-400/30 text-emerald-300 text-[11px] font-semibold px-2.5 py-1 rounded-full">
              <ShieldCheck className="w-3.5 h-3.5" />
              SIH26056 Live Implementation
            </span>
            <span className="text-[11px] text-slate-400 font-mono">
              Base: Jan 2024 = 100.0
            </span>
          </div>

          {/* Heading */}
          <div>
            <h1 className="text-xl sm:text-2xl font-black tracking-tight text-white flex items-center gap-2.5">
              National Airfare Price Index (APIx)
            </h1>
            <p className="text-xs sm:text-sm text-slate-300 mt-1 leading-relaxed">
              High-frequency multi-channel index capturing dynamic pricing variance (<span className="text-blue-300 font-semibold">T+1 to T+45</span>), unbundled surcharges, and seat scarcity across 486 domestic routes for real-time National Accounts & RBI Monetary Policy.
            </p>
          </div>

          {/* Live Metagroup Indicators */}
          <div className="flex flex-wrap items-center gap-4 pt-1 text-[11px] text-slate-300 font-medium">
            <div className="flex items-center gap-1.5">
              <span className="w-2 h-2 rounded-full bg-emerald-400"></span>
              <span>486 Monitored Sectors</span>
            </div>
            <div className="flex items-center gap-1.5">
              <span className="w-2 h-2 rounded-full bg-blue-400"></span>
              <span>2.84M Monthly Quotes</span>
            </div>
            <div className="flex items-center gap-1.5">
              <span className="w-2 h-2 rounded-full bg-indigo-400"></span>
              <span>Daily Geometric Jevons Index</span>
            </div>
          </div>
        </div>

        {/* Right Column: Quick Action Jumps & Index Snapshot */}
        <div className="flex flex-col sm:flex-row lg:flex-col items-stretch gap-3 w-full lg:w-auto shrink-0">
          {/* Quick Snapshot Card */}
          <div className="bg-white/5 border border-white/10 rounded-xl p-3.5 backdrop-blur-md flex items-center justify-between gap-6">
            <div>
              <span className="text-[10px] font-bold text-slate-400 uppercase tracking-wider block">
                Current National APIx
              </span>
              <div className="flex items-baseline gap-2 mt-0.5">
                <span className="text-2xl sm:text-3xl font-black text-white">128.6</span>
                <span className="text-xs font-bold text-emerald-400 flex items-center">
                  +1.8% MoM
                </span>
              </div>
            </div>
            <div className="text-right border-l border-white/10 pl-4">
              <span className="text-[10px] font-medium text-slate-400 block">Avg Domestic Fare</span>
              <span className="text-sm font-bold text-blue-200">₹6,842</span>
              <span className="text-[10px] text-slate-400 block mt-0.5">12.84 Cr Pax</span>
            </div>
          </div>

          {/* Navigation Action Buttons */}
          <div className="grid grid-cols-2 gap-2">
            <button
              onClick={() => navigate('/backtesting')}
              className="bg-blue-600 hover:bg-blue-500 text-white font-semibold text-xs py-2 px-3 rounded-lg shadow transition-all flex items-center justify-center gap-1.5 cursor-pointer group"
            >
              <TrendingUp className="w-3.5 h-3.5" />
              <span>30-Day Backtest</span>
              <ArrowRight className="w-3 h-3 group-hover:translate-x-0.5 transition-transform" />
            </button>

            <button
              onClick={() => navigate('/api-access')}
              className="bg-slate-800 hover:bg-slate-700 text-slate-100 font-semibold text-xs py-2 px-3 rounded-lg border border-slate-600 shadow transition-all flex items-center justify-center gap-1.5 cursor-pointer group"
            >
              <Cpu className="w-3.5 h-3.5 text-blue-400" />
              <span>Govt REST APIs</span>
              <ArrowRight className="w-3 h-3 group-hover:translate-x-0.5 transition-transform" />
            </button>
          </div>

          {/* Secondary Action */}
          <button
            onClick={handleExportBriefing}
            className="w-full bg-slate-800/60 hover:bg-slate-800 text-slate-300 hover:text-white text-[11px] font-medium py-1.5 px-3 rounded-lg border border-slate-700/60 flex items-center justify-center gap-1.5 transition-colors cursor-pointer"
          >
            {downloaded ? (
              <>
                <CheckCircle2 className="w-3.5 h-3.5 text-emerald-400" />
                <span className="text-emerald-300 font-semibold">Executive Briefing Downloaded!</span>
              </>
            ) : (
              <>
                <Download className="w-3.5 h-3.5" />
                <span>Export Executive Briefing (.JSON)</span>
              </>
            )}
          </button>
        </div>
      </div>
    </div>
  );
};
