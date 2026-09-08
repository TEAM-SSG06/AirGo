# AirGo - AI Agent Instructions

All agents operating in this workspace must adhere to:

1. **Zero Dummy Data**: Never invent or use placeholder variables, fake seat numbers, or mock prices. If data cannot be fetched, fail explicitly.
2. **Inspect Real DOM First**: Always inspect actual rendered HTML and DOM structures before writing selectors or parsing logic.
3. **Ground Truth Proof**: Generate visual screenshots and JSON artifacts to verify all extraction steps against live websites.
4. **Timestamped Run Folders**: Save every execution's artifacts into `runs/YYYY-MM-DD_HH-MM-SS_<prefix>/` locally for full audit traceability.
5. **Always Use Chrome, Never MSEdge**: Always launch Google Chrome (`channel="chrome"` or standard Chromium executable). Never launch or use Microsoft Edge (`msedge`).
6. **Architectural Clarity Before Code**: If the architecture is not clear or if scraper files are scattered without a clear design, STOP and ask the user what to do and how to fix it before writing or moving code.

