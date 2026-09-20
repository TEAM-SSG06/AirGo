import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { LiveQuoteTicker } from '../components/dashboard/LiveQuoteTicker';
import { ExecutiveHeroBanner } from '../components/dashboard/ExecutiveHeroBanner';
import { AdvancePurchaseStrip } from '../components/dashboard/AdvancePurchaseStrip';
import { MetricCards } from '../components/dashboard/MetricCards';
import { HistoricalTrendChart } from '../components/dashboard/HistoricalTrendChart';
import { DomesticFareMovement } from '../components/dashboard/DomesticFareMovement';
import { FarePressureGauge } from '../components/dashboard/FarePressureGauge';
import { RoutesInflationTable } from '../components/dashboard/RoutesInflationTable';
import { PassengerDemandChart } from '../components/dashboard/PassengerDemandChart';
import { KeyInsights } from '../components/dashboard/KeyInsights';
import { Filter, Layers, Compass, TrendingUp, Sparkles, ExternalLink } from 'lucide-react';

export const DashboardPage = () => {
  const navigate = useNavigate();
  const [selectedTier, setSelectedTier] = useState('all');

  const TIERS = [
    { id: 'all', label: 'All 486 Domestic Sectors', count: '486 Routes' },
    { id: 'metro', label: 'Metro-to-Metro (Tier 1 Trunk)', count: '48 Routes • 38.4% Pax' },
    { id: 'tier2', label: 'Metro to Non-Metro (Tier 2)', count: '186 Routes' },
    { id: 'udan', label: 'UDAN Regional Connectivity', count: '252 Routes' }
  ];

  return (
    <div className="space-y-6 animate-in fade-in duration-200">
      {/* 1. Real-Time Flight Quotes Stream Ticker */}
      <LiveQuoteTicker />

      {/* 2. Executive Mandate & Index Hero Banner */}
      <ExecutiveHeroBanner />

      {/* 3. Section Divider & Quick Sector Filter Bar */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 bg-white border border-slate-200/90 rounded-xl p-3 shadow-2xs">
        <div className="flex items-center gap-2">
          <div className="p-1.5 rounded-lg bg-blue-50 text-blue-600 border border-blue-100">
            <Layers className="w-4 h-4" />
          </div>
          <div>
            <span className="text-xs font-bold text-slate-900 block">
              Market Sector Focus:
            </span>
            <span className="text-[11px] text-slate-500">
              Filter aggregation scope across DGCA route tiers
            </span>
          </div>
        </div>

        {/* Tier Selector Pills */}
        <div className="flex flex-wrap items-center gap-1.5">
          {TIERS.map((tier) => {
            const isActive = selectedTier === tier.id;
            return (
              <button
                key={tier.id}
                onClick={() => setSelectedTier(tier.id)}
                className={`text-xs px-3 py-1.5 rounded-lg font-medium transition-all cursor-pointer flex items-center gap-1.5 ${
                  isActive
                    ? 'bg-blue-600 text-white font-semibold shadow-xs'
                    : 'bg-slate-100/80 hover:bg-slate-200/80 text-slate-700'
                }`}
              >
                <span>{tier.label}</span>
                <span className={`text-[10px] px-1 py-0.2 rounded font-mono ${isActive ? 'bg-blue-700 text-blue-100' : 'bg-slate-200 text-slate-600'}`}>
                  {tier.count.split(' ')[0]}
                </span>
              </button>
            );
          })}
        </div>
      </div>

      {/* 4. Top 6 High-Frequency KPI Metric Cards */}
      <div>
        <div className="flex items-center justify-between mb-2.5 px-1">
          <h3 className="text-xs font-bold uppercase tracking-wider text-slate-500 flex items-center gap-1.5">
            <TrendingUp className="w-3.5 h-3.5 text-blue-600" />
            Executive Macro Indicators
          </h3>
          <span className="text-[11px] text-slate-400 font-medium">
            Updated today at 23:15 IST
          </span>
        </div>
        <MetricCards />
      </div>

      {/* 5. Dynamic Pricing Horizon Strip: T+1 to T+45 (Core SIH Problem Statement Proof) */}
      <AdvancePurchaseStrip />

      {/* 6. India Airfare Index - Historical Trend Area Chart */}
      <HistoricalTrendChart />

      {/* 7. 2-Column Row: Domestic Fare Movement & Fare Pressure */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <DomesticFareMovement />
        <FarePressureGauge />
      </div>

      {/* 8. Routes Driving Airfare Inflation Table */}
      <RoutesInflationTable onNavigateRoutes={() => navigate('/route-intelligence')} />

      {/* 9. Passenger Demand by Route Horizontal Bar Chart */}
      <PassengerDemandChart onNavigateDemand={() => navigate('/passenger-demand')} />

      {/* 10. Key Insights AI Briefing Cards */}
      <KeyInsights onNavigateAnalysis={() => navigate('/route-intelligence')} />
    </div>
  );
};
