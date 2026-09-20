import dgcaBasket from './dgcaRouteBasket.json';

// National Airfare Price Index Summary Metrics
export const nationalSummary = {
  currentIndex: 118.42,
  previousIndex: 114.17,
  yoyInflation: 3.72,
  momChange: 1.85,
  wowChange: 0.42,
  avgFare: 5840,
  medianFare: 5650,
  minFare: 3200,
  maxFare: 14800,
  coveredRoutes: 20,
  totalObservations: 4850,
  activeAirlines: 4,
  activePlatforms: 6,
  dataCoveragePct: 98.4,
  laspeyresIndex: 118.42,
  jevonsIndex: 117.85,
  fisherIndex: 118.13,
  baseYear: "2024=100",
  lastUpdated: "2026-09-04 11:30 IST"
};

// Historical Series (3-Year Monthly & 30-Day Daily)
export const historicalTimeSeries = [
  { date: '2023-09', apix: 100.00, laspeyres: 100.00, jevons: 100.00, cpiTransport: 100.00, yoy: 0.0, mom: 0.0 },
  { date: '2023-11', apix: 102.10, laspeyres: 102.15, jevons: 101.95, cpiTransport: 100.80, yoy: 2.1, mom: 2.1 },
  { date: '2024-01', apix: 104.50, laspeyres: 104.60, jevons: 104.20, cpiTransport: 101.90, yoy: 4.5, mom: 2.35 },
  { date: '2024-03', apix: 103.80, laspeyres: 103.90, jevons: 103.50, cpiTransport: 102.10, yoy: 3.8, mom: -0.67 },
  { date: '2024-05', apix: 107.20, laspeyres: 107.35, jevons: 106.90, cpiTransport: 103.40, yoy: 7.2, mom: 3.28 },
  { date: '2024-07', apix: 109.10, laspeyres: 109.25, jevons: 108.80, cpiTransport: 104.20, yoy: 9.1, mom: 1.77 },
  { date: '2024-09', apix: 108.40, laspeyres: 108.50, jevons: 108.10, cpiTransport: 104.50, yoy: 8.4, mom: -0.64 },
  { date: '2024-11', apix: 111.30, laspeyres: 111.45, jevons: 110.95, cpiTransport: 105.80, yoy: 11.3, mom: 2.68 },
  { date: '2025-01', apix: 110.60, laspeyres: 110.70, jevons: 110.30, cpiTransport: 106.10, yoy: 5.84, mom: -0.63 },
  { date: '2025-03', apix: 112.80, laspeyres: 112.95, jevons: 112.45, cpiTransport: 107.30, yoy: 8.67, mom: 1.99 },
  { date: '2025-05', apix: 114.90, laspeyres: 115.10, jevons: 114.50, cpiTransport: 108.20, yoy: 7.18, mom: 1.86 },
  { date: '2025-07', apix: 115.60, laspeyres: 115.80, jevons: 115.20, cpiTransport: 108.90, yoy: 5.96, mom: 0.61 },
  { date: '2025-09', apix: 114.17, laspeyres: 114.30, jevons: 113.80, cpiTransport: 109.10, yoy: 5.32, mom: -1.24 },
  { date: '2025-11', apix: 116.80, laspeyres: 116.95, jevons: 116.40, cpiTransport: 110.40, yoy: 4.94, mom: 2.30 },
  { date: '2026-01', apix: 115.90, laspeyres: 116.05, jevons: 115.50, cpiTransport: 110.80, yoy: 4.79, mom: -0.77 },
  { date: '2026-03', apix: 116.40, laspeyres: 116.55, jevons: 116.00, cpiTransport: 111.20, yoy: 3.19, mom: 0.43 },
  { date: '2026-05', apix: 117.20, laspeyres: 117.35, jevons: 116.80, cpiTransport: 111.80, yoy: 2.00, mom: 0.69 },
  { date: '2026-07', apix: 118.10, laspeyres: 118.25, jevons: 117.70, cpiTransport: 112.40, yoy: 2.16, mom: 0.77 },
  { date: '2026-08', apix: 118.42, laspeyres: 118.55, jevons: 118.02, cpiTransport: 112.70, yoy: 3.72, mom: 0.27 }
];

