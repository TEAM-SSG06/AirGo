import React from 'react';
import { useNavigate } from 'react-router-dom';
import { ExecutiveHeroBanner } from '../components/dashboard/ExecutiveHeroBanner';
import { AdvancePurchaseStrip } from '../components/dashboard/AdvancePurchaseStrip';
import { MetricCards } from '../components/dashboard/MetricCards';
import { HistoricalTrendChart } from '../components/dashboard/HistoricalTrendChart';
import { DomesticFareMovement } from '../components/dashboard/DomesticFareMovement';
import { FarePressureGauge } from '../components/dashboard/FarePressureGauge';
import { RoutesInflationTable } from '../components/dashboard/RoutesInflationTable';
import { PassengerDemandChart } from '../components/dashboard/PassengerDemandChart';
import { KeyInsights } from '../components/dashboard/KeyInsights';
import { TrendingUp } from 'lucide-react';

export const DashboardPage = () => {
  const navigate = useNavigate();

  return (
    <div className="space-y-6 animate-in fade-in duration-200">
      {/* Executive Mandate & Index Hero Banner */}
      <ExecutiveHeroBanner />

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
