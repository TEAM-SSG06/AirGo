import React, { useState } from 'react';
import { useLocation } from 'react-router-dom';
import { useFilters } from '../../context/FilterContext';
import { 
  Filter, 
  ChevronDown, 
  RotateCcw, 
  Calendar, 
  PlaneTakeoff, 
  PlaneLanding, 
  Building2, 
  Tag, 
  Layers, 
  Check, 
  SlidersHorizontal, 
  Sparkles 
} from 'lucide-react';

export const FilterBar = () => {
  const location = useLocation();
  const { filters, updateFilter, resetFilters } = useFilters();
  const [activeDropdown, setActiveDropdown] = useState(null);

  // FilterBar is ONLY relevant on the main executive Overview / Dashboard.
  // It is explicitly removed from all other pages (Backtesting, API Access, Methodology, 
  // Scrapers, Data Quality, Reports, Settings, Users, etc.) where localized controls exist.
  const ALLOWED_PATHS = ['/', '/dashboard', '/airfare-index'];
  if (!ALLOWED_PATHS.includes(location.pathname)) {
    return null;
  }

  const toggleDropdown = (name) => {
    setActiveDropdown(activeDropdown === name ? null : name);
  };

  const closeDropdown = () => setActiveDropdown(null);

  return (
    <div className="bg-white border-b border-slate-200 px-6 py-2.5 space-y-2 shadow-2xs relative z-20 select-none">
      {/* LINE 1: Primary Dimensions & Reset Button */}
      <div className="flex items-center justify-between gap-3 flex-wrap sm:flex-nowrap">
        <div className="flex items-center gap-2.5 flex-wrap">
          {/* Label Badge */}
          <div className="flex items-center gap-1.5 text-blue-600 bg-blue-50/80 border border-blue-200/60 px-2.5 py-1 rounded-lg font-bold text-[10px] uppercase tracking-wider shrink-0">
            <SlidersHorizontal className="w-3.5 h-3.5" />
            <span>Filters</span>
          </div>

          {/* 1. Date Range Filter */}
          <div className="relative">
            <button
              onClick={() => toggleDropdown('dateRange')}
              className={`flex items-center gap-1.5 border rounded-lg px-3 py-1.5 transition-all text-xs whitespace-nowrap shadow-2xs cursor-pointer ${
                activeDropdown === 'dateRange'
                  ? 'border-blue-500 bg-blue-50/80 ring-2 ring-blue-500/20 text-blue-950 font-medium'
                  : 'border-slate-200/90 hover:border-slate-300 bg-slate-50/80 hover:bg-slate-100/90 text-slate-700'
              }`}
            >
              <Calendar className="w-3.5 h-3.5 text-slate-400 shrink-0" />
              <span className="text-slate-400 font-normal">Date Range:</span>
              <span className="font-bold text-slate-900">{filters.dateRange}</span>
              <ChevronDown className="w-3 h-3 text-slate-400 ml-0.5 shrink-0" />
            </button>

            {activeDropdown === 'dateRange' && (
              <div className="absolute left-0 mt-1.5 w-60 bg-white border border-slate-200 rounded-xl p-1.5 shadow-xl z-50 text-xs space-y-0.5">
                {['Aug 01 - Aug 31, 2026', 'Jul 01 - Jul 31, 2026', 'Jun 01 - Jun 30, 2026', 'Last 7 Days (Live)', 'Custom Range...'].map((opt) => (
                  <div
                    key={opt}
                    onClick={() => {
                      updateFilter('dateRange', opt);
                      closeDropdown();
                    }}
                    className="flex items-center justify-between px-2.5 py-1.5 rounded-lg hover:bg-slate-50 cursor-pointer font-medium text-slate-700"
                  >
                    <span>{opt}</span>
                    {filters.dateRange === opt && <Check className="w-3.5 h-3.5 text-blue-600 font-bold" />}
                  </div>
                ))}
              </div>
            )}
          </div>

          {/* 2. Origin Filter */}
          <div className="relative">
            <button
              onClick={() => toggleDropdown('origin')}
              className={`flex items-center gap-1.5 border rounded-lg px-3 py-1.5 transition-all text-xs whitespace-nowrap shadow-2xs cursor-pointer ${
                activeDropdown === 'origin'
                  ? 'border-blue-500 bg-blue-50/80 ring-2 ring-blue-500/20 text-blue-950 font-medium'
                  : 'border-slate-200/90 hover:border-slate-300 bg-slate-50/80 hover:bg-slate-100/90 text-slate-700'
              }`}
            >
              <PlaneTakeoff className="w-3.5 h-3.5 text-slate-400 shrink-0" />
              <span className="text-slate-400 font-normal">Origin:</span>
              <span className="font-bold text-slate-900">{filters.origin}</span>
              <ChevronDown className="w-3 h-3 text-slate-400 ml-0.5 shrink-0" />
            </button>

            {activeDropdown === 'origin' && (
              <div className="absolute left-0 mt-1.5 w-56 bg-white border border-slate-200 rounded-xl p-1.5 shadow-xl z-50 text-xs space-y-0.5 max-h-56 overflow-y-auto">
                {['All Airports', 'DEL (Delhi)', 'BOM (Mumbai)', 'BLR (Bengaluru)', 'HYD (Hyderabad)', 'CCU (Kolkata)', 'MAA (Chennai)', 'AMD (Ahmedabad)', 'GOI (Goa)'].map((opt) => (
                  <div
                    key={opt}
                    onClick={() => {
                      updateFilter('origin', opt);
                      closeDropdown();
                    }}
                    className="flex items-center justify-between px-2.5 py-1.5 rounded-lg hover:bg-slate-50 cursor-pointer font-medium text-slate-700"
                  >
                    <span>{opt}</span>
                    {filters.origin === opt && <Check className="w-3.5 h-3.5 text-blue-600 font-bold" />}
                  </div>
                ))}
              </div>
            )}
          </div>

          {/* 3. Destination Filter */}
          <div className="relative">
            <button
              onClick={() => toggleDropdown('destination')}
              className={`flex items-center gap-1.5 border rounded-lg px-3 py-1.5 transition-all text-xs whitespace-nowrap shadow-2xs cursor-pointer ${
                activeDropdown === 'destination'
                  ? 'border-blue-500 bg-blue-50/80 ring-2 ring-blue-500/20 text-blue-950 font-medium'
                  : 'border-slate-200/90 hover:border-slate-300 bg-slate-50/80 hover:bg-slate-100/90 text-slate-700'
              }`}
            >
              <PlaneLanding className="w-3.5 h-3.5 text-slate-400 shrink-0" />
              <span className="text-slate-400 font-normal">Destination:</span>
              <span className="font-bold text-slate-900">{filters.destination}</span>
              <ChevronDown className="w-3 h-3 text-slate-400 ml-0.5 shrink-0" />
            </button>

            {activeDropdown === 'destination' && (
              <div className="absolute left-0 mt-1.5 w-56 bg-white border border-slate-200 rounded-xl p-1.5 shadow-xl z-50 text-xs space-y-0.5 max-h-56 overflow-y-auto">
                {['All Airports', 'DEL (Delhi)', 'BOM (Mumbai)', 'BLR (Bengaluru)', 'HYD (Hyderabad)', 'CCU (Kolkata)', 'MAA (Chennai)', 'AMD (Ahmedabad)', 'GOI (Goa)'].map((opt) => (
                  <div
                    key={opt}
                    onClick={() => {
                      updateFilter('destination', opt);
                      closeDropdown();
                    }}
                    className="flex items-center justify-between px-2.5 py-1.5 rounded-lg hover:bg-slate-50 cursor-pointer font-medium text-slate-700"
                  >
                    <span>{opt}</span>
                    {filters.destination === opt && <Check className="w-3.5 h-3.5 text-blue-600 font-bold" />}
                  </div>
                ))}
              </div>
            )}
          </div>
        </div>

        {/* Reset Action */}
        <button
          onClick={resetFilters}
          className="flex items-center gap-1.5 text-slate-500 hover:text-slate-900 hover:bg-slate-100 px-3 py-1.5 rounded-lg text-xs font-bold whitespace-nowrap transition-colors shrink-0 cursor-pointer border border-slate-200 hover:border-slate-300 shadow-2xs"
        >
          <RotateCcw className="w-3.5 h-3.5 text-slate-400" />
          <span>Reset Filters</span>
        </button>
      </div>

      {/* LINE 2: Secondary Dimensions & Quick Category Presets */}
      <div className="flex items-center gap-2.5 flex-wrap pt-1 border-t border-slate-100">
        {/* 4. Airline Filter */}
        <div className="relative">
          <button
            onClick={() => toggleDropdown('airline')}
            className={`flex items-center gap-1.5 border rounded-lg px-3 py-1.5 transition-all text-xs whitespace-nowrap shadow-2xs cursor-pointer ${
              activeDropdown === 'airline'
                ? 'border-blue-500 bg-blue-50/80 ring-2 ring-blue-500/20 text-blue-950 font-medium'
                : 'border-slate-200/90 hover:border-slate-300 bg-slate-50/80 hover:bg-slate-100/90 text-slate-700'
            }`}
          >
            <Building2 className="w-3.5 h-3.5 text-slate-400 shrink-0" />
            <span className="text-slate-400 font-normal">Airline:</span>
            <span className="font-bold text-slate-900">{filters.airline}</span>
            <ChevronDown className="w-3 h-3 text-slate-400 ml-0.5 shrink-0" />
          </button>

          {activeDropdown === 'airline' && (
            <div className="absolute left-0 mt-1.5 w-56 bg-white border border-slate-200 rounded-xl p-1.5 shadow-xl z-50 text-xs space-y-0.5">
              {['All Airlines', 'IndiGo (6E)', 'Air India (AI)', 'Akasa Air (QP)', 'SpiceJet (SG)', 'Air India Express (IX)'].map((opt) => (
                <div
                  key={opt}
                  onClick={() => {
                    updateFilter('airline', opt);
                    closeDropdown();
                  }}
                  className="flex items-center justify-between px-2.5 py-1.5 rounded-lg hover:bg-slate-50 cursor-pointer font-medium text-slate-700"
                >
                  <span>{opt}</span>
                  {filters.airline === opt && <Check className="w-3.5 h-3.5 text-blue-600 font-bold" />}
                </div>
              ))}
            </div>
          )}
        </div>

        {/* 5. Route Category Filter */}
        <div className="relative">
          <button
            onClick={() => toggleDropdown('routeCategory')}
            className={`flex items-center gap-1.5 border rounded-lg px-3 py-1.5 transition-all text-xs whitespace-nowrap shadow-2xs cursor-pointer ${
              activeDropdown === 'routeCategory'
                ? 'border-blue-500 bg-blue-50/80 ring-2 ring-blue-500/20 text-blue-950 font-medium'
                : 'border-slate-200/90 hover:border-slate-300 bg-slate-50/80 hover:bg-slate-100/90 text-slate-700'
            }`}
          >
            <Tag className="w-3.5 h-3.5 text-slate-400 shrink-0" />
            <span className="text-slate-400 font-normal">Route Category:</span>
            <span className="font-bold text-slate-900">{filters.routeCategory}</span>
            <ChevronDown className="w-3 h-3 text-slate-400 ml-0.5 shrink-0" />
          </button>

          {activeDropdown === 'routeCategory' && (
            <div className="absolute left-0 mt-1.5 w-52 bg-white border border-slate-200 rounded-xl p-1.5 shadow-xl z-50 text-xs space-y-0.5">
              {['All', 'Metro to Metro', 'Metro to Non-Metro', 'Tier-2 Feeder Corridors', 'Tourist & Regional'].map((opt) => (
                <div
                  key={opt}
                  onClick={() => {
                    updateFilter('routeCategory', opt);
                    closeDropdown();
                  }}
                  className="flex items-center justify-between px-2.5 py-1.5 rounded-lg hover:bg-slate-50 cursor-pointer font-medium text-slate-700"
                >
                  <span>{opt}</span>
                  {filters.routeCategory === opt && <Check className="w-3.5 h-3.5 text-blue-600 font-bold" />}
                </div>
              ))}
            </div>
          )}
        </div>

        {/* 6. Fare Breakdown Filter */}
        <div className="relative">
          <button
            onClick={() => toggleDropdown('fareBreakdown')}
            className={`flex items-center gap-1.5 border rounded-lg px-3 py-1.5 transition-all text-xs whitespace-nowrap shadow-2xs cursor-pointer ${
              activeDropdown === 'fareBreakdown'
                ? 'border-blue-500 bg-blue-50/80 ring-2 ring-blue-500/20 text-blue-950 font-medium'
                : 'border-slate-200/90 hover:border-slate-300 bg-slate-50/80 hover:bg-slate-100/90 text-slate-700'
            }`}
          >
            <Layers className="w-3.5 h-3.5 text-slate-400 shrink-0" />
            <span className="text-slate-400 font-normal">Fare Breakdown:</span>
            <span className="font-bold text-slate-900">{filters.fareBreakdown}</span>
            <ChevronDown className="w-3 h-3 text-slate-400 ml-0.5 shrink-0" />
          </button>

          {activeDropdown === 'fareBreakdown' && (
            <div className="absolute left-0 mt-1.5 w-56 bg-white border border-slate-200 rounded-xl p-1.5 shadow-xl z-50 text-xs space-y-0.5">
              {['All', 'Base Fare Only', 'Base Fare + Taxes', 'Checkout Total (Incl Fees)', 'Seat & Ancillary Adjusted'].map((opt) => (
                <div
                  key={opt}
                  onClick={() => {
                    updateFilter('fareBreakdown', opt);
                    closeDropdown();
                  }}
                  className="flex items-center justify-between px-2.5 py-1.5 rounded-lg hover:bg-slate-50 cursor-pointer font-medium text-slate-700"
                >
                  <span>{opt}</span>
                  {filters.fareBreakdown === opt && <Check className="w-3.5 h-3.5 text-blue-600 font-bold" />}
                </div>
              ))}
            </div>
          )}
        </div>

        {/* Quick Tag Pills */}
        <div className="hidden lg:flex items-center gap-1.5 ml-auto text-[11px] text-slate-400 font-medium">
          <span className="text-slate-400 mr-1">Presets:</span>
          {['DEL ↔ BOM', 'BLR ↔ DEL', 'Top 15 Trunk'].map((preset) => (
            <button
              key={preset}
              onClick={() => {
                if (preset === 'DEL ↔ BOM') {
                  updateFilter('origin', 'DEL (Delhi)');
                  updateFilter('destination', 'BOM (Mumbai)');
                } else if (preset === 'BLR ↔ DEL') {
                  updateFilter('origin', 'BLR (Bengaluru)');
                  updateFilter('destination', 'DEL (Delhi)');
                } else {
                  updateFilter('routeCategory', 'Metro to Metro');
                }
              }}
              className="px-2 py-0.5 rounded-md bg-slate-100 hover:bg-blue-50 hover:text-blue-700 border border-slate-200/80 text-slate-600 transition-colors cursor-pointer"
            >
              {preset}
            </button>
          ))}
        </div>
      </div>
    </div>
  );
};