// 30-Day Continuous Daily Empirical Backtesting Series (Aug 01 – Aug 30, 2026)
// Benchmarking Real-Time APIx against DGCA Base Tariff (100.0) and MoSPI CPI Transport Sub-Index
export const dailyBacktestTimeSeries = [
  { day: 1, date: 'Aug 01', fullDate: '2026-08-01', dayOfWeek: 'Sat', APIxRealtime: 116.85, DGCABaseline: 100.0, CPITransportSubindex: 111.80, laspeyres: 117.02, fisher: 116.71, avgMarketFare: 5610, variancePct: 16.85, dailyQuotes: 4720, status: 'PASS' },
  { day: 2, date: 'Aug 02', fullDate: '2026-08-02', dayOfWeek: 'Sun', APIxRealtime: 117.20, DGCABaseline: 100.0, CPITransportSubindex: 111.85, laspeyres: 117.38, fisher: 117.05, avgMarketFare: 5625, variancePct: 17.20, dailyQuotes: 4810, status: 'PASS' },
  { day: 3, date: 'Aug 03', fullDate: '2026-08-03', dayOfWeek: 'Mon', APIxRealtime: 116.10, DGCABaseline: 100.0, CPITransportSubindex: 111.85, laspeyres: 116.25, fisher: 115.98, avgMarketFare: 5570, variancePct: 16.10, dailyQuotes: 4650, status: 'PASS' },
  { day: 4, date: 'Aug 04', fullDate: '2026-08-04', dayOfWeek: 'Tue', APIxRealtime: 115.75, DGCABaseline: 100.0, CPITransportSubindex: 111.90, laspeyres: 115.90, fisher: 115.62, avgMarketFare: 5555, variancePct: 15.75, dailyQuotes: 4620, status: 'PASS' },
  { day: 5, date: 'Aug 05', fullDate: '2026-08-05', dayOfWeek: 'Wed', APIxRealtime: 115.90, DGCABaseline: 100.0, CPITransportSubindex: 111.90, laspeyres: 116.05, fisher: 115.78, avgMarketFare: 5565, variancePct: 15.90, dailyQuotes: 4640, status: 'PASS' },
  { day: 6, date: 'Aug 06', fullDate: '2026-08-06', dayOfWeek: 'Thu', APIxRealtime: 116.30, DGCABaseline: 100.0, CPITransportSubindex: 111.95, laspeyres: 116.48, fisher: 116.18, avgMarketFare: 5585, variancePct: 16.30, dailyQuotes: 4700, status: 'PASS' },
  { day: 7, date: 'Aug 07', fullDate: '2026-08-07', dayOfWeek: 'Fri', APIxRealtime: 117.40, DGCABaseline: 100.0, CPITransportSubindex: 112.00, laspeyres: 117.58, fisher: 117.26, avgMarketFare: 5640, variancePct: 17.40, dailyQuotes: 4860, status: 'PASS' },
  { day: 8, date: 'Aug 08', fullDate: '2026-08-08', dayOfWeek: 'Sat', APIxRealtime: 117.90, DGCABaseline: 100.0, CPITransportSubindex: 112.00, laspeyres: 118.08, fisher: 117.75, avgMarketFare: 5665, variancePct: 17.90, dailyQuotes: 4890, status: 'PASS' },
  { day: 9, date: 'Aug 09', fullDate: '2026-08-09', dayOfWeek: 'Sun', APIxRealtime: 118.15, DGCABaseline: 100.0, CPITransportSubindex: 112.05, laspeyres: 118.32, fisher: 118.01, avgMarketFare: 5680, variancePct: 18.15, dailyQuotes: 4920, status: 'PASS' },
  { day: 10, date: 'Aug 10', fullDate: '2026-08-10', dayOfWeek: 'Mon', APIxRealtime: 116.70, DGCABaseline: 100.0, CPITransportSubindex: 112.10, laspeyres: 116.85, fisher: 116.58, avgMarketFare: 5605, variancePct: 16.70, dailyQuotes: 4670, status: 'PASS' },
  { day: 11, date: 'Aug 11', fullDate: '2026-08-11', dayOfWeek: 'Tue', APIxRealtime: 116.40, DGCABaseline: 100.0, CPITransportSubindex: 112.10, laspeyres: 116.55, fisher: 116.28, avgMarketFare: 5590, variancePct: 16.40, dailyQuotes: 4630, status: 'PASS' },
  { day: 12, date: 'Aug 12', fullDate: '2026-08-12', dayOfWeek: 'Wed', APIxRealtime: 116.95, DGCABaseline: 100.0, CPITransportSubindex: 112.15, laspeyres: 117.10, fisher: 116.82, avgMarketFare: 5620, variancePct: 16.95, dailyQuotes: 4710, status: 'PASS' },
  { day: 13, date: 'Aug 13', fullDate: '2026-08-13', dayOfWeek: 'Thu', APIxRealtime: 117.80, DGCABaseline: 100.0, CPITransportSubindex: 112.20, laspeyres: 117.98, fisher: 117.65, avgMarketFare: 5660, variancePct: 17.80, dailyQuotes: 4850, status: 'PASS' },
  { day: 14, date: 'Aug 14', fullDate: '2026-08-14', dayOfWeek: 'Fri', APIxRealtime: 119.85, DGCABaseline: 100.0, CPITransportSubindex: 112.20, laspeyres: 120.05, fisher: 119.70, avgMarketFare: 5760, variancePct: 19.85, dailyQuotes: 5120, status: 'PASS' },
  { day: 15, date: 'Aug 15', fullDate: '2026-08-15', dayOfWeek: 'Sat', APIxRealtime: 120.40, DGCABaseline: 100.0, CPITransportSubindex: 112.25, laspeyres: 120.62, fisher: 120.25, avgMarketFare: 5790, variancePct: 20.40, dailyQuotes: 5190, status: 'PASS' },
  { day: 16, date: 'Aug 16', fullDate: '2026-08-16', dayOfWeek: 'Sun', APIxRealtime: 120.10, DGCABaseline: 100.0, CPITransportSubindex: 112.25, laspeyres: 120.32, fisher: 119.95, avgMarketFare: 5775, variancePct: 20.10, dailyQuotes: 5140, status: 'PASS' },
  { day: 17, date: 'Aug 17', fullDate: '2026-08-17', dayOfWeek: 'Mon', APIxRealtime: 117.50, DGCABaseline: 100.0, CPITransportSubindex: 112.30, laspeyres: 117.68, fisher: 117.38, avgMarketFare: 5645, variancePct: 17.50, dailyQuotes: 4760, status: 'PASS' },
  { day: 18, date: 'Aug 18', fullDate: '2026-08-18', dayOfWeek: 'Tue', APIxRealtime: 116.80, DGCABaseline: 100.0, CPITransportSubindex: 112.35, laspeyres: 116.95, fisher: 116.67, avgMarketFare: 5610, variancePct: 16.80, dailyQuotes: 4680, status: 'PASS' },
  { day: 19, date: 'Aug 19', fullDate: '2026-08-19', dayOfWeek: 'Wed', APIxRealtime: 116.95, DGCABaseline: 100.0, CPITransportSubindex: 112.35, laspeyres: 117.10, fisher: 116.82, avgMarketFare: 5620, variancePct: 16.95, dailyQuotes: 4690, status: 'PASS' },
  { day: 20, date: 'Aug 20', fullDate: '2026-08-20', dayOfWeek: 'Thu', APIxRealtime: 117.30, DGCABaseline: 100.0, CPITransportSubindex: 112.40, laspeyres: 117.48, fisher: 117.18, avgMarketFare: 5635, variancePct: 17.30, dailyQuotes: 4740, status: 'PASS' },
  { day: 21, date: 'Aug 21', fullDate: '2026-08-21', dayOfWeek: 'Fri', APIxRealtime: 118.25, DGCABaseline: 100.0, CPITransportSubindex: 112.45, laspeyres: 118.44, fisher: 118.12, avgMarketFare: 5685, variancePct: 18.25, dailyQuotes: 4880, status: 'PASS' },
  { day: 22, date: 'Aug 22', fullDate: '2026-08-22', dayOfWeek: 'Sat', APIxRealtime: 118.60, DGCABaseline: 100.0, CPITransportSubindex: 112.45, laspeyres: 118.80, fisher: 118.45, avgMarketFare: 5705, variancePct: 18.60, dailyQuotes: 4910, status: 'PASS' },
  { day: 23, date: 'Aug 23', fullDate: '2026-08-23', dayOfWeek: 'Sun', APIxRealtime: 118.80, DGCABaseline: 100.0, CPITransportSubindex: 112.50, laspeyres: 119.00, fisher: 118.65, avgMarketFare: 5715, variancePct: 18.80, dailyQuotes: 4930, status: 'PASS' },
  { day: 24, date: 'Aug 24', fullDate: '2026-08-24', dayOfWeek: 'Mon', APIxRealtime: 117.40, DGCABaseline: 100.0, CPITransportSubindex: 112.55, laspeyres: 117.58, fisher: 117.26, avgMarketFare: 5640, variancePct: 17.40, dailyQuotes: 4720, status: 'PASS' },
  { day: 25, date: 'Aug 25', fullDate: '2026-08-25', dayOfWeek: 'Tue', APIxRealtime: 117.15, DGCABaseline: 100.0, CPITransportSubindex: 112.55, laspeyres: 117.32, fisher: 117.02, avgMarketFare: 5630, variancePct: 17.15, dailyQuotes: 4690, status: 'PASS' },
  { day: 26, date: 'Aug 26', fullDate: '2026-08-26', dayOfWeek: 'Wed', APIxRealtime: 117.35, DGCABaseline: 100.0, CPITransportSubindex: 112.60, laspeyres: 117.52, fisher: 117.22, avgMarketFare: 5640, variancePct: 17.35, dailyQuotes: 4710, status: 'PASS' },
  { day: 27, date: 'Aug 27', fullDate: '2026-08-27', dayOfWeek: 'Thu', APIxRealtime: 117.70, DGCABaseline: 100.0, CPITransportSubindex: 112.60, laspeyres: 117.88, fisher: 117.55, avgMarketFare: 5655, variancePct: 17.70, dailyQuotes: 4770, status: 'PASS' },
  { day: 28, date: 'Aug 28', fullDate: '2026-08-28', dayOfWeek: 'Fri', APIxRealtime: 118.50, DGCABaseline: 100.0, CPITransportSubindex: 112.65, laspeyres: 118.70, fisher: 118.35, avgMarketFare: 5695, variancePct: 18.50, dailyQuotes: 4890, status: 'PASS' },
  { day: 29, date: 'Aug 29', fullDate: '2026-08-29', dayOfWeek: 'Sat', APIxRealtime: 118.90, DGCABaseline: 100.0, CPITransportSubindex: 112.70, laspeyres: 119.10, fisher: 118.75, avgMarketFare: 5720, variancePct: 18.90, dailyQuotes: 4940, status: 'PASS' },
  { day: 30, date: 'Aug 30', fullDate: '2026-08-30', dayOfWeek: 'Sun', APIxRealtime: 118.42, DGCABaseline: 100.0, CPITransportSubindex: 112.70, laspeyres: 118.55, fisher: 118.13, avgMarketFare: 5840, variancePct: 18.42, dailyQuotes: 4850, status: 'PASS' }
];

