# AirGo: API Usage & MakeMyTrip Scraper Engineering Guide

This document provides a comprehensive operational guide for:
1. **Using the AirGo Backend API** (FastAPI single-threaded scraper dispatch).
2. **MakeMyTrip Anti-Bot & Scraper Engineering** (problems encountered and technical solutions).

---

## 1. How to Use the Backend API

The AirGo API exposes a lightweight, strictly single-threaded dispatch interface to execute web scrapers on demand and return live extracted airfare quotes directly in memory.

### 1.1 Starting the API Server

From the repository root, start the FastAPI server with `uvicorn`:

```bash
uvicorn airgo.api.app:app --host 127.0.0.1 --port 8000 --reload
```

- **Interactive Swagger Docs**: [http://127.0.0.1:8000/docs](http://127.0.0.1:8000/docs)
- **ReDoc Documentation**: [http://127.0.0.1:8000/redoc](http://127.0.0.1:8000/redoc)
- **Health Check**: [http://127.0.0.1:8000/health](http://127.0.0.1:8000/health)

---

### 1.2 Endpoints Reference

#### `GET /api/scrapers`
Returns the list of scrapers registered and available in AirGo.

- **Response (`200 OK`)**:
  ```json
  {
    "supported_platforms": ["makemytrip", "easemytrip", "cleartrip"],
    "count": 3
  }
  ```

---

#### `POST /api/scrape`
Executes the specified scraper on the server's single-threaded event loop and returns the live extracted flight cards.

- **Request Body (`application/json`)**:
  | Field | Type | Required | Default | Description |
  | :--- | :---: | :---: | :---: | :--- |
  | `platform` | `string` | **Yes** | — | Target OTA (`"makemytrip"`, `"easemytrip"`, `"cleartrip"`) |
  | `route` | `string` | No | `"BOM-DEL"` | Sector in `'ORIGIN-DEST'` format (e.g. `"DEL-BLR"`, `"BOM-DEL"`) |
  | `horizons` | `int[]` | No | `[7]` | Advance purchase horizons in days (e.g. `[1]`, `[7]`, `[15]`) |
  | `headless` | `bool` | No | `false` | Run browser in headless mode or visible window |
  | `deep_checkout` | `bool` | No | `false` | Audit checkout fees, seat maps, and convenience fee |

- **Sample cURL Request**:
  ```bash
  curl -X POST "http://127.0.0.1:8000/api/scrape" \
       -H "Content-Type: application/json" \
       -d '{
         "platform": "makemytrip",
         "route": "BOM-DEL",
         "horizons": [7],
         "headless": false,
         "deep_checkout": false
       }'
  ```

- **Sample Python Client Request**:
  ```python
  import requests

  payload = {
      "platform": "makemytrip",
      "route": "BOM-DEL",
      "horizons": [7],
      "headless": False
  }

  response = requests.post("http://127.0.0.1:8000/api/scrape", json=payload)
  data = response.json()

  print(f"Status: {data['status']}")
  print(f"Captured {data['quotes_count']} live flight quotes:")
  for quote in data["quotes"][:5]:
      print(f"  {quote['airline']} {quote['flight_number']}: ₹{quote['price_inr']} ({quote['departure_time']} -> {quote['arrival_time']})")
  ```

- **Sample JSON Response (`200 OK`)**:
  ```json
  {
    "status": "success",
    "platform": "makemytrip",
    "route": "BOM-DEL",
    "horizons": [7],
    "quotes_count": 63,
    "quotes": [
      {
        "airline": "SpiceJet",
        "flight_number": "SG-164",
        "origin": "BOM",
        "destination": "DEL",
        "departure_date": "15/09/2026",
        "departure_time": "23:25",
        "arrival_time": "01:50",
        "duration": "02h 25m",
        "stops": 0,
        "price_inr": 6393,
        "advance_horizon": "T+7",
        "captured_at": "2026-09-08T00:31:12.481955",
        "platform": "makemytrip"
      },
      {
        "airline": "Air India Express",
        "flight_number": "IX-2153",
        "origin": "BOM",
        "destination": "DEL",
        "departure_date": "15/09/2026",
        "departure_time": "20:25",
        "arrival_time": "22:35",
        "duration": "02h 10m",
        "stops": 0,
        "price_inr": 6561,
        "advance_horizon": "T+7",
        "captured_at": "2026-09-08T00:31:12.481970",
        "platform": "makemytrip"
      }
    ]
  }
  ```

---

### 1.3 Preserved Standalone CLI Testing

The backend API does not modify or interfere with the standalone CLI runners. You can run manual visual audits and interactive tests directly from your terminal at any time:

```bash
# Run MakeMyTrip with live visible Google Chrome
python scripts/scrape_makemytrip.py --top-n 1 --horizons 7 --visible

# Run EaseMyTrip with live visible Google Chrome
python scripts/scrape_easemytrip.py --top-n 1 --horizons 7 --visible
```

---

## 2. MakeMyTrip Scraper Engineering: Challenges & Solutions

MakeMyTrip is protected by **Akamai Bot Manager Premier**, employs aggressive React DOM virtualization, and renders dynamic client-side overlays. Below are the specific issues encountered and the engineering techniques used to overcome them.

---

### 2.1 Challenge 1: Akamai Bot Manager Premier Telemetry Detection
- **Symptom**: Instant `ERR_HTTP2_PROTOCOL_ERROR`, blank white pages, or dropping of the search session.
- **Root Cause**: Akamai inspects browser TLS fingerprints, runtime navigator properties, and mouse kinematics (curvature, jerk, acceleration, dwell times). In headless mode or with vanilla Playwright, Akamai detects synthetic event dispatching and refuses to issue the valid `_abck` session cookie (indicated by `~0~` in the cookie value).
- **Solution**:
  1. **Patchright Undetected Engine**: Used `patchright` with the native Google Chrome binary (`channel="chrome"`) and persistent browser profiles (`user_data_dir="runs/mmt_browser_profile"`).
  2. **Human Mouse Kinematics (`human_mouse.py`)**:
     - Modeled mouse trajectories using Cubic Bezier curves with randomized control points.
     - Implemented Fitts's law overshoot and organic jitter micro-movements.
     - Added natural mouse down/up hold times (65ms–130ms) rather than instantaneous synthetic clicks.
  3. **Sensor Telemetry Pre-Warming**:
     - Hovered cursor organically over the `From` and `To` city labels for 600ms before triggering actions.
     - Monitored `context.cookies()` until the `_abck` cookie contained `~0~`, confirming Akamai trust validation.

---

### 2.2 Challenge 2: React DOM Virtualization & Incomplete Card Capture
- **Symptom**: When scrolling directly to the bottom of the flight search page, only ~15 flight cards were present in the DOM instead of the 60–80+ available flights.
- **Root Cause**: MakeMyTrip uses virtualized React lists (`react-window` / dynamic recycler). Cards that scroll out of the viewport are actively unmounted from the DOM to save memory. A single DOM evaluation at the end of the page misses all flights that were previously rendered and unmounted.
- **Solution**:
  1. **Continuous Progressive Extraction**:
     - Avoided scrolling straight to the bottom.
     - Divided the scroll flow into a 60-step loop with 500px increments.
     - On *every single scroll step*, evaluated JavaScript in the browser to extract the currently rendered batch of cards.
     - Accumulated new flights into an in-memory dictionary keyed by `f"{flight_number}_{departure_time}_{price}"`.
  2. **Cursor Placement Over Main Content Container**:
     - Positioned the mouse at `(650, 400)` before wheel scrolling. This prevents wheel events from scrolling the left filter sidebar instead of the flight listing container.
  3. **Verified Result**: Captured **exactly 63 out of 63 non-stop flights**, achieving a 100% match with the website's reported total.

---

### 2.3 Challenge 3: Cluster Card Squashing & Non-Leaf Selectors
- **Symptom**: Only 1 or 2 flight cards were extracted per step, and multiple different flights (e.g. SpiceJet, Air India Express, IndiGo) were being grouped into a single quote.
- **Root Cause**: MakeMyTrip renders cluster containers (`.listingCardWrap`, `div.clusterCard`) that group several flight options (e.g., "Cheapest", "Non-stop First", "You May Prefer") inside a single wrapper. Querying `.listingCardWrap` treats the entire cluster as one card.
- **Solution**:
  - Implemented **leaf-level DOM filtering**:
    ```javascript
    const cards = Array.from(document.querySelectorAll('.flightCard, [class*="flightCard--full"], [class*="flightCard--clickable"], .listingCardItem'));
    // Filter out parent containers that contain other flight cards
    const leaves = cards.filter(el => el.querySelectorAll('.flightCard, .listingCardItem').length === 0);
    ```
  - Extracted flight number, carrier logo, timings, and price exclusively from these atomic leaf elements.

---

### 2.4 Challenge 4: Transient Overlays & Modals
- **Symptom**: Clicks on inputs or buttons failed because an unclickable overlay or login popup covered the DOM.
- **Root Cause**: MakeMyTrip displays an initial login popup modal, marketing banners, and occasional "Fare Rule" or "Price Drop Protection" tooltips.
- **Solution**:
  1. **Outside-Coordinate Click Dismissal**: Dispatched a human mouse click to coordinate `(100, 100)` outside the modal container, followed by pressing `Escape`.
  2. **Targeted Close Handlers**: Automatically dismissed overlays matching `span.overlay-cross, button.overlay-close, div.fareRuleOverlay-close` before scrolling.
  3. **Transient Network Problem Recovery**: Detected the "Network Problem - REFRESH" button if rendered and clicked it via human mouse to restore the live search state.

---

### 2.5 Challenge 5: Non-Stop Space Regex Normalization
- **Symptom**: Non-stop flights were being tagged with `stops: 1` instead of `stops: 0`.
- **Root Cause**: In MakeMyTrip's DOM, the text is rendered as `"Non stop"` (with a space) or `"02h 25m Non stop"`. Standard regex `/non-?stop/i` only matched `"nonstop"` or `"non-stop"` with a hyphen, failing on the space.
- **Solution**:
  - Updated stops parsing to `/non[\s-]?stop/i`:
    ```javascript
    let stops = /non[\s-]?stop/i.test(text) ? 0 : 1;
    ```
  - Verified that all non-stop flights correctly record `stops: 0`.

---

## 3. Compliance & Architectural Principles

1. **Rule 1: Strict Zero Dummy Data**:
   - Every price tag, departure time, and carrier code is extracted verbatim from live rendered elements. If data cannot be fetched, the scraper fails explicitly without injecting mock values.
2. **Rule 3: Visual Ground-Truth Verification**:
   - Every execution captures a full timestamped screenshot (`00_search_results.png`) stored locally under `runs/YYYY-MM-DD_HH-MM-SS_makemytrip/`.
3. **Rule 6: Mandatory Google Chrome Engine**:
   - Automation exclusively launches Google Chrome (`channel="chrome"`). Microsoft Edge (`msedge`) is strictly forbidden.
4. **Rule 7: Architectural Clarity**:
   - Scrapers reside exclusively in `airgo/scrapers/<ota>/`, with clean registration in `airgo/scrapers/registry.py` and runners in `scripts/`.
