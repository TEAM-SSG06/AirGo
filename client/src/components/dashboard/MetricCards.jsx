import React from 'react';
import { KPI_METRICS } from '../../config/dashboardData';
import { 
  TrendingUp, 
  IndianRupee, 
  Users, 
  Plane, 
  Database, 
  AlertTriangle, 
  ArrowUpRight, 
  ArrowDownRight,
  Activity
} from 'lucide-react';

export const MetricCards = () => {
  const getIcon = (id) => {
    switch (id) {
      case 'airfare_index':
        return <TrendingUp className="w-4 h-4 text-blue-600" />;
      case 'avg_fare':
        return <IndianRupee className="w-4 h-4 text-indigo-600" />;
      case 'passenger_traffic':
        return <Users className="w-4 h-4 text-cyan-600" />;
      case 'routes_monitored':
        return <Plane className="w-4 h-4 text-emerald-600" />;
      case 'raw_observations':
        return <Database className="w-4 h-4 text-purple-600" />;
      case 'anomalies_detected':
        return <AlertTriangle className="w-4 h-4 text-amber-600" />;
      default:
        return <Activity className="w-4 h-4 text-slate-600" />;
    }
  };

  const getAccentBg = (id) => {
    switch (id) {
      case 'airfare_index':
        return 'bg-blue-50/70 border-blue-100/80';
      case 'avg_fare':
        return 'bg-indigo-50/70 border-indigo-100/80';
      case 'passenger_traffic':
        return 'bg-cyan-50/70 border-cyan-100/80';
      case 'routes_monitored':
        return 'bg-emerald-50/70 border-emerald-100/80';
      case 'raw_observations':
        return 'bg-purple-50/70 border-purple-100/80';
      case 'anomalies_detected':
        return 'bg-amber-50/70 border-amber-100/80';
      default:
        return 'bg-slate-50 border-slate-100';
    }
  };

  return (
    <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-6 gap-3.5">
      {KPI_METRICS.map((metric) => {
        const isAnomaly = metric.id === 'anomalies_detected';

        return (
          <div
            key={metric.id}
            className="bg-white border border-slate-200/90 rounded-xl p-4 shadow-2xs hover:shadow-xs hover:border-slate-300 transition-all relative flex flex-col justify-between group"
          >
            {/* Top row: Icon, Title, and Alert tag if any */}
            <div>
              <div className="flex items-center justify-between gap-1.5 mb-2">
                <div className={`p-1.5 rounded-lg border ${getAccentBg(metric.id)} transition-colors`}>
                  {getIcon(metric.id)}
                </div>
                {metric.tag && (
                  <span className="bg-red-500/10 text-red-600 border border-red-500/20 text-[9px] font-bold px-1.5 py-0.5 rounded tracking-wider">
                    {metric.tag}
                  </span>
                )}
              </div>

              <span className="text-[11px] font-semibold text-slate-600 leading-snug block">
                {metric.title}
              </span>

              {/* Big Metric Value */}
              <div className="mt-2">
                <span className="text-2xl font-black tracking-tight text-slate-900 group-hover:text-blue-600 transition-colors">
                  {metric.value}
                </span>
              </div>
            </div>

            {/* Bottom row: Delta & Subtext */}
            <div className="text-[10px] mt-3 pt-2 border-t border-slate-100 flex items-center justify-between">
              <div className="flex items-center gap-1 font-bold">
                {isAnomaly ? (
                  <span className="text-amber-600 flex items-center gap-0.5">
                    {metric.change}
                  </span>
                ) : (
                  <span className="text-emerald-600 flex items-center gap-0.5">
                    <ArrowUpRight className="w-3 h-3 stroke-[2.5]" />
                    {metric.change}
                  </span>
                )}
              </div>
              <span className="text-slate-400 font-normal truncate">{metric.changeSub}</span>
            </div>
          </div>
        );
      })}
    </div>
  );
};