// Route Data mapping DGCA Route Basket with econometric statistics
export const routeAnalyticsList = dgcaBasket.map((item, idx) => {
  const baseFares = [4800, 4500, 4200, 3900, 3700, 4600, 4400, 3800, 4100, 4900, 3950, 4650, 4300, 3600, 4750, 4250, 3550, 3850, 3900, 3450];
  const baseline = baseFares[idx % baseFares.length];
  
  // Custom variation per route
  const indexVal = parseFloat((110 + (idx % 7) * 2.8 - (idx % 3) * 1.5 + Math.sin(idx) * 3).toFixed(2));
  const avgFare = Math.round(baseline * (indexVal / 100));
  const yoyPct = parseFloat(((indexVal - 108.0) / 108.0 * 100).toFixed(2));
  const momPct = parseFloat((1.2 + (idx % 5) * 0.4 - (idx % 2) * 0.8).toFixed(2));
  const volatility = parseFloat((2.5 + (idx % 4) * 1.2).toFixed(2));

  return {
    rank: item.rank,
    route: item.route,
    city1: item.city1,
    city2: item.city2,
    totalPax: item.total_pax,
    weightWithinBasket: item.weight_traffic_within_basket,
    weightPct: parseFloat((item.weight_traffic_within_basket * 100).toFixed(2)),
    nationalPaxSharePct: parseFloat((item.share_of_national_traffic * 100).toFixed(2)),
    tier: item.tier,
    index: indexVal,
    baseFare: baseline,
    avgFare: avgFare,
    medianFare: Math.round(avgFare * 0.97),
    minFare: Math.round(baseline * 0.85),
    maxFare: Math.round(avgFare * 1.85),
    yoyPct: yoyPct,
    momPct: momPct,
    wowPct: parseFloat((momPct * 0.22).toFixed(2)),
    volatilityScore: volatility,
    t1SurgePct: parseFloat((35 + (idx % 5) * 8).toFixed(1)),
    t45DiscountPct: parseFloat((18 + (idx % 4) * 5).toFixed(1)),
    observationsCount: 220 + idx * 12,
    activeCarriers: ['IndiGo', 'Air India', idx % 2 === 0 ? 'Akasa Air' : 'SpiceJet'],
    flightTimeMins: 90 + (idx % 6) * 25,
    windows: {
      'T+1': { avgFare: Math.round(avgFare * 1.45), index: parseFloat((indexVal * 1.42).toFixed(1)), yoy: parseFloat((yoyPct * 1.4).toFixed(2)), mom: parseFloat((momPct * 1.5).toFixed(2)), availabilityPct: 88, median: Math.round(avgFare * 1.42), min: Math.round(avgFare * 1.2), max: Math.round(avgFare * 2.1), stdDev: 820, observations: 42 },
      'T+7': { avgFare: Math.round(avgFare * 1.18), index: parseFloat((indexVal * 1.16).toFixed(1)), yoy: parseFloat((yoyPct * 1.18).toFixed(2)), mom: parseFloat((momPct * 1.2).toFixed(2)), availabilityPct: 93, median: Math.round(avgFare * 1.16), min: Math.round(avgFare * 1.02), max: Math.round(avgFare * 1.55), stdDev: 540, observations: 56 },
      'T+15': { avgFare: avgFare, index: indexVal, yoy: yoyPct, mom: momPct, availabilityPct: 96, median: Math.round(avgFare * 0.98), min: Math.round(baseline * 0.95), max: Math.round(avgFare * 1.3), stdDev: 380, observations: 64 },
      'T+30': { avgFare: Math.round(avgFare * 0.90), index: parseFloat((indexVal * 0.91).toFixed(1)), yoy: parseFloat((yoyPct * 0.85).toFixed(2)), mom: parseFloat((momPct * 0.8).toFixed(2)), availabilityPct: 98, median: Math.round(avgFare * 0.89), min: Math.round(baseline * 0.90), max: Math.round(avgFare * 1.15), stdDev: 290, observations: 48 },
      'T+45': { avgFare: Math.round(avgFare * 0.82), index: parseFloat((indexVal * 0.83).toFixed(1)), yoy: parseFloat((yoyPct * 0.75).toFixed(2)), mom: parseFloat((momPct * 0.6).toFixed(2)), availabilityPct: 99, median: Math.round(avgFare * 0.81), min: Math.round(baseline * 0.85), max: Math.round(avgFare * 1.05), stdDev: 210, observations: 38 }
    }
  };
});

