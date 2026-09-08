# AirGo Project Guidelines & Rules for AI Agents

These rules are **MANDATORY** for all AI coding agents working on the AirGo codebase.

---

## 1. 🚫 STRICT ZERO-DUMMY DATA POLICY
- **NO FAKE OR SYNTHETIC DATA**: Never inject placeholder variables, hardcoded seat numbers (e.g., `'18-F'`), mock fares (e.g., `300.50`), synthetic breakdowns, or simulated quotes.
- **FAIL FAST & HONESTLY**: If live data cannot be extracted from the target website (due to network timeout, anti-bot blocking, or changed DOM layout), the script **MUST** raise an explicit error or return `None` / `[]` with diagnostic logs.
- **NEVER MASK FAILURES**: Do not use hardcoded fallback strings to make a failed scraper look like it succeeded. If it doesn't work, report that it doesn't work.

---

## 2. 🔍 INSPECT ACTUAL RENDERED HTML BEFORE WRITING SELECTORS
- **NO GUESSING TAGS OR CLASSES**: Never assume class names, IDs, or element hierarchies based on generic intuition.
- **DOM-FIRST DEVELOPMENT**:
  1. Capture the actual rendered DOM (via Playwright `page.content()`, rendered HTML dumps, or interactive inspection).
  2. Inspect the real element attributes, inline Angular/React attributes (e.g., `ng-click`, `data-seat`, `price=`), and computed styles.
  3. Write exact, robust selectors matching the observed HTML.
- **EXCEPTION CLAUSE**: If dynamic elements cannot be captured in advance, use exhaustive DOM discovery logging (`querySelectorAll('*')`) to inspect the live state dynamically rather than guessing.

---

## 3. 📸 VISUAL GROUND-TRUTH VERIFICATION
- **SCREENSHOT AUDITING**: All multi-step flows (Search Results, Checkout Review, Seat Matrix, Payment Gateway) must capture timestamped, high-resolution screenshots as ground-truth proof.
- **SAFE CAPTURE**: Use resilient screenshot handlers (`full_page=False` or try/except fallback) to prevent Chromium texture buffer limits on large rendered pages.
- **INTERACTIVE VERIFICATION**: Provide `--visible` and `--pause` flags in CLI tools so human auditors can watch live automation and verify against their screen.

---

## 4. 📁 TIMESTAMPED RUN FOLDERS (LOCAL AUDIT STORAGE)
- **ISOLATED RUN DIRECTORIES**: Every execution must write its artifacts into a dedicated timestamped folder: `runs/YYYY-MM-DD_HH-MM-SS_<prefix>/`.
- **EVIDENCE PRESERVATION**: Never overwrite historical audit runs. Store the rendered `search_results.html`, `checkout_review.html`, screenshot proof, and `run_summary.json` inside the run folder locally.

---

## 5. 📊 CLEAR SEPARATION OF OBSERVED VS COMPUTED METRICS
- **Raw Observed Data**: Price tags, seat IDs, taxes, convenience fees extracted directly from the DOM must be stored and displayed without modification.
- **Econometric / Statistical Models**: Any derived metrics (e.g., Econometric Expected Consumer Seat Surcharge, Flight Load Factor %, CPI Baskets) must be explicitly marked as computed models and separated from raw observed data points.

---

## 6. 🌐 BROWSER ENGINE: ALWAYS USE CHROME AND NEVER MSEDGE
- **MANDATORY CHROME**: Always launch Google Chrome (or Chromium via Patchright/Playwright with `channel="chrome"` or standard Chromium executable).
- **NEVER MSEDGE**: Under NO circumstances should Microsoft Edge (`msedge`) be launched or used as a browser channel.

---

## 7. 🛑 MANDATORY ARCHITECTURAL CLARITY BEFORE CODE
- **STOP AND ASK**: If the architecture is not clear, or if there are scraper files scattered without a clear architecture, unified design pattern, or designated directory structure, the agent **MUST STOP immediately** and ask the user what to do and how to structure/fix it.
- **NO SPRAWL OR AD-HOC SCATTERING**: Do not create, scatter, or dump uncoordinated scraper files or one-off scripts across random directories. Always align on the project structure, design patterns, and module architecture with the user before proceeding.

