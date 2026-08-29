# Strict Data Integrity & Scraping Rules

## Rule 1: Absolute Zero-Dummy Data
1. No synthetic seat numbers, prices, or mock breakdowns are permitted in any script, API, or database write.
2. If an extraction fails, output an explicit error rather than substituting hardcoded fallbacks.

## Rule 2: Inspect Actual HTML Before Writing Selectors
1. Always inspect the live DOM or rendered `.html` dumps prior to defining CSS/XPath selectors.
2. Base all selectors on observed DOM classes, IDs, or Angular/React properties.
3. If elements are dynamic, use DOM discovery traversal to log live attributes before querying.

## Rule 3: Visual Screenshot Proof
1. Maintain screenshot artifacts (`checkout_screenshot.png`, `aircraft_cabin_seat_map.png`, `live_payment_proof.png`) for full auditability.

## Rule 4: Timestamped Run Folders (Local Audit Storage)
1. Write all outputs, logs, HTML dumps, and screenshots into isolated timestamped directories: `runs/YYYY-MM-DD_HH-MM-SS_<prefix>/`.
2. Keep runs cleanly isolated locally without overwriting previous audit history.
