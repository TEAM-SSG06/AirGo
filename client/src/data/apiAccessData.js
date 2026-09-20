/**
 * Government & Institutional API Gateway Configuration Data
 * Formatted for MoSPI (NSO), Reserve Bank of India (RBI), DGCA, and state economic bureaus.
 */

export const API_CONSUMER_KEYS = [
  {
    id: 'KEY-RBI-MPC-01',
    clientName: 'Reserve Bank of India (Monetary Policy Dept)',
    ministry: 'Monetary Policy Committee (MPC)',
    keyPrefix: 'ag_live_rbi_mpc_9a4f...',
    maskedKey: 'ag_live_rbi_mpc_9a4f8821bc34e0921',
    status: 'ACTIVE',
    tier: 'Institutional Priority',
    scopes: ['apix:realtime', 'apix:backtest', 'rbi:bulletin', 'sectors:summary'],
    rateLimitPerMin: 300,
    dailyQuota: 50000,
    usedToday: 14280,
    monthlyRequests: 384500,
    ipWhitelisted: ['10.24.0.0/16', '164.100.12.0/24'],
    lastUsed: '3 minutes ago',
    createdAt: '2025-06-01',
    expiresAt: '2027-06-01',
    contactEmail: 'monetary-nowcast@rbi.org.in'
  },
  {
    id: 'KEY-MOSPI-NSO-02',
    clientName: 'MoSPI National Accounts Division (NAD / CPI)',
    ministry: 'Ministry of Statistics & Programme Implementation',
    keyPrefix: 'ag_live_mospi_nso_c2e1...',
    maskedKey: 'ag_live_mospi_nso_c2e17743df890a214',
    status: 'ACTIVE',
    tier: 'Statistical Core',
    scopes: ['apix:realtime', 'apix:backtest', 'nso:feed', 'quotes:disaggregated', 'reports:all'],
    rateLimitPerMin: 500,
    dailyQuota: 100000,
    usedToday: 41200,
    monthlyRequests: 890000,
    ipWhitelisted: ['164.100.0.0/16 (NIC Cloud)'],
    lastUsed: '12 minutes ago',
    createdAt: '2025-01-10',
    expiresAt: '2028-01-10',
    contactEmail: 'cpi-airtransport@mospi.gov.in'
  },
  {
    id: 'KEY-DGCA-TARIFF-03',
    clientName: 'DGCA Directorate of Air Transport & Tariffs',
    ministry: 'Directorate General of Civil Aviation',
    keyPrefix: 'ag_live_dgca_tariff_7f88...',
    maskedKey: 'ag_live_dgca_tariff_7f881109ea553c901',
    status: 'ACTIVE',
    tier: 'Regulatory Admin',
    scopes: ['* (Full Administrative Read & Quota Control)'],
    rateLimitPerMin: 600,
    dailyQuota: 150000,
    usedToday: 62450,
    monthlyRequests: 1240000,
    ipWhitelisted: ['164.100.72.0/24'],
    lastUsed: 'Just now',
    createdAt: '2024-11-01',
    expiresAt: '2028-11-01',
    contactEmail: 'tariff-monitoring@dgca.gov.in'
  },
  {
    id: 'KEY-NITI-AAYOG-04',
    clientName: 'NITI Aayog Infrastructure & Transport Vertical',
    ministry: 'National Institution for Transforming India',
    keyPrefix: 'ag_live_niti_trans_4e22...',
    maskedKey: 'ag_live_niti_trans_4e229910ba772e543',
    status: 'ACTIVE',
    tier: 'Policy Research',
    scopes: ['apix:realtime', 'apix:backtest', 'sectors:summary'],
    rateLimitPerMin: 120,
    dailyQuota: 25000,
    usedToday: 3820,
    monthlyRequests: 94200,
    ipWhitelisted: ['14.139.58.0/24'],
    lastUsed: '1 hour ago',
    createdAt: '2026-03-15',
    expiresAt: '2027-03-15',
    contactEmail: 'aviation-policy@nic.in'
  },
  {
    id: 'KEY-MOCA-PLAN-05',
    clientName: 'Ministry of Civil Aviation (Economic Planning)',
    ministry: 'Ministry of Civil Aviation (MoCA)',
    keyPrefix: 'ag_revoked_moca_old_110a...',
    maskedKey: 'ag_revoked_moca_old_110a0092bc112',
    status: 'REVOKED',
    tier: 'Standard Institutional',
    scopes: ['apix:realtime'],
    rateLimitPerMin: 60,
    dailyQuota: 10000,
    usedToday: 0,
    monthlyRequests: 0,
    ipWhitelisted: ['Any (Revoked)'],
    lastUsed: '2026-08-10',
    createdAt: '2025-03-01',
    expiresAt: '2026-08-10 (Rotated for security protocol)',
    contactEmail: 'planning-cell@moca.gov.in'
  }
];

