import React from 'react';
import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom';
import { RoleProvider } from './context/RoleContext';
import { FilterProvider } from './context/FilterContext';
import { AuditModalProvider, useAuditModal } from './context/AuditModalContext';
import { Sidebar } from './components/layout/Sidebar';
import { Header } from './components/layout/Header';
import { RoleSwitcherModal } from './components/common/RoleSwitcherModal';

// 7 Existing Core Pages
import { DashboardPage } from './pages/DashboardPage';
import { DataCollectionPage } from './pages/DataCollectionPage';
import { AirfareDataPage } from './pages/AirfareDataPage';
import { IndexApixPage } from './pages/IndexApixPage';
import { AnalyticsPage } from './pages/AnalyticsPage';
import { BacktestingPage } from './pages/BacktestingPage';
import { SystemStatusPage } from './pages/SystemStatusPage';

// 10 New Institutional Pages
import { SourceCatalogPage } from './pages/SourceCatalogPage';
import { ScrapingRunsPage } from './pages/ScrapingRunsPage';
import { AiHealingScraperPage } from './pages/AiHealingScraperPage';
import { RouteBasketPage } from './pages/RouteBasketPage';
import { DataQualityPage } from './pages/DataQualityPage';
import { IndexMethodologyPage } from './pages/IndexMethodologyPage';
import { IndexReleasesPage } from './pages/IndexReleasesPage';
import { ReportsExportsPage } from './pages/ReportsExportsPage';
import { AuditLogPage } from './pages/AuditLogPage';
import { UsersRolesPage } from './pages/UsersRolesPage';
import { ApiAccessPage } from './pages/ApiAccessPage';

// Public Institutional Landing Page
import { LandingPage } from './pages/LandingPage';

// Corridor Micro-Level Deep Dive
import { RouteDetailPage } from './pages/RouteDetailPage';

// Interactive Audit & Scraper Simulation Modals
import { GroundTruthAuditModal } from './components/scraper/GroundTruthAuditModal';
import { HeadlessDemoRunnerModal } from './components/scraper/HeadlessDemoRunnerModal';

import { ThemeProvider } from './context/ThemeContext';

