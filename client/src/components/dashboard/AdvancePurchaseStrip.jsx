import React, { useState } from 'react';
import { Calendar, Clock, AlertCircle, Info, ChevronRight, BarChart2, ShieldAlert } from 'lucide-react';

const HORIZONS = [
  {
    horizon: 'T+1',
    label: 'Emergency / Tatkal',
    leadTime: '24-48 Hours',
    avgFare: '₹8,450',
    surge: '+82.2%',
    surgeLevel: 'severe',
    basketWeight: '12.5%',
    volatility: '±24.8%',
    consumerGroup: 'Urgent medical, family emergency, sudden executive travel',
    description: 'Manual CPI offices completely miss these extreme surge fares as they only collect advance quotes during business hours.'
  },
  {
    horizon: 'T+7',
    label: 'Weekly Business',
    leadTime: '5-7 Days',
    avgFare: '₹6,720',
    surge: '+45.5%',
    surgeLevel: 'high',
    basketWeight: '28.0%',
    volatility: '±14.2%',
    consumerGroup: 'Corporate & SME weekly travelers, inter-city consultations',
    description: 'High price-inelasticity window where algorithmic revenue management systems push seat tiers aggressively.'
  },
  {
    horizon: 'T+15',
    label: 'Mid-Advance Window',
    leadTime: '14-16 Days',
    avgFare: '₹5,540',
    surge: '+18.2%',
    surgeLevel: 'moderate',
    basketWeight: '32.5%',
    volatility: '±7.6%',
    consumerGroup: 'Planned business meetings, personal & visiting friends/relatives',
    description: 'Represents the modal median booking day for domestic Indian aviation passengers according to DGCA traffic filings.'
  },
  {
    horizon: 'T+30',
    label: 'Standard Advance',
    leadTime: '28-32 Days',
    avgFare: '₹4,680',
    surge: '+8.0%',
    surgeLevel: 'low',
    basketWeight: '18.0%',
    volatility: '±4.1%',
    consumerGroup: 'Vacations, scheduled conferences, festival bookings',
    description: 'Baseline consumer bucket where promotional fares and low bucket tiers (e.g. IndiGo Saver, Akasa Saver) remain open.'
  },
  {
    horizon: 'T+45',
    label: 'Long-Horizon Base',
    leadTime: '40-45 Days',
    avgFare: '₹4,210',
    surge: '1.00× (Base)',
    surgeLevel: 'base',
    basketWeight: '9.0%',
    volatility: '±2.0%',
    consumerGroup: 'Leisure family travel, planned annual leaves, school holidays',
    description: 'Econometric anchor point with maximum seat inventory availability and unconstrained fare class choice.'
  }
];

export const AdvancePurchaseStrip = () => {
  const [selectedHorizon, setSelectedHorizon] = useState(HORIZONS[0]);

  return (
    <div className="bg-white border border-slate-200/90 rounded-xl p-5 shadow-2xs">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2 border-b border-slate-100 pb-3">
        <div>
          <div className="flex items-center gap-2">
            <h2 className="text-sm font-bold text-slate-900 tracking-tight flex items-center gap-1.5">
              <Calendar className="w-4 h-4 text-blue-600" />
              Dynamic Pricing Yield Curve by Advance Booking Horizon
            </h2>
            <span className="bg-blue-50 text-blue-700 text-[10px] font-bold px-2 py-0.5 rounded border border-blue-200/60">
              T+1 to T+45 Window
            </span>
          </div>
          <p className="text-[11px] text-slate-500 mt-0.5">
            Explaining why manual monthly sampling fails: Same domestic sector swings by up to <strong className="text-slate-800">+82.2%</strong> across booking lead times.
          </p>
        </div>

        <span className="text-[11px] text-slate-400 font-medium">
          Click any horizon for econometric breakdown
        </span>
      </div>

      {/* 5-Column Horizon Cards Grid */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-5 gap-3 mt-4">
        {HORIZONS.map((item) => {
          const isSelected = selectedHorizon.horizon === item.horizon;

          const getBadgeStyle = () => {
            switch (item.surgeLevel) {
              case 'severe':
                return 'bg-red-50 text-red-700 border-red-200';
              case 'high':
                return 'bg-amber-50 text-amber-700 border-amber-200';
              case 'moderate':
                return 'bg-blue-50 text-blue-700 border-blue-200';
              case 'low':
                return 'bg-emerald-50 text-emerald-700 border-emerald-200';
              default:
                return 'bg-slate-50 text-slate-700 border-slate-200';
            }
          };

          return (
            <div
              key={item.horizon}
              onClick={() => setSelectedHorizon(item)}
              className={`rounded-xl p-3.5 border transition-all cursor-pointer flex flex-col justify-between ${
                isSelected
                  ? 'border-blue-600 bg-blue-50/40 shadow-sm ring-1 ring-blue-600/30'
                  : 'border-slate-200/90 bg-white hover:border-slate-300 hover:shadow-2xs'
              }`}
            >
              <div>
                <div className="flex items-center justify-between">
                  <span className="text-xs font-black text-slate-900 font-mono">
                    {item.horizon}
                  </span>
                  <span className={`text-[10px] font-bold px-1.5 py-0.5 rounded border ${getBadgeStyle()}`}>
                    {item.surge}
                  </span>
                </div>

                <div className="mt-2">
                  <span className="text-[11px] font-semibold text-slate-600 block">
                    {item.label}
                  </span>
                  <span className="text-lg font-extrabold text-slate-900 block mt-0.5">
                    {item.avgFare}
                  </span>
                </div>
              </div>

              <div className="mt-3 pt-2.5 border-t border-slate-100/90 flex items-center justify-between text-[10px] text-slate-500">
                <span>Weight: <strong className="text-slate-800">{item.basketWeight}</strong></span>
                <span className="text-slate-400 font-mono">{item.volatility}</span>
              </div>
            </div>
          );
        })}
      </div>

      {/* Selected Horizon Deep-Dive Callout */}
      <div className="mt-4 bg-slate-50 border border-slate-200/80 rounded-xl p-3.5 flex flex-col md:flex-row items-start md:items-center justify-between gap-4">
        <div className="flex items-start gap-3">
          <div className="p-2 rounded-lg bg-blue-600 text-white font-mono font-bold text-xs shrink-0 mt-0.5">
            {selectedHorizon.horizon}
          </div>
          <div>
            <div className="flex flex-wrap items-center gap-2">
              <span className="text-xs font-bold text-slate-900">
                {selectedHorizon.label} ({selectedHorizon.leadTime})
              </span>
              <span className="text-[10px] bg-slate-200 text-slate-700 px-1.5 py-0.5 rounded font-medium">
                Basket Weight: {selectedHorizon.basketWeight}
              </span>
              <span className="text-[10px] bg-slate-200 text-slate-700 px-1.5 py-0.5 rounded font-medium">
                Volatility: {selectedHorizon.volatility}
              </span>
            </div>
            <p className="text-[11px] text-slate-600 mt-1">
              <strong className="text-slate-800">Consumer Segment:</strong> {selectedHorizon.consumerGroup}
            </p>
            <p className="text-[11px] text-slate-500 mt-0.5 italic">
              "{selectedHorizon.description}"
            </p>
          </div>
        </div>

        <div className="shrink-0 flex items-center gap-2 self-end md:self-auto">
          <div className="text-right">
            <span className="text-[10px] text-slate-400 uppercase font-bold block">Weighted Avg Fare</span>
            <span className="text-base font-extrabold text-blue-700">{selectedHorizon.avgFare}</span>
          </div>
        </div>
      </div>
    </div>
  );
};