export const GOVERNMENT_API_ENDPOINTS = [
  {
    path: '/api/v1/index/realtime',
    method: 'GET',
    category: 'Headline Index',
    title: 'Real-Time National APIx Headline Index',
    description: 'Retrieves synthesized national airfare price index, Laspeyres / Fisher formulations, 24h delta, and sector weighting.',
    authRequired: true,
    requiredScope: 'apix:realtime',
    rateLimit: '300 req/min',
    queryParams: [
      { name: 'base', type: 'string', default: '2024', description: 'Base index benchmark year (2024 = 100.0)' },
      { name: 'formula', type: 'string', default: 'fisher', description: 'Formula calculation: fisher | laspeyres | jevons' },
      { name: 'corridors', type: 'string', default: 'ALL', description: 'Comma-separated routes (e.g. BOM-DEL,BLR-DEL)' }
    ],
    sampleCurl: 'curl -X GET "https://airgo.gov.in/api/v1/index/realtime?base=2024&formula=fisher" \\\n  -H "Authorization: Bearer ag_live_rbi_mpc_9a4f..." \\\n  -H "Accept: application/json"',
    samplePython: `import requests

url = "https://airgo.gov.in/api/v1/index/realtime"
headers = {
    "Authorization": "Bearer ag_live_rbi_mpc_9a4f...",
    "Accept": "application/json"
}
params = {"base": "2024", "formula": "fisher"}
response = requests.get(url, headers=headers, params=params)
data = response.json()
print(f"National APIx: {data['headline_index']} (Base 2024=100)")`,
    sampleResponse: {
      status: "SUCCESS",
      timestamp: "2026-09-08T11:30:00+05:30",
      headline_index: 118.42,
      formula: "Fisher Superlative Ideal",
      base_benchmark: "2024=100.0",
      change_24h_pct: 1.4,
      change_mom_pct: 3.72,
      monitored_sectors: 20,
      verified_quotes_count: 4850,
      compliance: "MoSPI & DGCA Certified"
    }
  },
  {
    path: '/api/v1/backtest/series',
    method: 'GET',
    category: 'Statistical Backtesting',
    title: '30-Day Empirical Backtest & Trajectory Series',
    description: 'Delivers full 30-day continuous daily comparison between real-time APIx, DGCA monthly baseline tariff (100.0), and MoSPI CPI Transport Sub-Index.',
    authRequired: true,
    requiredScope: 'apix:backtest',
    rateLimit: '200 req/min',
    queryParams: [
      { name: 'days', type: 'integer', default: 30, description: 'Longitudinal time window: 7, 15, or 30 days' },
      { name: 'format', type: 'string', default: 'json', description: 'Output encoding format: json | csv' }
    ],
    sampleCurl: 'curl -X GET "https://airgo.gov.in/api/v1/backtest/series?days=30" \\\n  -H "Authorization: Bearer ag_live_mospi_nso_c2e1..."',
    samplePython: `import requests
import pandas as pd

url = "https://airgo.gov.in/api/v1/backtest/series"
headers = {"Authorization": "Bearer ag_live_mospi_nso_c2e1..."}
res = requests.get(url, headers=headers, params={"days": 30})
df = pd.DataFrame(res.json()['time_series'])
print(f"MAPE: {res.json()['metrics']['mape_pct']}% | CPI Correlation: {res.json()['metrics']['cpi_correlation']}")`,
    sampleResponse: {
      status: "SUCCESS",
      validation_window: "2026-08-01 to 2026-08-30 (30 Days)",
      metrics: {
        mape_pct: 2.14,
        cpi_correlation: 0.942,
        tracking_error: 1.48,
        validation_status: "PASS (<3.0%)"
      },
      time_series: [
        { date: "Aug 01", apix: 116.85, cpi_transport: 111.80, dgca_base: 100.0, avg_fare: 5610, quotes: 4720 },
        { date: "Aug 15", apix: 120.40, cpi_transport: 112.25, dgca_base: 100.0, avg_fare: 5790, quotes: 5190 },
        { date: "Aug 30", apix: 118.42, cpi_transport: 112.70, dgca_base: 100.0, avg_fare: 5840, quotes: 4850 }
      ]
    }
  },
  {
    path: '/api/v1/institutional/nso-feed',
    method: 'GET',
    category: 'MoSPI National Accounts',
    title: 'MoSPI / NSO CPI Transport Sub-Index Ingestion Feed',
    description: 'Standardized monthly consumer price relative feed formatted specifically for NSO CPI compilation protocols.',
    authRequired: true,
    requiredScope: 'nso:feed',
    rateLimit: '100 req/min',
    queryParams: [
      { name: 'month', type: 'string', default: '2026-08', description: 'Statistical accounting period (YYYY-MM)' },
      { name: 'basket_version', type: 'string', default: 'v2026.2', description: 'Route passenger traffic basket version' }
    ],
    sampleCurl: 'curl -X GET "https://airgo.gov.in/api/v1/institutional/nso-feed?month=2026-08" \\\n  -H "Authorization: Bearer ag_live_mospi_nso_c2e1..."',
    samplePython: `import requests

url = "https://airgo.gov.in/api/v1/institutional/nso-feed"
headers = {"Authorization": "Bearer ag_live_mospi_nso_c2e1..."}
resp = requests.get(url, headers=headers, params={"month": "2026-08"})
nso_payload = resp.json()
print("Sub-Index Value for CPI Transport:", nso_payload['index_value'])`,
    sampleResponse: {
      statistical_agency: "MoSPI / National Statistical Office (NSO)",
      sub_index_code: "CPI_TRANSPORT_AIR_TRAVEL",
      period: "2026-08",
      index_value: 118.42,
      base_period: "2024=100.0",
      basket_version: "v2026.2",
      total_observations_audited: 144350,
      zero_dummy_certified: true,
      sha256_checksum: "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855"
    }
  },
  {
    path: '/api/v1/quotes',
    method: 'GET',
    category: 'Disaggregated Micro-Data',
    title: 'Cleaned & Disaggregated Flight Quote Observations',
    description: 'Access individual unbundled fare quotes across carriers, advance purchase horizons (T+1..T+45), base fare, taxes, and fees.',
    authRequired: true,
    requiredScope: 'quotes:disaggregated',
    rateLimit: '500 req/min',
    queryParams: [
      { name: 'route', type: 'string', default: 'BOM-DEL', description: 'Corridor pair code (e.g. BOM-DEL, BLR-DEL)' },
      { name: 'horizon', type: 'string', default: 'T+1', description: 'Lead time horizon: T+1 | T+7 | T+15 | T+30 | T+45' },
      { name: 'limit', type: 'integer', default: 20, description: 'Records per batch (max 100)' }
    ],
    sampleCurl: 'curl -X GET "https://airgo.gov.in/api/v1/quotes?route=BOM-DEL&horizon=T+1&limit=5" \\\n  -H "Authorization: Bearer ag_live_dgca_tariff_7f88..."',
    samplePython: `import requests

url = "https://airgo.gov.in/api/v1/quotes"
headers = {"Authorization": "Bearer ag_live_dgca_tariff_7f88..."}
params = {"route": "BOM-DEL", "horizon": "T+1", "limit": 5}
quotes = requests.get(url, headers=headers, params=params).json()
for q in quotes['data']:
    print(f"{q['carrier']} {q['flight_no']} -> Base: ₹{q['base_fare']} | Total: ₹{q['total_fare']}")`,
    sampleResponse: {
      count: 2,
      route: "BOM-DEL",
      horizon: "T+1",
      data: [
        {
          flight_no: "6E-6027",
          carrier: "IndiGo",
          departure: "06:15",
          arrival: "08:30",
          base_fare: 4709,
          fuel_surcharge: 800,
          udf_tax: 920,
          seat_fee: 350,
          total_fare: 6779,
          lead_window: "T+1",
          verified_source: "Airline Direct TLS",
          ground_truth_hash: "99a82f..."
        },
        {
          flight_no: "AI-806",
          carrier: "Air India",
          departure: "07:30",
          arrival: "09:45",
          base_fare: 5120,
          fuel_surcharge: 950,
          udf_tax: 980,
          seat_fee: 0,
          total_fare: 7050,
          lead_window: "T+1",
          verified_source: "Air India Harvester",
          ground_truth_hash: "77b10c..."
        }
      ]
    }
  }
];

export const API_GATEWAY_METRICS = {
  totalApiRequests24h: 342150,
  averageResponseLatencyMs: 32,
  p99ResponseLatencyMs: 84,
  systemAvailabilityUptime: "99.98%",
  activeGovernmentClients: 4,
  rateLimitViolations24h: 0,
  tlsCipherSuite: "TLS_AES_256_GCM_SHA384",
  authenticationMethod: "Bearer Token (OAuth2 RFC 6750)"
};