function AppLayout() {
  const { 
    isAuditOpen, 
    auditFlight, 
    closeAuditModal, 
    openAuditModal,
    isHeadlessOpen, 
    closeHeadless, 
    openHeadless
  } = useAuditModal();

  return (
    <div className="flex min-h-screen bg-[#f8fafc] dark:bg-[#090d16] text-slate-900 dark:text-slate-100 font-sans antialiased transition-colors duration-200">
      {/* Streamlined Left Navigation Sidebar */}
      <Sidebar />

      {/* Main Content Area */}
      <div className="flex-1 flex flex-col min-w-0">
        {/* Dynamic Header with Breadcrumbs & Official Persona */}
        <Header />

        {/* Page Content Body */}
        <main className="flex-1 p-6 space-y-6 max-w-[1600px] w-full mx-auto">
          <Routes>
            {/* 7 Existing Core Routes */}
            <Route path="/dashboard" element={<DashboardPage />} />
            <Route path="/data-collection" element={<DataCollectionPage />} />
            <Route path="/airfare-data" element={<AirfareDataPage />} />
            <Route path="/index-apix" element={<IndexApixPage />} />
            <Route path="/analytics" element={<AnalyticsPage />} />
            <Route path="/backtesting" element={<BacktestingPage />} />
            <Route path="/system-status" element={<SystemStatusPage />} />

            {/* 10 Institutional Expansion Routes */}
            <Route path="/source-catalog" element={<SourceCatalogPage />} />
            <Route path="/scraping-runs" element={<ScrapingRunsPage />} />
            <Route path="/ai-healing-scrapers" element={<AiHealingScraperPage />} />
            <Route path="/route-basket" element={<RouteBasketPage />} />
            <Route path="/data-quality" element={<DataQualityPage />} />
            <Route path="/index-methodology" element={<IndexMethodologyPage />} />
            <Route path="/index-releases" element={<IndexReleasesPage />} />
            <Route path="/reports-exports" element={<ReportsExportsPage />} />
            <Route path="/audit-log" element={<AuditLogPage />} />
            <Route path="/users-roles" element={<UsersRolesPage />} />
            <Route path="/api-access" element={<ApiAccessPage />} />

            {/* Corridor Drill-down */}
            <Route path="/index/routes/:routeId" element={<RouteDetailPage />} />

            {/* Backward Compatibility Aliases & Safe Redirects */}
            <Route path="/index/routes" element={<Navigate to="/index-apix" replace />} />
            <Route path="/airfare-index" element={<Navigate to="/index-apix" replace />} />
            <Route path="/route-intelligence" element={<Navigate to="/index-apix" replace />} />
            <Route path="/index/overview" element={<Navigate to="/dashboard" replace />} />
            <Route path="/index/booking-window" element={<Navigate to="/analytics" replace />} />
            <Route path="/index/airlines" element={<Navigate to="/index-apix" replace />} />
            <Route path="/index/flights" element={<Navigate to="/airfare-data" replace />} />
            <Route path="/index/flights/:flightId" element={<Navigate to="/airfare-data" replace />} />
            <Route path="/index/platforms" element={<Navigate to="/analytics" replace />} />
            <Route path="/index/price-analytics" element={<Navigate to="/analytics" replace />} />
            <Route path="/index/inflation" element={<Navigate to="/index-apix" replace />} />
            <Route path="/index/raw-data" element={<Navigate to="/airfare-data" replace />} />
            <Route path="/index/data-quality" element={<Navigate to="/data-quality" replace />} />
            <Route path="/index/methodology" element={<Navigate to="/index-methodology" replace />} />
            <Route path="/fare-analytics" element={<Navigate to="/analytics" replace />} />
            <Route path="/passenger-demand" element={<Navigate to="/analytics" replace />} />
            <Route path="/anomaly-detection" element={<Navigate to="/data-quality" replace />} />
            <Route path="/data-sources" element={<Navigate to="/source-catalog" replace />} />
            <Route path="/scraping-monitor" element={<Navigate to="/scraping-runs" replace />} />
            <Route path="/ai-scraper-manager" element={<Navigate to="/ai-healing-scrapers" replace />} />
            <Route path="/scraper-manager" element={<Navigate to="/ai-healing-scrapers" replace />} />
            <Route path="/self-healing" element={<Navigate to="/ai-healing-scrapers" replace />} />
            <Route path="/historical-data" element={<Navigate to="/backtesting" replace />} />
            <Route path="/govt-reports" element={<Navigate to="/reports-exports" replace />} />
            <Route path="/export-centre" element={<Navigate to="/reports-exports" replace />} />
            <Route path="/system-settings" element={<Navigate to="/system-status" replace />} />
            <Route path="*" element={<Navigate to="/dashboard" replace />} />
          </Routes>

          {/* Institutional Compliance Footer */}
          <footer className="text-center text-[11px] text-slate-400 dark:text-slate-500 py-4 border-t border-slate-200/60 dark:border-slate-800/80 mt-10">
            SIH26056: Real-time Airfare Price Index for India · Ministry of Statistics & Programme Implementation (MoSPI) · Directorate General of Civil Aviation (DGCA)
          </footer>
        </main>
      </div>

      {/* Global Interactive Role Switcher Modal */}
      <RoleSwitcherModal />

      {/* Ground-Truth Audit Modal (4-Step Screenshot Lightbox) */}
      <GroundTruthAuditModal 
        isOpen={isAuditOpen} 
        onClose={closeAuditModal} 
        flight={auditFlight} 
      />

      {/* Interactive Headless Demo Runner Modal */}
      <HeadlessDemoRunnerModal 
        isOpen={isHeadlessOpen} 
        onClose={closeHeadless} 
        onInspectFlight={(flight) => {
          closeHeadless();
          openAuditModal(flight);
        }}
      />
    </div>
  );
}

function App() {
  return (
    <BrowserRouter>
      <ThemeProvider>
        <RoleProvider>
          <FilterProvider>
            <AuditModalProvider>
              <Routes>
                {/* Public Institutional Landing Page (Full-Width) */}
                <Route path="/" element={<LandingPage />} />

                {/* Operational Platform Terminal Suite */}
                <Route path="/*" element={<AppLayout />} />
              </Routes>
            </AuditModalProvider>
          </FilterProvider>
        </RoleProvider>
      </ThemeProvider>
    </BrowserRouter>
  );
}

export default App;