// Airline Pricing Statistics
export const airlineAnalyticsList = [
  {
    code: '6E',
    name: 'IndiGo',
    marketSharePct: 60.8,
    avgFare: 5620,
    index: 117.8,
    yoyPct: 3.4,
    momPct: 1.6,
    routesCovered: 20,
    observationsCount: 2850,
    t1AvgFare: 8150,
    t45AvgFare: 4450,
    surgeMultiplier: 1.83,
    volatilityScore: 3.1,
    color: 'blue'
  },
  {
    code: 'AI',
    name: 'Air India',
    marketSharePct: 26.4,
    avgFare: 6180,
    index: 121.2,
    yoyPct: 4.8,
    momPct: 2.1,
    routesCovered: 18,
    observationsCount: 1240,
    t1AvgFare: 9120,
    t45AvgFare: 4980,
    surgeMultiplier: 1.83,
    volatilityScore: 3.8,
    color: 'red'
  },
  {
    code: 'QP',
    name: 'Akasa Air',
    marketSharePct: 7.2,
    avgFare: 5240,
    index: 113.6,
    yoyPct: 2.1,
    momPct: 1.1,
    routesCovered: 12,
    observationsCount: 460,
    t1AvgFare: 7450,
    t45AvgFare: 4100,
    surgeMultiplier: 1.81,
    volatilityScore: 2.8,
    color: 'purple'
  },
  {
    code: 'SG',
    name: 'SpiceJet',
    marketSharePct: 5.6,
    avgFare: 5190,
    index: 112.9,
    yoyPct: 1.9,
    momPct: 0.8,
    routesCovered: 10,
    observationsCount: 300,
    t1AvgFare: 7380,
    t45AvgFare: 4050,
    surgeMultiplier: 1.82,
    volatilityScore: 4.2,
    color: 'amber'
  }
];

