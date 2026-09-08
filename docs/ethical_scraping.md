# AirGo: Ethical Web Scraping, Rate Limiting & Compliance Policy

This document codifies the operational ethics, rate-limiting frameworks, and legal compliance safeguards implemented within the **AirGo** high-frequency airfare collection platform.

---

## 1. Regulatory Context & Scope

The **AirGo** platform is engineered to support the **National Statistical Office (NSO)**, **Ministry of Statistics and Programme Implementation (MoSPI)**, and the **Reserve Bank of India (RBI)** in measuring real-time domestic airfare inflation.

To maintain ethical operational standards and ensure zero disruption to target airline and aggregator web services, AirGo enforces strict technical constraints across all data acquisition modules.

---

## 2. Fundamental Ethical Scraping Tenets

### 2.1 Non-Intrusive, Read-Only Public Observation
* **No Inventory Locking:** The harvesting engine performs read-only searches for published public flight availability. It strictly terminates before the payment processing gateway and never reserves, locks, or holds airline seat inventory.
* **Non-Personal Data (Zero PII):** AirGo extracts exclusively impersonal commercial price schedules (origin, destination, date, flight number, base fare, taxes, and total fare). No passenger personal data, cookies, or user profile records are ever collected or stored.
* **Public Domain Prices:** Tariffs harvested are publicly displayed prices advertised to Indian consumers under the *Aircraft Rules, 1937*.

### 2.2 Strict Zero-Dummy Data Protocol
* AirGo never injects synthetic, mock, or randomized placeholder prices.
* If a target endpoint is unreachable, rate-limited, or presents anti-bot friction, the crawler **fails fast and honestly**, logging an explicit diagnostic entry rather than generating fake or guessed fare data.

---

## 3. Rate-Limiting and Traffic Cadence Safeguards

To prevent operational load on airline origin servers and Online Travel Aggregators (OTAs):

| Parameter | Operational Setting | Rationale |
| :--- | :--- | :--- |
| **Request Cadence Delay** | $\ge 1.0\text{s} - 2.5\text{s}$ per query | Enforces human-like pacing between flight route searches |
| **Worker Concurrency Limit** | Max 1 to 3 concurrent browser instances | Minimizes socket exhaustion and CPU utilization on target hosts |
| **Off-Peak Execution Window** | Scheduled at **03:00 AM IST** daily | Runs during lowest domestic passenger booking activity |
| **Batch Pagination Ceiling** | 1 full-day sweep per route-horizon | Avoids polling duplicate pages within short timeframes |

---

## 4. Anti-Bot and HTTP Status Protocol

AirGo implements robust HTTP response handling to respect server capacity signals:

1. **HTTP 200 (OK):** Extract published availability, validate non-empty payload, record latency.
2. **HTTP 429 (Too Many Requests):** Immediately halt active worker thread. Apply randomized exponential backoff ($2^k \times \text{jitter}$, up to 60 seconds). If persistent, abort route run and log warning.
3. **HTTP 403 / 503 (Forbidden / Service Unavailable):** Log diagnostic incident with timestamp and target URL; terminate execution to prevent repeated server probing.
4. **Bandwidth Optimization:** Block non-essential heavy multimedia assets (video ads, large marketing banners, analytics beacons) during automated browser runs to minimize bandwidth consumption for both AirGo and the target host.

---

## 5. Auditability and Reproducibility

Per **Rule 4** of the AirGo Project Guidelines:
* Every scraping execution generates an immutable, isolated audit directory:
  `runs/YYYY-MM-DD_HH-MM-SS_<prefix>/`
* Preserves rendered HTML snapshots (`search_results.html`), high-resolution visual screenshots of displayed prices, and `run_summary.json` execution manifests.
* Enables external auditors (MoSPI/RBI) to cross-reference every data point in PostgreSQL against raw live website captures.

## 6. Ixigo Prototype Boundaries

The Ixigo-only prototype checks `https://www.ixigo.com/robots.txt` before each
new search path. A search is refused and recorded as `blocked` when the path is
not allowed or the robots file cannot be read. Searches run sequentially with a
configurable delay and jitter, using one standard Playwright browser context per
route/window search; no proxy rotation, fingerprint spoofing, or CAPTCHA solving
is attempted.

For selected fare options, the prototype may traverse Ixigo's public booking
funnel to the review/Pay Now landing page to observe a tax-inclusive price. It
never enters card, CVV, or other payment fields and never submits payment. A
CAPTCHA, block, sold-out result, or price change is recorded in the timestamped
run artifacts as `blocked` or `unavailable`; it is not replaced with synthetic
data. Ixigo results are currently written to `runs/*_ixigo_scrape/` as CSV,
JSON, HTML, screenshots, and a run summary rather than inserted into the
database.
