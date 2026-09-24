import React from 'react';
import { useNavigate, useLocation } from 'react-router-dom';
import { useRole } from '../../context/RoleContext';
import { useAuditModal } from '../../context/AuditModalContext';
import { useTheme } from '../../context/ThemeContext';
import { Calendar, Bell, ShieldCheck, Terminal, ChevronDown, Sun, Moon } from 'lucide-react';

export const Header = () => {
  const { currentRole, setIsRoleModalOpen } = useRole();
  const { openHeadless } = useAuditModal();
  const { isDark, toggleTheme } = useTheme();
  const navigate = useNavigate();
  const location = useLocation();

  const getCrumb = () => {
    switch (location.pathname) {
      case '/data-collection':
        return 'Data Collection';
      case '/scraping-runs':
        return 'Scraping Runs & Job History';
      case '/airfare-data':
        return 'Airfare Data';
      case '/data-quality':
        return 'Data Quality Center';
      case '/source-catalog':
        return 'Source Catalog';
      case '/route-basket':
        return 'Route & Basket Management';
      case '/index-apix':
        return 'Index / APIx';
      case '/index-methodology':
        return 'Index Methodology';
      case '/index-releases':
        return 'Index Releases';
      case '/backtesting':
        return 'Back-testing';
      case '/analytics':
        return 'Analytics';
      case '/reports-exports':
        return 'Reports & Exports';
      case '/system-status':
        return 'System/API Status';
      case '/api-access':
        return 'API Access & Keys';
      case '/audit-log':
        return 'Audit Log';
      case '/users-roles':
        return 'User & Role Management';
      default:
        if (location.pathname.startsWith('/index/routes/')) {
          return 'Corridor Analysis';
        }
        return 'Dashboard';
    }
  };

  const crumb = getCrumb();

  return (
    <header className="bg-white dark:bg-[#0d1322] border-b border-slate-200 dark:border-slate-800 px-6 py-2.5 flex items-center justify-between sticky top-0 z-20 shadow-xs transition-colors duration-200">
      {/* Institutional Platform Identifier & Breadcrumb Context */}
      <div className="flex items-center gap-2.5">
        <span className="px-2 py-0.5 rounded bg-blue-600 text-white font-bold text-[11px] tracking-wider shrink-0 font-mono">
          SIH26056
        </span>
        <div className="flex items-center gap-1.5 text-xs text-[#6B7280] dark:text-slate-400 font-medium">
          <button
            onClick={() => navigate('/')}
            className="hover:text-blue-600 dark:hover:text-blue-400 transition-colors cursor-pointer"
            title="Go to Landing Page"
          >
            AirGo
          </button>
          <span>/</span>
          <span className="text-[#111827] dark:text-white font-semibold">{crumb}</span>
        </div>
      </div>

      {/* Right Controls */}
      <div className="flex items-center gap-2.5">
        {/* Scraper Studio Button */}
        <button
          onClick={() => openHeadless({ route: 'BOM-DEL', horizon: 'T+1' })}
          className="hidden sm:flex items-center gap-1.5 px-2.5 py-1.5 rounded-lg border border-slate-200 dark:border-slate-700/80 hover:border-emerald-500/50 bg-slate-50 dark:bg-slate-800/60 hover:bg-emerald-50 dark:hover:bg-emerald-950/30 text-[12px] font-medium text-slate-700 dark:text-slate-200 hover:text-emerald-700 dark:hover:text-emerald-400 transition-all cursor-pointer shadow-2xs group"
          title="Open Headless Scraper Simulation Studio"
        >
          <Terminal className="w-3.5 h-3.5 text-emerald-600 dark:text-emerald-400 group-hover:scale-110 transition-transform" />
          <span>Scraper Studio</span>
        </button>

        <div className="h-6 w-px bg-slate-200 dark:bg-slate-800 mx-0.5"></div>

        {/* Month / Date Selector */}
        <div className="relative hidden md:block">
          <div className="flex items-center gap-2 px-2.5 py-1.5 rounded-lg border border-slate-200 dark:border-slate-700/80 bg-slate-50 dark:bg-slate-800/60 text-[12px] font-medium text-[#111827] dark:text-slate-200 shadow-2xs">
            <Calendar className="w-3.5 h-3.5 text-[#6B7280] dark:text-slate-400" />
            <span>August 2026</span>
          </div>
        </div>

        {/* Dark / Light Mode Toggle Button */}
        <button
          onClick={toggleTheme}
          title={isDark ? "Switch to Light Mode" : "Switch to Dark Mode"}
          className="w-8 h-8 rounded-lg border border-slate-200 dark:border-slate-700/80 hover:border-slate-300 dark:hover:border-slate-600 flex items-center justify-center text-[#4B5563] dark:text-amber-400 bg-slate-50 dark:bg-slate-800/60 hover:bg-slate-100 dark:hover:bg-slate-700/60 transition-colors cursor-pointer"
          aria-label="Toggle dark mode"
        >
          {isDark ? <Sun className="w-4 h-4 text-amber-400" /> : <Moon className="w-4 h-4 text-slate-600" />}
        </button>

        {/* Notifications */}
        <button
          title="Data Verification & Pipeline Alerts"
          className="w-8 h-8 rounded-lg border border-slate-200 dark:border-slate-700/80 hover:border-slate-300 dark:hover:border-slate-600 flex items-center justify-center text-[#4B5563] dark:text-slate-300 bg-slate-50 dark:bg-slate-800/60 hover:bg-slate-100 dark:hover:bg-slate-700/60 relative transition-colors cursor-pointer"
        >
          <Bell className="w-4 h-4 text-[#6B7280] dark:text-slate-400" />
          <span className="w-2 h-2 rounded-full bg-emerald-500 absolute top-1.5 right-1.5 ring-2 ring-white dark:ring-slate-900"></span>
        </button>

        <div className="h-6 w-px bg-slate-200 dark:bg-slate-800 mx-0.5"></div>

        {/* User Profile Persona Switcher Button */}
        <button
          onClick={() => setIsRoleModalOpen(true)}
          className="flex items-center gap-2.5 pl-1.5 pr-2.5 py-1 rounded-lg bg-slate-50 hover:bg-blue-50/60 border border-slate-200 hover:border-blue-300 text-left transition-all cursor-pointer shadow-2xs group"
          title="Click to switch user role and test permissions"
        >
          <img
            src={currentRole.avatar}
            alt={currentRole.name}
            className="w-7 h-7 rounded-full object-cover border border-slate-200"
          />
          <div className="hidden lg:block text-left">
            <div className="flex items-center gap-1.5">
              <p className="text-xs font-semibold text-[#111827] leading-tight group-hover:text-blue-600">
                {currentRole.name}
              </p>
              <span className={`text-[10px] font-bold px-1.5 py-0.2 rounded border ${currentRole.badgeColor}`}>
                {currentRole.roleLabel}
              </span>
            </div>
            <p className="text-[10px] text-[#6B7280] font-normal leading-tight mt-0.5">
              {currentRole.title}
            </p>
          </div>
          <ChevronDown className="w-3.5 h-3.5 text-slate-400 group-hover:text-blue-600 transition-transform" />
        </button>
      </div>
    </header>
  );
};