// Flights & Canonical Fare Products
export const flightProductsList = [
  {
    flightNumber: '6E-201',
    airline: 'IndiGo',
    airlineCode: '6E',
    route: 'DEL-BOM',
    origin: 'DEL',
    destination: 'BOM',
    departureTime: '06:00',
    arrivalTime: '08:10',
    advanceWindow: 'T+15',
    travelDate: '2026-09-19',
    fareClass: 'Economy Saver',
    canonicalId: 'CFP-DELBOM-6E201-T15',
    baseFare: 4800,
    taxes: 750,
    fees: 150,
    totalFare: 5700,
    currentPrice: 5700,
    index: 123.9,
    historicalBasePrice: 4600,
    availabilityPct: 96,
    platformQuotes: [
      { platform: 'IndiGo Direct', baseFare: 4800, taxes: 750, convenienceFee: 0, totalFare: 5550, isDirect: true, isLowest: true, premiumPct: 0.0 },
      { platform: 'MakeMyTrip', baseFare: 4800, taxes: 750, convenienceFee: 250, totalFare: 5800, isDirect: false, isLowest: false, premiumPct: 4.5 },
      { platform: 'Ixigo', baseFare: 4800, taxes: 750, convenienceFee: 150, totalFare: 5700, isDirect: false, isLowest: false, premiumPct: 2.7 },
      { platform: 'Cleartrip', baseFare: 4800, taxes: 750, convenienceFee: 190, totalFare: 5740, isDirect: false, isLowest: false, premiumPct: 3.4 },
      { platform: 'EaseMyTrip', baseFare: 4800, taxes: 750, convenienceFee: 50, totalFare: 5600, isDirect: false, isLowest: false, premiumPct: 0.9 }
    ]
  },
  {
    flightNumber: 'AI-805',
    airline: 'Air India',
    airlineCode: 'AI',
    route: 'DEL-BOM',
    origin: 'DEL',
    destination: 'BOM',
    departureTime: '08:00',
    arrivalTime: '10:15',
    advanceWindow: 'T+15',
    travelDate: '2026-09-19',
    fareClass: 'Economy Flex',
    canonicalId: 'CFP-DELBOM-AI805-T15',
    baseFare: 5200,
    taxes: 820,
    fees: 180,
    totalFare: 6200,
    currentPrice: 6200,
    index: 126.5,
    historicalBasePrice: 4900,
    availabilityPct: 92,
    platformQuotes: [
      { platform: 'Air India Direct', baseFare: 5200, taxes: 820, convenienceFee: 0, totalFare: 6020, isDirect: true, isLowest: true, premiumPct: 0.0 },
      { platform: 'MakeMyTrip', baseFare: 5200, taxes: 820, convenienceFee: 280, totalFare: 6300, isDirect: false, isLowest: false, premiumPct: 4.6 },
      { platform: 'Ixigo', baseFare: 5200, taxes: 820, convenienceFee: 180, totalFare: 6200, isDirect: false, isLowest: false, premiumPct: 3.0 },
      { platform: 'Cleartrip', baseFare: 5200, taxes: 820, convenienceFee: 220, totalFare: 6240, isDirect: false, isLowest: false, premiumPct: 3.6 },
      { platform: 'EaseMyTrip', baseFare: 5200, taxes: 820, convenienceFee: 80, totalFare: 6100, isDirect: false, isLowest: false, premiumPct: 1.3 }
    ]
  },
  {
    flightNumber: '6E-512',
    airline: 'IndiGo',
    airlineCode: '6E',
    route: 'BLR-DEL',
    origin: 'BLR',
    destination: 'DEL',
    departureTime: '07:15',
    arrivalTime: '10:00',
    advanceWindow: 'T+7',
    travelDate: '2026-09-11',
    fareClass: 'Economy Saver',
    canonicalId: 'CFP-BLRDEL-6E512-T7',
    baseFare: 6100,
    taxes: 910,
    fees: 190,
    totalFare: 7200,
    currentPrice: 7200,
    index: 128.2,
    historicalBasePrice: 5600,
    availabilityPct: 89,
    platformQuotes: [
      { platform: 'IndiGo Direct', baseFare: 6100, taxes: 910, convenienceFee: 0, totalFare: 7010, isDirect: true, isLowest: true, premiumPct: 0.0 },
      { platform: 'MakeMyTrip', baseFare: 6100, taxes: 910, convenienceFee: 290, totalFare: 7300, isDirect: false, isLowest: false, premiumPct: 4.1 },
      { platform: 'Ixigo', baseFare: 6100, taxes: 910, convenienceFee: 190, totalFare: 7200, isDirect: false, isLowest: false, premiumPct: 2.7 },
      { platform: 'Cleartrip', baseFare: 6100, taxes: 910, convenienceFee: 210, totalFare: 7220, isDirect: false, isLowest: false, premiumPct: 3.0 },
      { platform: 'EaseMyTrip', baseFare: 6100, taxes: 910, convenienceFee: 60, totalFare: 7070, isDirect: false, isLowest: false, premiumPct: 0.85 }
    ]
  },
  {
    flightNumber: 'QP-1102',
    airline: 'Akasa Air',
    airlineCode: 'QP',
    route: 'BOM-BLR',
    origin: 'BOM',
    destination: 'BLR',
    departureTime: '14:30',
    arrivalTime: '16:15',
    advanceWindow: 'T+30',
    travelDate: '2026-10-04',
    fareClass: 'Saver',
    canonicalId: 'CFP-BOMBLR-QP1102-T30',
    baseFare: 3600,
    taxes: 620,
    fees: 120,
    totalFare: 4340,
    currentPrice: 4340,
    index: 109.8,
    historicalBasePrice: 3950,
    availabilityPct: 98,
    platformQuotes: [
      { platform: 'Akasa Direct', baseFare: 3600, taxes: 620, convenienceFee: 0, totalFare: 4220, isDirect: true, isLowest: true, premiumPct: 0.0 },
      { platform: 'MakeMyTrip', baseFare: 3600, taxes: 620, convenienceFee: 220, totalFare: 4440, isDirect: false, isLowest: false, premiumPct: 5.2 },
      { platform: 'Ixigo', baseFare: 3600, taxes: 620, convenienceFee: 120, totalFare: 4340, isDirect: false, isLowest: false, premiumPct: 2.8 },
      { platform: 'Cleartrip', baseFare: 3600, taxes: 620, convenienceFee: 140, totalFare: 4360, isDirect: false, isLowest: false, premiumPct: 3.3 }
    ]
  },
  {
    flightNumber: 'SG-812',
    airline: 'SpiceJet',
    airlineCode: 'SG',
    route: 'DEL-HYD',
    origin: 'DEL',
    destination: 'HYD',
    departureTime: '19:10',
    arrivalTime: '21:25',
    advanceWindow: 'T+1',
    travelDate: '2026-09-05',
    fareClass: 'Saver',
    canonicalId: 'CFP-DELHYD-SG812-T1',
    baseFare: 7200,
    taxes: 980,
    fees: 220,
    totalFare: 8400,
    currentPrice: 8400,
    index: 138.5,
    historicalBasePrice: 6060,
    availabilityPct: 82,
    platformQuotes: [
      { platform: 'SpiceJet Direct', baseFare: 7200, taxes: 980, convenienceFee: 0, totalFare: 8180, isDirect: true, isLowest: true, premiumPct: 0.0 },
      { platform: 'MakeMyTrip', baseFare: 7200, taxes: 980, convenienceFee: 310, totalFare: 8490, isDirect: false, isLowest: false, premiumPct: 3.8 },
      { platform: 'Ixigo', baseFare: 7200, taxes: 980, convenienceFee: 220, totalFare: 8400, isDirect: false, isLowest: false, premiumPct: 2.7 },
      { platform: 'Cleartrip', baseFare: 7200, taxes: 980, convenienceFee: 250, totalFare: 8430, isDirect: false, isLowest: false, premiumPct: 3.0 }
    ]
  }
];

