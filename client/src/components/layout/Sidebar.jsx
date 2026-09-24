import React from 'react';
import { useNavigate, useLocation } from 'react-router-dom';
import { useRole } from '../../context/RoleContext';
import { getSectionsForRole } from '../../config/roles';
import { ShieldCheck, UserCheck } from 'lucide-react';

export const Sidebar = () => {
  const { currentRole, setIsRoleModalOpen } = useRole();
  const navigate = useNavigate();
  const location = useLocation();

  const sections = getSectionsForRole(currentRole);

  return (
    <aside className="w-64 bg-white dark:bg-[#0d1322] text-slate-800 dark:text-slate-200 flex flex-col h-screen sticky top-0 border-r border-slate-200 dark:border-slate-800 select-none z-30 shrink-0 font-sans transition-colors duration-200">
      {/* Brand Header - Clicking takes to Landing Page */}
      <div
        onClick={() => navigate('/')}
        className="p-5 border-b border-slate-100 dark:border-slate-800 cursor-pointer flex items-center gap-3 hover:bg-slate-50 dark:hover:bg-slate-800/50 transition-colors group"
        title="Go to Landing Page"
      >
        <div className="w-8 h-8 rounded-lg bg-slate-900 dark:bg-blue-600 text-white font-black text-xs flex items-center justify-center font-mono shadow-2xs group-hover:bg-blue-600 transition-colors">
          AG
        </div>
        <div>
          <h1 className="text-[15px] font-semibold text-[#111827] dark:text-white tracking-tight leading-none group-hover:text-blue-600 dark:group-hover:text-blue-400 transition-colors">
            AirGo
          </h1>
          <p className="text-xs text-[#6B7280] dark:text-slate-400 font-normal tracking-tight mt-1">
            Airfare Index Platform
          </p>
        </div>
      </div>

      {/* Navigation Items Grouped by 5 Sections */}
      <div className="flex-1 overflow-y-auto py-3 px-3 space-y-4 scrollbar-none">
        {sections.map((section, sIdx) => (
          <div key={section.title || sIdx} className="space-y-0.5">
            <div className="px-3 pb-1 pt-1 text-[10px] font-bold text-slate-400 dark:text-slate-500 uppercase tracking-wider">
              {section.title}
            </div>
            {section.items.map((item) => {
              const Icon = item.icon;
              const isActive = location.pathname === item.path;

              return (
                <button
                  key={item.id}
                  onClick={() => navigate(item.path)}
                  className={`w-full flex items-center justify-between px-3 py-2 rounded-lg text-[13px] transition-all cursor-pointer ${
                    isActive
                      ? 'bg-blue-50 dark:bg-blue-900/30 text-blue-700 dark:text-blue-400 font-semibold shadow-2xs'
                      : 'text-[#4B5563] dark:text-slate-400 hover:text-[#111827] dark:hover:text-white hover:bg-slate-50 dark:hover:bg-slate-800/60 font-medium'
                  }`}
                >
                  <div className="flex items-center gap-2.5 min-w-0">
                    {Icon && <Icon className={`w-4 h-4 shrink-0 ${isActive ? 'text-blue-600 dark:text-blue-400' : 'text-slate-400 dark:text-slate-500'}`} />}
                    <span className="truncate text-left">{item.label}</span>
                  </div>

                  {item.badge && (
                    <span className="bg-slate-100 dark:bg-slate-800 text-slate-600 dark:text-slate-300 text-[10px] font-semibold px-1.5 py-0.5 rounded-md shrink-0">
                      {item.badge}
                    </span>
                  )}
                </button>
              );
            })}
          </div>
        ))}
      </div>

      {/* Role Switcher Drawer in Sidebar Footer */}
      <div className="p-3 border-t border-slate-100 dark:border-slate-800 bg-slate-50/70 dark:bg-slate-900/60">
        <button
          onClick={() => setIsRoleModalOpen(true)}
          className="w-full flex items-center gap-2.5 p-2 rounded-lg border border-slate-200 dark:border-slate-700/80 bg-white dark:bg-[#111827] hover:border-blue-300 dark:hover:border-blue-700 hover:bg-blue-50/50 dark:hover:bg-slate-800/70 transition-all text-left shadow-2xs group cursor-pointer"
          title="Click to switch institutional role"
        >
          <img
            src={currentRole.avatar}
            alt={currentRole.name}
            className="w-7 h-7 rounded-full object-cover border border-slate-200 dark:border-slate-700 shrink-0"
          />
          <div className="min-w-0 flex-1">
            <p className="text-xs font-semibold text-slate-900 dark:text-white truncate leading-tight group-hover:text-blue-600 dark:group-hover:text-blue-400">
              {currentRole.name}
            </p>
            <p className="text-[10px] text-slate-500 dark:text-slate-400 truncate font-medium">
              {currentRole.roleLabel}
            </p>
          </div>
          <UserCheck className="w-3.5 h-3.5 text-slate-400 dark:text-slate-500 group-hover:text-blue-600 shrink-0" />
        </button>
        <div className="mt-2 px-1 flex items-center justify-between text-[10px] text-slate-400 dark:text-slate-500">
          <span>Base 2024 = 100.0</span>
          <span>MoSPI · DGCA</span>
        </div>
      </div>
    </aside>
  );
};
