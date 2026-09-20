import { 
  LayoutDashboard, 
  TrendingUp, 
  Compass, 
  BarChart3, 
  AlertTriangle, 
  Database, 
  Activity, 
  CheckCircle2, 
  History, 
  FileText, 
  Download, 
  Shield, 
  Settings,
  Scale,
  Layers,
  Plane,
  Calendar,
  BookOpen,
  Key
} from 'lucide-react';

export const USER_ROLES = {
  POLICY_ANALYST: {
    id: 'policy_analyst',
    name: 'Dr. Ananya Rao',
    title: 'Senior Policy Analyst',
    department: 'MoSPI / NSO Economic Statistics',
    avatar: 'https://images.unsplash.com/photo-1573496359142-b8d87734a5a2?q=80&w=150&auto=format&fit=crop',
    roleLabel: 'Senior Policy Analyst',
    badgeColor: 'bg-blue-500/10 text-blue-400 border-blue-500/20',
    sections: [
      {
        title: 'OVERVIEW',
        items: [
          { id: 'dashboard', label: 'Classic Dashboard', icon: LayoutDashboard, path: '/dashboard', active: true }
        ]
      },
      {
        title: 'INDEX & PRICE ANALYTICS',
        items: [
          { id: 'routes_index', label: 'Route Index & Heatmap', icon: Compass, path: '/index/routes' },
          { id: 'booking_window', label: 'Booking Window Horizon', icon: Calendar, path: '/index/booking-window' },
          { id: 'airline_analytics', label: 'Airline Pricing & Yield', icon: Plane, path: '/index/airlines' },
          { id: 'flight_analytics', label: 'Flight Product Explorer', icon: Layers, path: '/index/flights' },
          { id: 'platform_analytics', label: 'Platform & OTA Spreads', icon: BarChart3, path: '/index/platforms' },
          { id: 'price_analytics', label: 'Price Distributions & Volatility', icon: Activity, path: '/index/price-analytics' },
          { id: 'inflation_analytics', label: 'Airfare Inflation', icon: TrendingUp, path: '/index/inflation' }
        ]
      },
      {
        title: 'AUDIT & METHODOLOGY',
        items: [
          { id: 'raw_data', label: 'Raw Observations Log', icon: Database, path: '/index/raw-data' },
          { id: 'data_quality', label: 'Data Quality Assurance', icon: CheckCircle2, path: '/index/data-quality' },
          { id: 'methodology', label: 'Index Methodology', icon: BookOpen, path: '/index/methodology' },
          { id: 'backtesting', label: 'Backtesting & Validation', icon: History, path: '/backtesting' },
          { id: 'scraping_monitor', label: 'Scraping Monitor', icon: Activity, path: '/scraping-monitor' }
        ]
      },
      {
        title: 'REPORTS & EXPORTS',
        items: [
          { id: 'govt_reports', label: 'Government Reports', icon: FileText, path: '/govt-reports' },
          { id: 'export_centre', label: 'Export Centre', icon: Download, path: '/export-centre' },
          { id: 'api_access', label: 'Government API Gateway', icon: Key, path: '/api-access' }
        ]
      },
      {
        title: 'ADMINISTRATION',
        items: [
          { id: 'users_roles', label: 'Users & Roles', icon: Shield, path: '/users-roles' },
          { id: 'system_settings', label: 'System Settings', icon: Settings, path: '/system-settings' }
        ]
      }
    ]
  },

  DGCA_AUDITOR: {
    id: 'dgca_auditor',
    name: 'Rajesh Verma',
    title: 'DGCA Tariff Auditor',
    department: 'Directorate General of Civil Aviation',
    avatar: 'https://images.unsplash.com/photo-1507003211169-0a1dd7228f2d?q=80&w=150&auto=format&fit=crop',
    roleLabel: 'Tariff Regulator',
    badgeColor: 'bg-emerald-500/10 text-emerald-400 border-emerald-500/20',
    sections: [
      {
        title: 'OVERVIEW',
        items: [
          { id: 'dashboard', label: 'Tariff Compliance Dashboard', icon: LayoutDashboard, path: '/dashboard', active: true }
        ]
      },
      {
        title: 'REGULATORY AUDIT',
        items: [
          { id: 'routes_index', label: 'Corridor Index & Heatmap', icon: Scale, path: '/index/routes' },
          { id: 'booking_window', label: 'T+1 Surge Window Audit', icon: Calendar, path: '/index/booking-window' },
          { id: 'backtesting', label: 'DGCA Tariff Backtesting', icon: History, path: '/backtesting' },
          { id: 'platform_analytics', label: 'Direct vs OTA Fee Spreads', icon: BarChart3, path: '/index/platforms' },
          { id: 'anomaly_detection', label: 'Surge Price Anomalies', icon: AlertTriangle, path: '/anomaly-detection', badge: '12' }
        ]
      },
      {
        title: 'EVIDENCE & DATA',
        items: [
          { id: 'raw_data', label: 'Raw Observations Audit Log', icon: Database, path: '/index/raw-data' },
          { id: 'data_quality', label: 'Ground-Truth Quality Verifier', icon: CheckCircle2, path: '/index/data-quality' },
          { id: 'scraping_monitor', label: 'Live Scraping Audits', icon: Activity, path: '/scraping-monitor' }
        ]
      },
      {
        title: 'REPORTS',
        items: [
          { id: 'govt_reports', label: 'DGCA Tariff Reports', icon: FileText, path: '/govt-reports' },
          { id: 'export_centre', label: 'Compliance Audit Exports', icon: Download, path: '/export-centre' },
          { id: 'api_access', label: 'DGCA API Gateway Feeds', icon: Key, path: '/api-access' }
        ]
      }
    ]
  },

  RBI_OFFICER: {
    id: 'rbi_officer',
    name: 'Dr. Sunita Deshmukh',
    title: 'RBI Monetary Policy Analyst',
    department: 'Reserve Bank of India (Monetary Policy Dept)',
    avatar: 'https://images.unsplash.com/photo-1580489944761-15a19d654956?q=80&w=150&auto=format&fit=crop',
    roleLabel: 'Monetary Policy Officer',
    badgeColor: 'bg-purple-500/10 text-purple-400 border-purple-500/20',
    sections: [
      {
        title: 'OVERVIEW',
        items: [
          { id: 'dashboard', label: 'CPI Transport Dashboard', icon: LayoutDashboard, path: '/dashboard', active: true }
        ]
      },
      {
        title: 'MACRO INFLATION',
        items: [
          { id: 'inflation_analytics', label: 'Airfare Inflation Decomposition', icon: TrendingUp, path: '/index/inflation' },
          { id: 'routes_index', label: 'Route Index Matrix', icon: Compass, path: '/index/routes' },
          { id: 'price_analytics', label: 'Price Volatility Distributions', icon: Activity, path: '/index/price-analytics' }
        ]
      },
      {
        title: 'FORECASTING & METHODOLOGY',
        items: [
          { id: 'methodology', label: 'Econometric Methodology', icon: BookOpen, path: '/index/methodology' },
          { id: 'backtesting', label: '30-Day Model Backtesting (CPI)', icon: History, path: '/backtesting' },
          { id: 'historical_data', label: 'Monthly CPI Historical Comparison', icon: History, path: '/historical-data' },
          { id: 'govt_reports', label: 'Monetary Policy Committee Reports', icon: FileText, path: '/govt-reports' },
          { id: 'export_centre', label: 'RBI Macro Data Feeds', icon: Download, path: '/export-centre' },
          { id: 'api_access', label: 'RBI Nowcasting API Gateway', icon: Key, path: '/api-access' }
        ]
      }
    ]
  }
};