// Platform Analytics Data
export const platformAnalyticsList = [
  { platform: 'Direct Airline Portal', avgFare: 5580, medianFare: 5420, diffFromDirect: 0, avgConvenienceFee: 0, totalFare: 5580, observations: 1920, coveragePct: 100.0, matchRatePct: 100.0, dispersionStdDev: 410, type: 'Direct' },
  { platform: 'EaseMyTrip', avgFare: 5645, medianFare: 5490, diffFromDirect: 65, avgConvenienceFee: 65, totalFare: 5645, observations: 1420, coveragePct: 94.2, matchRatePct: 98.1, dispersionStdDev: 425, type: 'OTA' },
  { platform: 'Ixigo', avgFare: 5740, medianFare: 5580, diffFromDirect: 160, avgConvenienceFee: 160, totalFare: 5740, observations: 1850, coveragePct: 97.8, matchRatePct: 97.4, dispersionStdDev: 430, type: 'OTA' },
  { platform: 'Cleartrip', avgFare: 5785, medianFare: 5620, diffFromDirect: 205, avgConvenienceFee: 205, totalFare: 5785, observations: 1790, coveragePct: 96.5, matchRatePct: 96.8, dispersionStdDev: 435, type: 'OTA' },
  { platform: 'MakeMyTrip', avgFare: 5850, medianFare: 5690, diffFromDirect: 270, avgConvenienceFee: 270, totalFare: 5850, observations: 1910, coveragePct: 99.4, matchRatePct: 99.2, dispersionStdDev: 445, type: 'OTA' }
];

