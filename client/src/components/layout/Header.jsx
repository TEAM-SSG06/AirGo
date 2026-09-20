import React from 'react';
import { useNavigate, useLocation } from 'react-router-dom';
import { useRole } from '../../context/RoleContext';
import { Calendar, Clock, Bell, ChevronDown, Sparkles } from 'lucide-react';

export const Header = () => {
  const { currentRole, setIsRoleModalOpen } = useRole();
  const navigate = useNavigate();
  const location = useLocation();

  const getPageInfo = () => {
    switch (location.pathname) {
      case '/route-intelligence':
        return { title: 'DGCA Domestic Route Basket & Index Weights', crumb: 'Route Basket & Weights' };
      case '/airfare-index':
        return { title: 'Airfare Price Index (APIx) Series', crumb: 'Airfare Index' };
      case '/fare-analytics':
        return { title: 'Fare Analytics & Dynamic Pricing', crumb: 'Fare Analytics' };
      case '/passenger-demand':
        return { title: 'DGCA Passenger Demand Analysis', crumb: 'Passenger Demand' };
      case '/anomaly-detection':
        return { title: 'Surge & Price Anomaly Detection', crumb: 'Anomaly Detection' };
      case '/data-sources':
        return { title: 'Data Sources & Connector Health', crumb: 'Data Sources' };
      case '/scraping-monitor':
        return { title: 'Scraping Monitor & Evidence Audit', crumb: 'Scraping Monitor' };
      case '/data-quality':
        return { title: 'Data Quality & Zero-Dummy Assurance', crumb: 'Data Quality' };
      case '/historical-data':
        return { title: 'Historical Airfare & CPI Time Series', crumb: 'Historical Data' };
      case '/backtesting':
      case '/index/backtesting':
        return { title: 'Econometric Back-Testing & Validation', crumb: 'Backtesting' };
      case '/govt-reports':
        return { title: 'Government & Regulatory Reports', crumb: 'Government Reports' };
      case '/export-centre':
        return { title: 'Data Export Centre', crumb: 'Export Centre' };
      case '/api-access':
      case '/index/api-access':
        return { title: 'Government API Gateway & Management', crumb: 'API Management' };
      case '/users-roles':
        return { title: 'Users & Roles (RBAC Management)', crumb: 'Users & Roles' };
      case '/system-settings':
        return { title: 'System Settings & Scraper Tuning', crumb: 'System Settings' };
      default:
        return { title: 'National Airfare Intelligence', crumb: 'Dashboard' };
    }
  };

  const { title, crumb } = getPageInfo();

  return (
    <header className="bg-white border-b border-slate-200 px-6 py-3.5 flex items-center justify-between sticky top-0 z-20 shadow-xs">
      {/* Title & Breadcrumbs */}
      <div>
        <h1 className="text-lg font-bold text-slate-900 tracking-tight flex items-center gap-2">
          {title}
        </h1>
        <div className="flex items-center gap-1.5 text-xs text-slate-500 font-medium">
          <button 
            onClick={() => navigate('/')}
            className="hover:text-blue-600 transition-colors cursor-pointer"
          >
            Home
          </button>
          <span>/</span>
          <span className="text-slate-800 font-semibold">{crumb}</span>
        </div>
      </div>

      {/* Right Controls */}
      <div className="flex items-center gap-3">
        {/* Month / Date Selector */}
        <div className="relative">
          <button className="flex items-center gap-2 px-3 py-1.5 rounded-lg border border-slate-200 hover:border-slate-300 bg-white text-xs font-semibold text-slate-700 shadow-2xs hover:bg-slate-50 transition-colors">
            <Calendar className="w-3.5 h-3.5 text-slate-500" />
            <span>August 2026</span>
            <ChevronDown className="w-3.5 h-3.5 text-slate-400" />
          </button>
        </div>

        {/* History / Refresh */}
        <button 
          title="Data Refresh Interval: 15 mins"
          className="w-8 h-8 rounded-lg border border-slate-200 hover:border-slate-300 flex items-center justify-center text-slate-600 hover:bg-slate-50 transition-colors"
        >
          <Clock className="w-4 h-4 text-slate-500" />
        </button>

        {/* Notifications */}
        <button 
          title="Notifications & Alerts"
          className="w-8 h-8 rounded-lg border border-slate-200 hover:border-slate-300 flex items-center justify-center text-slate-600 hover:bg-slate-50 relative transition-colors"
        >
          <Bell className="w-4 h-4 text-slate-500" />
          <span className="w-2 h-2 rounded-full bg-red-500 absolute top-1.5 right-1.5 ring-2 ring-white"></span>
        </button>

        <div className="h-6 w-px bg-slate-200 mx-1"></div>

        {/* User Profile / Quick Role Switch */}
        <button 
          onClick={() => setIsRoleModalOpen(true)}
          className="flex items-center gap-2.5 pl-1 pr-2 py-1 rounded-lg hover:bg-slate-100/80 transition-all text-left"
        >
          <img
            src={currentRole.avatar}
            alt={currentRole.name}
            className="w-8 h-8 rounded-full object-cover border border-slate-200"
          />
          <div className="hidden sm:block">
            <p className="text-xs font-bold text-slate-800 leading-tight">{currentRole.name}</p>
            <p className="text-[10px] text-slate-500">{currentRole.title}</p>
          </div>
          <ChevronDown className="w-3.5 h-3.5 text-slate-400 hidden sm:block" />
        </button>
      </div>
    </header>
  );
};
