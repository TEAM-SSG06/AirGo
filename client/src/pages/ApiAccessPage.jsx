import React, { useState } from 'react';
import { 
  Key, 
  ShieldCheck, 
  Copy, 
  Check, 
  RefreshCw, 
  Plus, 
  Code2, 
  Activity, 
  Clock, 
  Server, 
  ExternalLink, 
  AlertTriangle, 
  CheckCircle2, 
  X,
  Play,
  Terminal,
  Layers,
  ChevronDown,
  ChevronRight,
  Sliders,
  Lock,
  Globe,
  Download,
  Building2
} from 'lucide-react';
import { StatisticalBreadcrumbs } from '../components/analytics/StatisticalBreadcrumbs';
import { 
  API_CONSUMER_KEYS, 
  GOVERNMENT_API_ENDPOINTS, 
  API_GATEWAY_METRICS 
} from '../data/apiAccessData';

export const ApiAccessPage = () => {
  const [activeTab, setActiveTab] = useState('keys'); // 'keys' | 'console' | 'quotas' | 'security'
  const [keysList, setKeysList] = useState(API_CONSUMER_KEYS);
  const [copiedKeyId, setCopiedKeyId] = useState(null);
  const [copiedCode, setCopiedCode] = useState(false);
  const [showGenerateModal, setShowGenerateModal] = useState(false);
  
  // New Key Form State
  const [newClientName, setNewClientName] = useState('');
  const [newMinistry, setNewMinistry] = useState('');
  const [newScope, setNewScope] = useState('apix:realtime');
  const [newQuota, setNewQuota] = useState(50000);
  const [newRateLimit, setNewRateLimit] = useState(300);
  const [newIpSubnet, setNewIpSubnet] = useState('164.100.0.0/16');
  const [notice, setNotice] = useState('');

  // Interactive Console State
  const [selectedEndpointIndex, setSelectedEndpointIndex] = useState(0);
  const [activeCodeLang, setActiveCodeLang] = useState('curl'); // 'curl' | 'python'
  const [consoleParams, setConsoleParams] = useState({
    base: '2024',
    formula: 'fisher',
    days: 30,
    month: '2026-08',
    route: 'BOM-DEL',
    horizon: 'T+1'
  });
  const [isRunningTest, setIsRunningTest] = useState(false);
  const [testResponse, setTestResponse] = useState(null);

  const selectedEndpoint = GOVERNMENT_API_ENDPOINTS[selectedEndpointIndex] || GOVERNMENT_API_ENDPOINTS[0];

  const handleCopyKey = (keyId, maskedKey) => {
    navigator.clipboard.writeText(maskedKey || 'ag_live_key_sample_token');
    setCopiedKeyId(keyId);
    setTimeout(() => setCopiedKeyId(null), 2500);
  };

  const handleCopyCode = (text) => {
    navigator.clipboard.writeText(text);
    setCopiedCode(true);
    setTimeout(() => setCopiedCode(false), 2500);
  };

  const handleGenerateKey = (e) => {
    e.preventDefault();
    if (!newClientName) return;

    const newKeyObj = {
      id: `KEY-${newClientName.toUpperCase().slice(0, 4)}-${Date.now().toString().slice(-4)}`,
      clientName: newClientName,
      ministry: newMinistry || 'Government Department / Institution',
      keyPrefix: `ag_live_${newClientName.toLowerCase().replace(/[^a-z0-9]/g, '').slice(0, 5)}_${Math.random().toString(36).slice(2, 6)}...`,
      maskedKey: `ag_live_${newClientName.toLowerCase().replace(/[^a-z0-9]/g, '').slice(0, 5)}_${Math.random().toString(36).slice(2, 10)}8890`,
      status: 'ACTIVE',
      tier: 'Institutional Priority',
      scopes: [newScope, 'sectors:summary'],
      rateLimitPerMin: Number(newRateLimit),
      dailyQuota: Number(newQuota),
      usedToday: 0,
      monthlyRequests: 0,
      ipWhitelisted: [newIpSubnet || '164.100.0.0/16'],
      lastUsed: 'Provisioned just now',
      createdAt: new Date().toISOString().slice(0, 10),
      expiresAt: new Date(Date.now() + 730 * 24 * 3600 * 1000).toISOString().slice(0, 10),
      contactEmail: `api-access@${newClientName.toLowerCase().replace(/[^a-z0-9]/g, '')}.gov.in`
    };

    setKeysList([newKeyObj, ...keysList]);
    setShowGenerateModal(false);
    setNewClientName('');
    setNewMinistry('');
    setNotice(`API Access Key provisioned successfully for ${newKeyObj.clientName}`);
    setTimeout(() => setNotice(''), 4000);
  };

  const handleRotateKey = (keyId) => {
    setKeysList(keysList.map(k => {
      if (k.id === keyId) {
        return {
          ...k,
          maskedKey: `ag_live_rot_${Math.random().toString(36).slice(2, 12)}_sec992`,
          lastUsed: 'Key rotated just now'
        };
      }
      return k;
    }));
    setNotice(`Security rotation complete for ${keyId}. Previous token invalidated.`);
    setTimeout(() => setNotice(''), 4000);
  };

  const handleToggleRevoke = (keyId) => {
    setKeysList(keysList.map(k => {
      if (k.id === keyId) {
        const nextStatus = k.status === 'ACTIVE' ? 'REVOKED' : 'ACTIVE';
        return { ...k, status: nextStatus };
      }
      return k;
    }));
  };

  const handleExecuteLiveTest = () => {
    setIsRunningTest(true);
    setTestResponse(null);
    setTimeout(() => {
      setIsRunningTest(false);
      setTestResponse({
        httpStatus: 200,
        statusText: 'OK',
        latencyMs: Math.floor(Math.random() * 25) + 20,
        headers: {
          'content-type': 'application/json; charset=utf-8',
          'x-ratelimit-limit': selectedEndpoint.rateLimit,
          'x-ratelimit-remaining': '298',
          'x-airgo-version': 'v2026.2',
          'access-control-allow-origin': '*.gov.in, *.rbi.org.in'
        },
        data: selectedEndpoint.sampleResponse
      });
    }, 600);
  };

  const handleExportOpenApi = () => {
    const spec = {
      openapi: '3.0.3',
      info: {
        title: 'AirGo Real-Time Airfare Price Index (APIx) Government API',
        version: '1.0.0',
        description: 'Official API documentation for MoSPI (NSO), Reserve Bank of India (RBI), and DGCA integration.'
      },
      servers: [{ url: 'https://airgo.gov.in/api/v1' }],
      endpoints: GOVERNMENT_API_ENDPOINTS
    };
    const dataStr = 'data:text/json;charset=utf-8,' + encodeURIComponent(JSON.stringify(spec, null, 2));
    const a = document.createElement('a');
    a.setAttribute('href', dataStr);
    a.setAttribute('download', 'airgo_government_openapi_spec.json');
    document.body.appendChild(a);
    a.click();
    a.remove();
    setNotice('OpenAPI v3.0 Specification downloaded.');
    setTimeout(() => setNotice(''), 3500);
  };

  return (
    <div className="space-y-6 text-slate-900 font-sans animate-in fade-in duration-200">
      {/* 1. Institutional Breadcrumb Navigation */}
      <StatisticalBreadcrumbs 
        items={[{ label: 'Government API Gateway & Management', path: '/api-access', icon: Key }]} 
      />

      {/* 2. Header Banner */}
      <div className="bg-white border border-slate-200 rounded-xl p-6 shadow-2xs space-y-4">
        <div className="flex flex-col md:flex-row justify-between items-start md:items-center gap-4">
          <div>
            <div className="flex items-center gap-2.5">
              <div className="w-9 h-9 rounded-lg bg-blue-50 border border-blue-200 text-blue-700 flex items-center justify-center font-bold">
                <Key className="w-5 h-5" />
              </div>
              <div>
                <h1 className="text-xl md:text-2xl font-bold text-slate-900 tracking-tight flex items-center gap-2">
                  Government API Gateway & Institutional Integration
                </h1>
                <p className="text-slate-500 text-xs md:text-sm mt-0.5 max-w-3xl">
                  Centralized institutional API management providing high-frequency REST feeds of Real-Time APIx, 30-day backtest series, and disaggregated quotes to MoSPI (NSO), RBI, and DGCA.
                </p>
              </div>
            </div>
          </div>

          <div className="flex items-center gap-2 w-full md:w-auto justify-end shrink-0">
            <button
              onClick={handleExportOpenApi}
              className="flex items-center gap-1.5 px-3 py-2 rounded-lg border border-slate-200 bg-white hover:bg-slate-50 text-slate-700 text-xs font-semibold shadow-2xs transition-colors cursor-pointer"
              title="Download OpenAPI Specification"
            >
              <Download className="w-3.5 h-3.5 text-slate-500" />
              <span>OpenAPI Spec</span>
            </button>

            <button
              onClick={() => setShowGenerateModal(true)}
              className="flex items-center gap-1.5 px-3.5 py-2 rounded-lg bg-blue-600 hover:bg-blue-700 text-white text-xs font-semibold shadow-2xs transition-colors cursor-pointer"
            >
              <Plus className="w-3.5 h-3.5" />
              <span>Provision Client Key</span>
            </button>
          </div>
        </div>

        {notice && (
          <div className="p-2.5 rounded-lg bg-emerald-50 border border-emerald-200 text-emerald-800 text-xs font-medium flex items-center gap-2 animate-in fade-in">
            <CheckCircle2 className="w-4 h-4 text-emerald-600 shrink-0" />
            <span>{notice}</span>
          </div>
        )}

        {/* Global Gateway Status Indicators */}
        <div className="flex items-center gap-2 pt-2 border-t border-slate-100 flex-wrap text-xs text-slate-500">
          <span className="inline-flex items-center gap-1 font-semibold text-emerald-700 bg-emerald-50 px-2 py-0.5 rounded border border-emerald-200">
            <CheckCircle2 className="w-3 h-3" /> Gateway Status: Operational (99.98% Uptime)
          </span>
          <span>•</span>
          <span>Security Protocol: <strong>TLS 1.3 / OAuth2 Bearer RFC 6750</strong></span>
          <span>•</span>
          <span>Intranet Whitelist: <strong>NIC Cloud / .gov.in & .rbi.org.in Subnets</strong></span>
        </div>
      </div>

      {/* 3. Gateway Health & Performance KPI Cards */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
        <div className="bg-white border border-slate-200 rounded-xl p-4 shadow-2xs">
          <span className="text-xs font-medium text-slate-500 block">24h Government API Requests</span>
          <div className="flex items-baseline gap-2 mt-1">
            <span className="text-2xl font-bold font-mono text-slate-900 tabular-nums">
              {API_GATEWAY_METRICS.totalApiRequests24h.toLocaleString()}
            </span>
            <span className="text-[11px] font-semibold text-emerald-700 bg-emerald-50 px-1.5 py-0.2 rounded border border-emerald-200">
              Active Sync
            </span>
          </div>
          <span className="text-[11px] text-slate-400 mt-1 block">MoSPI, RBI, and DGCA background ingestion</span>
        </div>

        <div className="bg-white border border-slate-200 rounded-xl p-4 shadow-2xs">
          <span className="text-xs font-medium text-slate-500 block">Average Gateway Latency</span>
          <div className="flex items-baseline gap-2 mt-1">
            <span className="text-2xl font-bold font-mono text-blue-600 tabular-nums">
              {API_GATEWAY_METRICS.averageResponseLatencyMs} ms
            </span>
            <span className="text-[11px] font-semibold text-slate-500 font-mono">
              p99: {API_GATEWAY_METRICS.p99ResponseLatencyMs} ms
            </span>
          </div>
          <span className="text-[11px] text-slate-400 mt-1 block">High-speed cached in-memory response tier</span>
        </div>

        <div className="bg-white border border-slate-200 rounded-xl p-4 shadow-2xs">
          <span className="text-xs font-medium text-slate-500 block">Active Institutional Clients</span>
          <div className="flex items-baseline gap-2 mt-1">
            <span className="text-2xl font-bold font-mono text-slate-900 tabular-nums">
              {keysList.filter(k => k.status === 'ACTIVE').length} Ministries
            </span>
            <span className="text-[11px] font-semibold text-purple-700 bg-purple-50 px-1.5 py-0.2 rounded border border-purple-200">
              Zero Leakage
            </span>
          </div>
          <span className="text-[11px] text-slate-400 mt-1 block">Provisioned with cryptographic token authentication</span>
        </div>

        <div className="bg-white border border-slate-200 rounded-xl p-4 shadow-2xs">
          <span className="text-xs font-medium text-slate-500 block">Rate Limit Violations (24h)</span>
          <div className="flex items-baseline gap-2 mt-1">
            <span className="text-2xl font-bold font-mono text-emerald-600 tabular-nums">
              {API_GATEWAY_METRICS.rateLimitViolations24h}
            </span>
            <span className="text-[11px] font-semibold text-emerald-700 bg-emerald-50 px-1.5 py-0.2 rounded border border-emerald-200">
              100% SLA Compliant
            </span>
          </div>
          <span className="text-[11px] text-slate-400 mt-1 block">Token-bucket algorithms prevent endpoint overload</span>
        </div>
      </div>

      {/* 4. Navigation Tabs */}
      <div className="flex items-center gap-1.5 border-b border-slate-200 pb-0 text-xs font-semibold">
        <button
          onClick={() => setActiveTab('keys')}
          className={`px-4 py-2.5 border-b-2 transition-all cursor-pointer flex items-center gap-2 ${
            activeTab === 'keys'
              ? 'border-blue-600 text-blue-700 font-bold bg-white'
              : 'border-transparent text-slate-500 hover:text-slate-800'
          }`}
        >
          <Key className="w-3.5 h-3.5" />
          <span>Government Client Keys ({keysList.length})</span>
        </button>

        <button
          onClick={() => setActiveTab('console')}
          className={`px-4 py-2.5 border-b-2 transition-all cursor-pointer flex items-center gap-2 ${
            activeTab === 'console'
              ? 'border-blue-600 text-blue-700 font-bold bg-white'
              : 'border-transparent text-slate-500 hover:text-slate-800'
          }`}
        >
          <Terminal className="w-3.5 h-3.5" />
          <span>Interactive API Console & Endpoints</span>
        </button>

        <button
          onClick={() => setActiveTab('quotas')}
          className={`px-4 py-2.5 border-b-2 transition-all cursor-pointer flex items-center gap-2 ${
            activeTab === 'quotas'
              ? 'border-blue-600 text-blue-700 font-bold bg-white'
              : 'border-transparent text-slate-500 hover:text-slate-800'
          }`}
        >
          <Sliders className="w-3.5 h-3.5" />
          <span>Rate Limits & IP Whitelisting</span>
        </button>

        <button
          onClick={() => setActiveTab('security')}
          className={`px-4 py-2.5 border-b-2 transition-all cursor-pointer flex items-center gap-2 ${
            activeTab === 'security'
              ? 'border-blue-600 text-blue-700 font-bold bg-white'
              : 'border-transparent text-slate-500 hover:text-slate-800'
          }`}
        >
          <ShieldCheck className="w-3.5 h-3.5" />
          <span>Security & CERT-In Protocol</span>
        </button>
      </div>

      {/* TAB 1: Government Client Keys & Credentials */}
      {activeTab === 'keys' && (
        <div className="space-y-4">
          <div className="bg-white border border-slate-200 rounded-xl shadow-2xs overflow-hidden">
            <div className="p-4 border-b border-slate-100 flex flex-col sm:flex-row sm:items-center justify-between gap-2">
              <div>
                <h2 className="text-base font-bold text-slate-900 flex items-center gap-2">
                  <Building2 className="w-4 h-4 text-blue-600" />
                  <span>Provisioned Government Institutions & Security Credentials</span>
                </h2>
                <p className="text-xs text-slate-500 mt-0.5">
                  Authorized ministries and agencies with cryptographic tokens configured for automated data ingestion.
                </p>
              </div>
              <span className="text-xs font-mono text-slate-500">Auto-rotate policy: 180 days</span>
            </div>

            <div className="divide-y divide-slate-100">
              {keysList.map((clientKey) => {
                const isCopied = copiedKeyId === clientKey.id;
                const quotaPct = Math.round((clientKey.usedToday / clientKey.dailyQuota) * 100);

                return (
                  <div key={clientKey.id} className="p-5 hover:bg-slate-50/70 transition-colors space-y-3">
                    <div className="flex flex-col lg:flex-row lg:items-center justify-between gap-3">
                      <div className="space-y-1">
                        <div className="flex items-center gap-2.5 flex-wrap">
                          <span className="font-bold text-sm text-slate-900">{clientKey.clientName}</span>
                          <span className={`text-[10px] font-bold px-2 py-0.5 rounded-full border ${
                            clientKey.status === 'ACTIVE' 
                              ? 'bg-emerald-50 text-emerald-700 border-emerald-200' 
                              : 'bg-rose-50 text-rose-700 border-rose-200'
                          }`}>
                            {clientKey.status}
                          </span>
                          <span className="text-[10px] font-mono text-slate-500 bg-slate-100 px-2 py-0.5 rounded">
                            {clientKey.tier}
                          </span>
                        </div>
                        <p className="text-xs text-slate-500">{clientKey.ministry} • Contact: <span className="font-mono text-slate-700">{clientKey.contactEmail}</span></p>
                      </div>

                      {/* Action Buttons */}
                      <div className="flex items-center gap-2 shrink-0">
                        <button
                          onClick={() => handleCopyKey(clientKey.id, clientKey.maskedKey)}
                          className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg border border-slate-200 bg-white hover:bg-slate-100 text-xs font-semibold text-slate-700 shadow-2xs transition-colors cursor-pointer"
                        >
                          {isCopied ? <Check className="w-3.5 h-3.5 text-emerald-600" /> : <Copy className="w-3.5 h-3.5 text-slate-500" />}
                          <span>{isCopied ? 'Token Copied' : 'Copy Bearer Token'}</span>
                        </button>

                        <button
                          onClick={() => handleRotateKey(clientKey.id)}
                          className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg border border-slate-200 bg-white hover:bg-slate-100 text-xs font-semibold text-slate-700 shadow-2xs transition-colors cursor-pointer"
                          title="Generate new secret token and invalidate current"
                        >
                          <RefreshCw className="w-3.5 h-3.5 text-blue-600" />
                          <span>Rotate Key</span>
                        </button>

                        <button
                          onClick={() => handleToggleRevoke(clientKey.id)}
                          className={`px-3 py-1.5 rounded-lg border text-xs font-semibold shadow-2xs transition-colors cursor-pointer ${
                            clientKey.status === 'ACTIVE'
                              ? 'border-rose-200 bg-rose-50 hover:bg-rose-100 text-rose-700'
                              : 'border-emerald-200 bg-emerald-50 hover:bg-emerald-100 text-emerald-700'
                          }`}
                        >
                          {clientKey.status === 'ACTIVE' ? 'Suspend' : 'Reactivate'}
                        </button>
                      </div>
                    </div>

                    {/* Token Key Bar & Quota Metrics */}
                    <div className="grid grid-cols-1 md:grid-cols-3 gap-3 pt-2">
                      <div className="p-2.5 rounded-lg bg-slate-50 border border-slate-200 space-y-1">
                        <span className="text-[10px] uppercase font-bold text-slate-400 block tracking-wider">Secret API Key Token</span>
                        <div className="flex items-center justify-between font-mono text-xs text-slate-800">
                          <span>{clientKey.maskedKey}</span>
                        </div>
                      </div>

                      <div className="p-2.5 rounded-lg bg-slate-50 border border-slate-200 space-y-1">
                        <div className="flex justify-between items-center text-[10px] uppercase font-bold text-slate-400">
                          <span>Daily Quota Usage</span>
                          <span className="text-slate-700 font-mono">{clientKey.usedToday.toLocaleString()} / {clientKey.dailyQuota.toLocaleString()} ({quotaPct}%)</span>
                        </div>
                        <div className="w-full bg-slate-200 rounded-full h-1.5 overflow-hidden">
                          <div 
                            className={`h-full rounded-full transition-all ${quotaPct > 80 ? 'bg-amber-500' : 'bg-blue-600'}`} 
                            style={{ width: `${Math.min(quotaPct, 100)}%` }}
                          ></div>
                        </div>
                      </div>

                      <div className="p-2.5 rounded-lg bg-slate-50 border border-slate-200 space-y-1">
                        <span className="text-[10px] uppercase font-bold text-slate-400 block tracking-wider">Authorized IP Subnet & Rate</span>
                        <div className="flex items-center justify-between text-xs">
                          <span className="font-mono text-slate-700 truncate">{clientKey.ipWhitelisted?.join(', ')}</span>
                          <span className="font-semibold text-blue-700 shrink-0">{clientKey.rateLimitPerMin} req/m</span>
                        </div>
                      </div>
                    </div>

                    {/* Scopes Badges */}
                    <div className="flex items-center gap-1.5 flex-wrap pt-1 text-xs">
                      <span className="text-[11px] text-slate-400 font-medium">Scopes:</span>
                      {clientKey.scopes.map((sc, sIdx) => (
                        <span key={sIdx} className="px-2 py-0.5 rounded bg-blue-50 text-blue-700 border border-blue-200 font-mono text-[10px] font-semibold">
                          {sc}
                        </span>
                      ))}
                      <span className="text-[11px] text-slate-400 ml-auto font-mono">Last active: {clientKey.lastUsed}</span>
                    </div>
                  </div>
                );
              })}
            </div>
          </div>
        </div>
      )}

      {/* TAB 2: Interactive API Console & Endpoints */}
      {activeTab === 'console' && (
        <div className="grid grid-cols-1 lg:grid-cols-12 gap-6">
          {/* Left Column: Endpoint Selector List */}
          <div className="lg:col-span-4 space-y-3">
            <h3 className="text-xs font-bold uppercase tracking-wider text-slate-400 px-1">
              Government Endpoints Specification
            </h3>

            <div className="space-y-2">
              {GOVERNMENT_API_ENDPOINTS.map((ep, idx) => {
                const isSelected = idx === selectedEndpointIndex;
                return (
                  <div
                    key={ep.path}
                    onClick={() => setSelectedEndpointIndex(idx)}
                    className={`p-3.5 rounded-xl border transition-all cursor-pointer ${
                      isSelected
                        ? 'border-blue-500 bg-blue-50/50 shadow-2xs'
                        : 'border-slate-200 bg-white hover:border-slate-300'
                    }`}
                  >
                    <div className="flex items-center justify-between">
                      <span className="px-2 py-0.5 rounded bg-blue-600 text-white font-mono text-[10px] font-bold">
                        {ep.method}
                      </span>
                      <span className="text-[10px] font-semibold text-slate-400 uppercase">
                        {ep.category}
                      </span>
                    </div>

                    <p className="font-mono font-bold text-xs text-slate-900 mt-2 truncate">
                      {ep.path}
                    </p>
                    <p className="text-[11px] text-slate-500 mt-0.5 line-clamp-2">
                      {ep.title}
                    </p>
                  </div>
                );
              })}
            </div>
          </div>

          {/* Right Column: Interactive Sandbox & Code Runner */}
          <div className="lg:col-span-8 space-y-4">
            <div className="bg-white border border-slate-200 rounded-xl p-5 shadow-2xs space-y-4">
              <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2 pb-3 border-b border-slate-100">
                <div>
                  <div className="flex items-center gap-2">
                    <span className="px-2 py-0.5 rounded bg-blue-600 text-white font-mono text-xs font-bold">
                      {selectedEndpoint.method}
                    </span>
                    <h2 className="font-mono text-sm font-bold text-slate-900">
                      {selectedEndpoint.path}
                    </h2>
                  </div>
                  <p className="text-xs text-slate-500 mt-1">
                    {selectedEndpoint.description}
                  </p>
                </div>

                <div className="flex items-center gap-2">
                  <span className="text-[10px] font-mono text-slate-500 bg-slate-100 px-2 py-1 rounded">
                    Scope: <strong className="text-blue-700">{selectedEndpoint.requiredScope}</strong>
                  </span>
                </div>
              </div>

              {/* Query Parameters Configurator */}
              <div className="space-y-2">
                <h4 className="text-xs font-bold text-slate-700">Request Query Parameters</h4>
                <div className="grid grid-cols-1 sm:grid-cols-3 gap-3">
                  {selectedEndpoint.queryParams.map((param) => (
                    <div key={param.name} className="p-2.5 rounded-lg bg-slate-50 border border-slate-200 space-y-1">
                      <div className="flex justify-between items-center">
                        <span className="font-mono text-xs font-bold text-slate-900">{param.name}</span>
                        <span className="text-[10px] font-mono text-slate-400">{param.type}</span>
                      </div>
                      <input 
                        type="text"
                        value={consoleParams[param.name] || param.default || ''}
                        onChange={(e) => setConsoleParams({ ...consoleParams, [param.name]: e.target.value })}
                        className="w-full bg-white border border-slate-200 rounded px-2 py-1 text-xs font-mono focus:outline-none focus:border-blue-500"
                        placeholder={`default: ${param.default}`}
                      />
                      <p className="text-[10px] text-slate-500 truncate">{param.description}</p>
                    </div>
                  ))}
                </div>
              </div>

              {/* Code Snippet Switcher & Test Trigger */}
              <div className="space-y-2 pt-2">
                <div className="flex items-center justify-between">
                  <div className="flex items-center gap-1 bg-slate-100 p-0.5 rounded-lg text-xs font-medium">
                    <button
                      onClick={() => setActiveCodeLang('curl')}
                      className={`px-3 py-1 rounded-md transition-all cursor-pointer ${
                        activeCodeLang === 'curl' ? 'bg-white text-blue-700 font-bold shadow-2xs' : 'text-slate-600'
                      }`}
                    >
                      cURL
                    </button>
                    <button
                      onClick={() => setActiveCodeLang('python')}
                      className={`px-3 py-1 rounded-md transition-all cursor-pointer ${
                        activeCodeLang === 'python' ? 'bg-white text-blue-700 font-bold shadow-2xs' : 'text-slate-600'
                      }`}
                    >
                      Python (requests)
                    </button>
                  </div>

                  <div className="flex items-center gap-2">
                    <button
                      onClick={() => handleCopyCode(activeCodeLang === 'curl' ? selectedEndpoint.sampleCurl : selectedEndpoint.samplePython)}
                      className="flex items-center gap-1 text-xs text-slate-500 hover:text-slate-900 cursor-pointer font-medium"
                    >
                      {copiedCode ? <Check className="w-3.5 h-3.5 text-emerald-600" /> : <Copy className="w-3.5 h-3.5" />}
                      <span>{copiedCode ? 'Copied' : 'Copy Code'}</span>
                    </button>

                    <button
                      onClick={handleExecuteLiveTest}
                      disabled={isRunningTest}
                      className="flex items-center gap-1.5 px-3.5 py-1.5 rounded-lg bg-emerald-600 hover:bg-emerald-700 text-white text-xs font-semibold shadow-2xs transition-colors cursor-pointer"
                    >
                      {isRunningTest ? <RefreshCw className="w-3.5 h-3.5 animate-spin" /> : <Play className="w-3.5 h-3.5 fill-current" />}
                      <span>{isRunningTest ? 'Sending...' : 'Send Test Request'}</span>
                    </button>
                  </div>
                </div>

                {/* Code Box */}
                <pre className="p-3.5 rounded-lg bg-slate-900 text-slate-100 font-mono text-xs overflow-x-auto leading-relaxed border border-slate-800">
                  {activeCodeLang === 'curl' ? selectedEndpoint.sampleCurl : selectedEndpoint.samplePython}
                </pre>
              </div>

              {/* Live Test Response Display */}
              {testResponse && (
                <div className="space-y-2 pt-2 border-t border-slate-100 animate-in fade-in">
                  <div className="flex items-center justify-between">
                    <div className="flex items-center gap-2 text-xs">
                      <span className="font-bold text-slate-700">Response Status:</span>
                      <span className="font-mono font-bold text-emerald-700 bg-emerald-50 border border-emerald-200 px-2 py-0.5 rounded">
                        {testResponse.httpStatus} {testResponse.statusText}
                      </span>
                      <span className="text-slate-400">•</span>
                      <span className="font-mono text-slate-500">Latency: <strong>{testResponse.latencyMs} ms</strong></span>
                    </div>

                    <span className="text-[10px] font-mono text-slate-400">Content-Type: application/json</span>
                  </div>

                  <pre className="p-4 rounded-lg bg-slate-950 text-emerald-400 font-mono text-xs overflow-x-auto leading-relaxed border border-slate-800 max-h-72">
                    {JSON.stringify(testResponse.data, null, 2)}
                  </pre>
                </div>
              )}
            </div>
          </div>
        </div>
      )}

      {/* TAB 3: Rate Limits & IP Whitelisting */}
      {activeTab === 'quotas' && (
        <div className="bg-white border border-slate-200 rounded-xl p-6 shadow-2xs space-y-5">
          <div>
            <h3 className="text-base font-bold text-slate-900 flex items-center gap-2">
              <Sliders className="w-4 h-4 text-blue-600" />
              <span>Institutional Rate Limits & IP Subnet Whitelisting Rules</span>
            </h3>
            <p className="text-xs text-slate-500 mt-0.5">
              Configured policies preventing scraping engine overload while ensuring unthrottled access for critical national macro modeling.
            </p>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div className="p-4 rounded-xl border border-slate-200 bg-slate-50/50 space-y-2.5">
              <div className="flex items-center gap-2 text-xs font-bold text-slate-900">
                <Globe className="w-4 h-4 text-blue-600" />
                <span>NIC Cloud & Institutional Intranet Whitelist</span>
              </div>
              <p className="text-xs text-slate-600 leading-relaxed">
                Only IP address allocations registered under Government of India ASN blocks (<code className="font-mono text-blue-700">AS45820 National Informatics Centre</code>) or RBI intranet subnets are granted production token generation access.
              </p>
              <div className="pt-2">
                <span className="font-mono text-[11px] bg-white border border-slate-200 px-2 py-1 rounded text-slate-700 block">
                  Active CIDR Rules: 164.100.0.0/16, 10.24.0.0/16, 14.139.58.0/24
                </span>
              </div>
            </div>

            <div className="p-4 rounded-xl border border-slate-200 bg-slate-50/50 space-y-2.5">
              <div className="flex items-center gap-2 text-xs font-bold text-slate-900">
                <Clock className="w-4 h-4 text-purple-600" />
                <span>Adaptive Token-Bucket Rate Throttling</span>
              </div>
              <p className="text-xs text-slate-600 leading-relaxed">
                Requests are metered across a leaky-bucket algorithm with burst allowances up to 600 req/min for DGCA automated tariff crawlers and 300 req/min for RBI nowcasting feeds.
              </p>
              <div className="pt-2">
                <span className="font-mono text-[11px] bg-white border border-slate-200 px-2 py-1 rounded text-slate-700 block">
                  Burst Factor: 1.5× | Cooldown Window: 60s
                </span>
              </div>
            </div>
          </div>
        </div>
      )}

      {/* TAB 4: Security & CERT-In Protocol */}
      {activeTab === 'security' && (
        <div className="bg-white border border-slate-200 rounded-xl p-6 shadow-2xs space-y-4">
          <div>
            <h3 className="text-base font-bold text-slate-900 flex items-center gap-2">
              <Lock className="w-4 h-4 text-blue-600" />
              <span>National Cyber Security & CERT-In Compliance Architecture</span>
            </h3>
            <p className="text-xs text-slate-500 mt-0.5">
              Cryptographic and infrastructure guarantees ensuring zero data tampering and verifiable provenance.
            </p>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-3 gap-4 pt-2">
            <div className="p-4 rounded-xl border border-slate-200 bg-slate-50 space-y-1.5">
              <p className="text-sm font-bold text-slate-900">1. SHA-256 Checksum Provenance</p>
              <p className="text-xs text-slate-600 leading-relaxed">
                Every published API payload includes a cryptographic SHA-256 digital signature derived from the raw underlying airline quote observations.
              </p>
            </div>

            <div className="p-4 rounded-xl border border-slate-200 bg-slate-50 space-y-1.5">
              <p className="text-sm font-bold text-slate-900">2. TLS 1.3 Strict Transport</p>
              <p className="text-xs text-slate-600 leading-relaxed">
                Enforces HSTS (Strict-Transport-Security) with ECDHE key exchanges, rejecting legacy SSLv3 and TLS 1.0/1.1 handshakes.
              </p>
            </div>

            <div className="p-4 rounded-xl border border-slate-200 bg-slate-50 space-y-1.5">
              <p className="text-sm font-bold text-slate-900">3. Immutable Audit Trails</p>
              <p className="text-xs text-slate-600 leading-relaxed">
                Every institutional API access event is streamed to write-once append-only compliance logs preserving timestamps and caller IP identities.
              </p>
            </div>
          </div>
        </div>
      )}

      {/* Modal: Generate New Government Client Key */}
      {showGenerateModal && (
        <div className="fixed inset-0 z-50 bg-slate-900/60 backdrop-blur-xs flex items-center justify-center p-4">
          <div className="bg-white border border-slate-200 rounded-2xl max-w-lg w-full p-6 shadow-xl space-y-5 animate-in zoom-in-95">
            <div className="flex items-center justify-between border-b border-slate-100 pb-3">
              <div className="flex items-center gap-2">
                <div className="w-8 h-8 rounded-lg bg-blue-50 text-blue-700 flex items-center justify-center">
                  <Key className="w-4 h-4" />
                </div>
                <h3 className="text-base font-bold text-slate-900">Provision Government Client API Key</h3>
              </div>
              <button 
                onClick={() => setShowGenerateModal(false)}
                className="p-1 rounded-md text-slate-400 hover:text-slate-700 hover:bg-slate-100 cursor-pointer"
              >
                <X className="w-4 h-4" />
              </button>
            </div>

            <form onSubmit={handleGenerateKey} className="space-y-4 text-xs">
              <div className="space-y-1">
                <label className="font-bold text-slate-700">Client Institution Name</label>
                <input 
                  type="text" 
                  required
                  placeholder="e.g. State Department of Economics & Statistics (DES)"
                  value={newClientName}
                  onChange={(e) => setNewClientName(e.target.value)}
                  className="w-full bg-slate-50 border border-slate-200 rounded-lg p-2.5 focus:outline-none focus:border-blue-500 font-medium"
                />
              </div>

              <div className="space-y-1">
                <label className="font-bold text-slate-700">Parent Ministry / Department</label>
                <input 
                  type="text" 
                  placeholder="e.g. Government of Maharashtra / MoSPI NSO"
                  value={newMinistry}
                  onChange={(e) => setNewMinistry(e.target.value)}
                  className="w-full bg-slate-50 border border-slate-200 rounded-lg p-2.5 focus:outline-none focus:border-blue-500 font-medium"
                />
              </div>

              <div className="grid grid-cols-2 gap-3">
                <div className="space-y-1">
                  <label className="font-bold text-slate-700">Primary Authorization Scope</label>
                  <select
                    value={newScope}
                    onChange={(e) => setNewScope(e.target.value)}
                    className="w-full bg-slate-50 border border-slate-200 rounded-lg p-2.5 focus:outline-none focus:border-blue-500 font-medium"
                  >
                    <option value="apix:realtime">apix:realtime (Headline Feed)</option>
                    <option value="apix:backtest">apix:backtest (30-Day Series)</option>
                    <option value="nso:feed">nso:feed (CPI Ingestion)</option>
                    <option value="quotes:disaggregated">quotes:disaggregated (Micro-Data)</option>
                    <option value="*">* (Full Institutional Admin)</option>
                  </select>
                </div>

                <div className="space-y-1">
                  <label className="font-bold text-slate-700">Daily Request Quota</label>
                  <select
                    value={newQuota}
                    onChange={(e) => setNewQuota(e.target.value)}
                    className="w-full bg-slate-50 border border-slate-200 rounded-lg p-2.5 focus:outline-none focus:border-blue-500 font-medium"
                  >
                    <option value="25000">25,000 req / day</option>
                    <option value="50000">50,000 req / day</option>
                    <option value="100000">100,000 req / day</option>
                    <option value="250000">250,000 req / day</option>
                  </select>
                </div>
              </div>

              <div className="grid grid-cols-2 gap-3">
                <div className="space-y-1">
                  <label className="font-bold text-slate-700">Rate Limit (req / min)</label>
                  <input 
                    type="number"
                    value={newRateLimit}
                    onChange={(e) => setNewRateLimit(e.target.value)}
                    className="w-full bg-slate-50 border border-slate-200 rounded-lg p-2.5 focus:outline-none focus:border-blue-500 font-medium"
                  />
                </div>

                <div className="space-y-1">
                  <label className="font-bold text-slate-700">Whitelisted Subnet Range</label>
                  <input 
                    type="text"
                    value={newIpSubnet}
                    onChange={(e) => setNewIpSubnet(e.target.value)}
                    placeholder="e.g. 164.100.0.0/16"
                    className="w-full bg-slate-50 border border-slate-200 rounded-lg p-2.5 focus:outline-none focus:border-blue-500 font-medium font-mono"
                  />
                </div>
              </div>

              <div className="p-3 bg-blue-50 border border-blue-200 rounded-lg text-[11px] text-blue-900 space-y-1">
                <p className="font-bold">Security Notice:</p>
                <p>Generating this key creates a 256-bit cryptographic token valid for 24 months. Ensure the recipient is verified under institutional government email credentials.</p>
              </div>

              <div className="flex items-center justify-end gap-2 pt-2 border-t border-slate-100">
                <button
                  type="button"
                  onClick={() => setShowGenerateModal(false)}
                  className="px-4 py-2 rounded-lg border border-slate-200 text-slate-700 font-semibold hover:bg-slate-50 cursor-pointer"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  className="px-4 py-2 rounded-lg bg-blue-600 hover:bg-blue-700 text-white font-semibold cursor-pointer shadow-2xs"
                >
                  Confirm & Provision Key
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
};