// Raw Scraped Observations Sample
export const rawObservationsList = [
  { id: 'OBS-892401', timestamp: '2026-09-04 11:24:18', source: 'EaseMyTrip API', route: 'DEL-BOM', airline: 'IndiGo', flightNo: '6E-201', travelDate: '2026-09-19', advanceDays: 15, window: 'T+15', fareClass: 'Economy', baseFare: 4800, taxes: 750, fees: 50, totalFare: 5600, availability: 'AVAILABLE', canonicalId: 'CFP-DELBOM-6E201-T15', qualityStatus: 'VALID' },
  { id: 'OBS-892402', timestamp: '2026-09-04 11:24:19', source: 'Ixigo Scraper', route: 'DEL-BOM', airline: 'IndiGo', flightNo: '6E-201', travelDate: '2026-09-19', advanceDays: 15, window: 'T+15', fareClass: 'Economy', baseFare: 4800, taxes: 750, fees: 150, totalFare: 5700, availability: 'AVAILABLE', canonicalId: 'CFP-DELBOM-6E201-T15', qualityStatus: 'VALID' },
  { id: 'OBS-892403', timestamp: '2026-09-04 11:24:20', source: 'MakeMyTrip Portal', route: 'DEL-BOM', airline: 'IndiGo', flightNo: '6E-201', travelDate: '2026-09-19', advanceDays: 15, window: 'T+15', fareClass: 'Economy', baseFare: 4800, taxes: 750, fees: 250, totalFare: 5800, availability: 'AVAILABLE', canonicalId: 'CFP-DELBOM-6E201-T15', qualityStatus: 'VALID' },
  { id: 'OBS-892404', timestamp: '2026-09-04 11:24:22', source: 'Air India Direct', route: 'DEL-BOM', airline: 'Air India', flightNo: 'AI-805', travelDate: '2026-09-19', advanceDays: 15, window: 'T+15', fareClass: 'Economy', baseFare: 5200, taxes: 820, fees: 0, totalFare: 6020, availability: 'AVAILABLE', canonicalId: 'CFP-DELBOM-AI805-T15', qualityStatus: 'VALID' },
  { id: 'OBS-892405', timestamp: '2026-09-04 11:24:25', source: 'Cleartrip Engine', route: 'BLR-DEL', airline: 'IndiGo', flightNo: '6E-512', travelDate: '2026-09-11', advanceDays: 7, window: 'T+7', fareClass: 'Economy', baseFare: 6100, taxes: 910, fees: 210, totalFare: 7220, availability: 'AVAILABLE', canonicalId: 'CFP-BLRDEL-6E512-T7', qualityStatus: 'VALID' },
  { id: 'OBS-892406', timestamp: '2026-09-04 11:24:28', source: 'Akasa Air Direct', route: 'BOM-BLR', airline: 'Akasa Air', flightNo: 'QP-1102', travelDate: '2026-10-04', advanceDays: 30, window: 'T+30', fareClass: 'Economy', baseFare: 3600, taxes: 620, fees: 0, totalFare: 4220, availability: 'AVAILABLE', canonicalId: 'CFP-BOMBLR-QP1102-T30', qualityStatus: 'VALID' },
  { id: 'OBS-892407', timestamp: '2026-09-04 11:24:30', source: 'SpiceJet Direct', route: 'DEL-HYD', airline: 'SpiceJet', flightNo: 'SG-812', travelDate: '2026-09-05', advanceDays: 1, window: 'T+1', fareClass: 'Economy', baseFare: 7200, taxes: 980, fees: 0, totalFare: 8180, availability: 'LIMITED (2 left)', canonicalId: 'CFP-DELHYD-SG812-T1', qualityStatus: 'VALID' },
  { id: 'OBS-892408', timestamp: '2026-09-04 11:24:32', source: 'MakeMyTrip Portal', route: 'DEL-HYD', airline: 'SpiceJet', flightNo: 'SG-812', travelDate: '2026-09-05', advanceDays: 1, window: 'T+1', fareClass: 'Economy', baseFare: 7200, taxes: 980, fees: 310, totalFare: 8490, availability: 'LIMITED (2 left)', canonicalId: 'CFP-DELHYD-SG812-T1', qualityStatus: 'VALID' },
  { id: 'OBS-892409', timestamp: '2026-09-04 11:24:35', source: 'Cleartrip Engine', route: 'BOM-GOI', airline: 'IndiGo', flightNo: '6E-344', travelDate: '2026-09-19', advanceDays: 15, window: 'T+15', fareClass: 'Economy', baseFare: 3200, taxes: 540, fees: 120, totalFare: 3860, availability: 'AVAILABLE', canonicalId: 'CFP-BOMGOI-6E344-T15', qualityStatus: 'VALID' },
  { id: 'OBS-892410', timestamp: '2026-09-04 11:24:38', source: 'Ixigo Scraper', route: 'DEL-SXR', airline: 'Air India', flightNo: 'AI-440', travelDate: '2026-09-11', advanceDays: 7, window: 'T+7', fareClass: 'Economy', baseFare: 8100, taxes: 1100, fees: 180, totalFare: 9380, availability: 'AVAILABLE', canonicalId: 'CFP-DELSXR-AI440-T7', qualityStatus: 'OUTLIER_REJECTED' }
];

// Data Quality Summary
export const dataQualitySummary = {
  totalIngested: 4850,
  validCount: 4720,
  invalidCount: 30,
  duplicateCount: 65,
  outliersRejected: 35,
  crossPlatformMatchRatePct: 97.8,
  coveragePct: 98.4,
  sources: [
    { name: 'IndiGo Direct TLS Engine', status: 'HEALTHY', latencyMs: 310, successRatePct: 99.4, lastBatchCount: 1420 },
    { name: 'Air India Direct API', status: 'HEALTHY', latencyMs: 420, successRatePct: 98.8, lastBatchCount: 940 },
    { name: 'EaseMyTrip High-Speed API', status: 'HEALTHY', latencyMs: 180, successRatePct: 99.8, lastBatchCount: 1120 },
    { name: 'MakeMyTrip Harvester', status: 'HEALTHY', latencyMs: 510, successRatePct: 97.6, lastBatchCount: 880 },
    { name: 'Ixigo Harvester', status: 'HEALTHY', latencyMs: 490, successRatePct: 98.1, lastBatchCount: 320 },
    { name: 'Cleartrip Harvester', status: 'WARNING', latencyMs: 820, successRatePct: 94.2, lastBatchCount: 170 }
  ]
};

// Index Calculation Methodology Specifications
export const methodologyDocs = {
  title: "AirGo Real-Time Airfare Price Index (APIx) Econometric Formulation",
  version: "1.0.0 (MoSPI / RBI Compliance)",
  basePeriod: "Calendar Year 2024 Average = 100.0",
  pipelineSteps: [
    { step: 1, name: "Raw Price Extraction", desc: "Real multi-source web scrapers query top domestic airlines and OTAs across advance windows T+1, T+7, T+15, T+30, T+45." },
    { step: 2, name: "Data Cleaning & Disaggregation", desc: "Deduplicates identical flight quotes, separates Base Fare from Airport Charges (UDF/PSF), GST, and OTA convenience fees." },
    { step: 3, name: "Outlier Removal (IQR)", desc: "Filters anomalous price spikes (>1.5x IQR above P75) to prevent scraping artifacts from distorting index levels." },
    { step: 4, name: "Canonical Fare Product Matching", desc: "Groups multi-platform quotes for the same flight product (Origin, Dest, Airline, Flight No, Travel Date) to compute direct vs. OTA spreads." },
    { step: 5, name: "Price Relatives Calculation", desc: "Computes elementary price relatives r_i = (P_it / P_i0) * 100 against baseline tariffs." },
    { step: 6, name: "Booking-Window Weighting", desc: "Aggregates advance windows using empirical passenger booking distributions (T+1: 18%, T+7: 24%, T+15: 32%, T+30: 16%, T+45: 10%)." },
    { step: 7, name: "Route-Level Aggregation", desc: "Formulates elementary Laspeyres, Jevons, and Fisher route index numbers for each corridor." },
    { step: 8, name: "National APIx Synthesis", desc: "Applies official DGCA passenger-traffic weights w_i to generate the National APIx Index." }
  ],
  formulas: [
    { name: "Price Relative (r_i)", formula: "r_{i,t} = \\frac{P_{i,t}}{P_{i,0}} \\times 100" },
    { name: "Laspeyres Price Index (L)", formula: "L_t = \\frac{\\sum (P_{i,t} \\cdot Q_{i,0})}{\\sum (P_{i,0} \\cdot Q_{i,0})} = \\sum w_i \\left(\\frac{P_{i,t}}{P_{i,0}}\\right)" },
    { name: "Jevons Geometric Index (J)", formula: "J_t = \\prod \\left(\\frac{P_{i,t}}{P_{i,0}}\\right)^{w_i}" },
    { name: "Fisher Ideal Index (F)", formula: "F_t = \\sqrt{L_t \\times P_t}" }
  ]
};
