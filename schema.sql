-- =====================================================================
-- AirGo Scraping & Airfare Index Layer — PostgreSQL DDL
-- Scope: Scraping runs, historical fare observations, checkout audits
-- Target Database: PostgreSQL 15+ / 17+ (Supabase compatible)
-- =====================================================================

-- ---------------------------------------------------------------------
-- 1. LEAN DIMENSION TABLES
-- ---------------------------------------------------------------------

CREATE TABLE IF NOT EXISTS dim_routes (
    route_id             SERIAL PRIMARY KEY,
    route_code           TEXT UNIQUE NOT NULL,     -- 'DEL-BOM'
    origin_iata          CHAR(3) NOT NULL,
    origin_city          TEXT NOT NULL,
    dest_iata            CHAR(3) NOT NULL,
    dest_city            TEXT NOT NULL,
    dgca_traffic_weight  NUMERIC(6,4) NOT NULL,    -- weight in the basket, from DGCA passenger data
    is_active            BOOLEAN DEFAULT TRUE,
    added_on             DATE DEFAULT CURRENT_DATE
);

CREATE TABLE IF NOT EXISTS dim_platforms (
    platform_id     SMALLSERIAL PRIMARY KEY,
    platform_name   TEXT UNIQUE NOT NULL,          -- 'IndiGo Direct','MakeMyTrip','HappyFares', etc.
    platform_type   TEXT NOT NULL CHECK (platform_type IN ('airline_direct','ota')),
    base_url        TEXT NOT NULL,
    scrape_method   TEXT NOT NULL CHECK (scrape_method IN ('static_html','api_intercept','selenium','playwright','scrapy')),
    rate_limit_rpm  INT DEFAULT 10,
    tos_reviewed_on DATE,
    is_active       BOOLEAN DEFAULT TRUE
);

CREATE TABLE IF NOT EXISTS dim_advance_purchase_windows (
    window_id       SMALLSERIAL PRIMARY KEY,
    window_code     TEXT UNIQUE NOT NULL,          -- 'T+1','T+7','T+15','T+30','T+45'
    days_ahead      SMALLINT NOT NULL,
    tolerance_days  SMALLINT DEFAULT 0
);

-- ---------------------------------------------------------------------
-- 2. SCRAPING INFRASTRUCTURE (Rotation Pools)
-- ---------------------------------------------------------------------

CREATE TABLE IF NOT EXISTS proxy_pool (
    proxy_id        SERIAL PRIMARY KEY,
    ip_address      INET NOT NULL,
    provider        TEXT,
    is_active       BOOLEAN DEFAULT TRUE,
    last_used_at    TIMESTAMPTZ,
    failure_count   INT DEFAULT 0,
    blocked_until   TIMESTAMPTZ
);

CREATE TABLE IF NOT EXISTS user_agent_pool (
    ua_id           SERIAL PRIMARY KEY,
    user_agent      TEXT NOT NULL,
    device_type     TEXT CHECK (device_type IN ('desktop','mobile')),
    is_active       BOOLEAN DEFAULT TRUE
);

-- ---------------------------------------------------------------------
-- 3. JOB SCHEDULING
-- ---------------------------------------------------------------------

CREATE TABLE IF NOT EXISTS scrape_jobs (
    job_id          BIGSERIAL PRIMARY KEY,
    route_id        INT NOT NULL REFERENCES dim_routes(route_id),
    route_code      TEXT NOT NULL,                 -- denormalized copy of dim_routes.route_code
    platform_id     SMALLINT NOT NULL REFERENCES dim_platforms(platform_id),
    platform_name   TEXT NOT NULL,                 -- denormalized copy of dim_platforms.platform_name
    window_id       SMALLINT NOT NULL REFERENCES dim_advance_purchase_windows(window_id),
    window_code     TEXT NOT NULL,                 -- denormalized copy, e.g. 'T+7'
    cron_expression TEXT NOT NULL,
    is_enabled      BOOLEAN DEFAULT TRUE,
    created_at      TIMESTAMPTZ DEFAULT now(),
    UNIQUE (route_id, platform_id, window_id)
);

-- ---------------------------------------------------------------------
-- 4. SCRAPE RUNS — Execution Log (Partitioned Monthly)
--    Each execution record represents a specific (route, platform, window).
-- ---------------------------------------------------------------------

CREATE TABLE IF NOT EXISTS scrape_runs (
    run_id              BIGSERIAL,
    job_id              BIGINT REFERENCES scrape_jobs(job_id),  -- Nullable for ad-hoc / CLI runs
    route_code          TEXT NOT NULL,                          -- 'BOM-DEL'
    platform_name       TEXT NOT NULL,                          -- 'HappyFares', 'MakeMyTrip'
    window_code         TEXT NOT NULL,                          -- 'T+1', 'T+7', 'T+15'
    run_started_at      TIMESTAMPTZ NOT NULL,
    run_ended_at        TIMESTAMPTZ,
    status              TEXT NOT NULL CHECK (status IN ('success','partial','failed','captcha_blocked','rate_limited','timeout')),
    http_status_code    SMALLINT,
    proxy_id            INT REFERENCES proxy_pool(proxy_id),
    ua_id               INT REFERENCES user_agent_pool(ua_id),
    retry_count         SMALLINT DEFAULT 0,
    captcha_encountered BOOLEAN DEFAULT FALSE,
    records_scraped     SMALLINT DEFAULT 0,                     -- Legacy counter
    records_found       INT DEFAULT 0,                          -- Total flights discovered on search page
    top_n_extracted     INT DEFAULT 0,                          -- Number of quotes actually persisted
    channel             TEXT DEFAULT 'chrome',                  -- 'chrome', 'playwright', 'api'
    error_message       TEXT,
    scraper_version     TEXT,
    raw_log_path        TEXT,                                   -- Path to audit run folder / log
    PRIMARY KEY (run_id, run_started_at)
) PARTITION BY RANGE (run_started_at);

CREATE TABLE IF NOT EXISTS scrape_runs_2026_09 PARTITION OF scrape_runs
    FOR VALUES FROM ('2026-09-01') TO ('2026-10-01');
CREATE TABLE IF NOT EXISTS scrape_runs_2026_10 PARTITION OF scrape_runs
    FOR VALUES FROM ('2026-10-01') TO ('2026-11-01');
CREATE TABLE IF NOT EXISTS scrape_runs_default PARTITION OF scrape_runs DEFAULT;

-- ---------------------------------------------------------------------
-- 5. FARE QUOTES — Main Historical Fact Table (Partitioned Monthly)
--    Stores raw observed airfares exactly as extracted from search cards.
-- ---------------------------------------------------------------------

CREATE TABLE IF NOT EXISTS fare_quotes (
    quote_id                BIGSERIAL,
    run_id                  BIGINT NOT NULL,          -- Logical reference to scrape_runs.run_id
    run_started_at          TIMESTAMPTZ NOT NULL,     -- Matches scrape_runs.run_started_at

    -- Flight identity
    airline_code            CHAR(2),                  -- 'SG', '6E', 'AI' (Nullable: scraper may only yield name)
    airline_name            TEXT NOT NULL,            -- 'SpiceJet', 'IndiGo', 'Air India Express'
    flight_number           TEXT NOT NULL,            -- 'SG-803', '6E-656'
    route_code              TEXT NOT NULL,            -- 'BOM-DEL'
    origin_iata             CHAR(3) NOT NULL,         -- 'BOM'
    dest_iata               CHAR(3) NOT NULL,         -- 'DEL'
    scheduled_dep_time      TIME NOT NULL,            -- '01:50:00'
    scheduled_arr_time      TIME,                     -- '04:10:00'
    duration_minutes        SMALLINT,                 -- Converted duration (e.g. '02h:20m' -> 140)
    stops                   SMALLINT DEFAULT 0,       -- 0 (non-stop), 1, 2

    -- Source platform
    platform_id             SMALLINT NOT NULL REFERENCES dim_platforms(platform_id),
    platform_name           TEXT NOT NULL,            -- 'HappyFares', 'MakeMyTrip'
    platform_type           TEXT NOT NULL CHECK (platform_type IN ('airline_direct','ota')),

    -- Timing & horizon
    scrape_timestamp        TIMESTAMPTZ NOT NULL,
    travel_date             DATE NOT NULL,            -- '2026-09-09'
    advance_purchase_days   SMALLINT NOT NULL,        -- 1
    window_code             TEXT NOT NULL,            -- 'T+1'

    -- Raw observed fare components (NO mathematical reconciliation enforced)
    fare_class              TEXT,                     -- 'Economy', 'ECONOMY_SAVER'
    base_fare               NUMERIC(10,2),            -- Observed base fare (Nullable if not itemized on search card)
    taxes                   NUMERIC(10,2) DEFAULT 0,  -- Observed taxes/fees
    user_dev_fee            NUMERIC(10,2) DEFAULT 0,
    convenience_fee         NUMERIC(10,2) DEFAULT 0,  -- OTA convenience fee
    other_surcharges        NUMERIC(10,2) DEFAULT 0,
    total_fare              NUMERIC(10,2) NOT NULL,   -- Maps to scraper's final_price
    search_price            NUMERIC(10,2),            -- Raw displayed search card price
    regular_price           NUMERIC(10,2),            -- Pre-discount sticker price
    promo_discount          NUMERIC(10,2) DEFAULT 0,  -- Instant promo or coupon discount
    displayed_search_price  NUMERIC(10,2),            -- Legacy alias for search_price
    final_payable_price     NUMERIC(10,2),            -- Price verified at checkout
    verification_status     TEXT DEFAULT 'SEARCH_RESULT',
    verification_timestamp  TIMESTAMPTZ,
    currency                CHAR(3) DEFAULT 'INR',

    -- Capacity & ancillary indicators
    baggage                 TEXT,                     -- '7 kg (1 PC)'
    total_seats             SMALLINT,
    seats_available         SMALLINT,                 -- Parsed numeric seat count (e.g. 9)
    available_seats_raw     TEXT,                     -- Original verbatim string (e.g. '9 Seat(s)')
    load_factor_pct         NUMERIC(5,2) GENERATED ALWAYS AS (
                                CASE WHEN total_seats > 0
                                     THEN ROUND(((total_seats - COALESCE(seats_available,0))::NUMERIC / total_seats) * 100, 2)
                                     ELSE NULL END
                            ) STORED,

    availability_status     TEXT NOT NULL DEFAULT 'available'
                            CHECK (availability_status IN ('available','sold_out','cancelled','not_found')),

    is_outlier              BOOLEAN DEFAULT FALSE,
    dedup_hash              TEXT NOT NULL,            -- hash(platform_id, flight_number, travel_date, fare_class, scheduled_dep_time)
    screenshot_path         TEXT,                     -- Relative path to search result screenshot proof
    raw_payload             JSONB,                    -- Verbatim unmodified scraper record

    PRIMARY KEY (quote_id, scrape_timestamp)
) PARTITION BY RANGE (scrape_timestamp);

CREATE TABLE IF NOT EXISTS fare_quotes_2026_09 PARTITION OF fare_quotes
    FOR VALUES FROM ('2026-09-01') TO ('2026-10-01');
CREATE TABLE IF NOT EXISTS fare_quotes_2026_10 PARTITION OF fare_quotes
    FOR VALUES FROM ('2026-10-01') TO ('2026-11-01');
CREATE TABLE IF NOT EXISTS fare_quotes_default PARTITION OF fare_quotes DEFAULT;

-- Prevent double-counting from retried scrapes within the same observation window
CREATE UNIQUE INDEX IF NOT EXISTS uq_fare_quotes_dedup
    ON fare_quotes (dedup_hash, scrape_timestamp);

-- Query performance indexes
CREATE INDEX IF NOT EXISTS idx_fare_quotes_route_travel_date
    ON fare_quotes (route_code, travel_date);
CREATE INDEX IF NOT EXISTS idx_fare_quotes_route_platform_date
    ON fare_quotes (route_code, platform_id, travel_date);
CREATE INDEX IF NOT EXISTS idx_fare_quotes_flight_travel_date
    ON fare_quotes (airline_name, flight_number, travel_date);
CREATE INDEX IF NOT EXISTS idx_fare_quotes_window
    ON fare_quotes (window_code, travel_date);
CREATE INDEX IF NOT EXISTS idx_fare_quotes_scrape_ts_brin
    ON fare_quotes USING BRIN (scrape_timestamp);
CREATE INDEX IF NOT EXISTS idx_fare_quotes_raw_payload_gin
    ON fare_quotes USING GIN (raw_payload);

-- ---------------------------------------------------------------------
-- 6. CHECKOUT AUDITS — Representative Booking Flow Verification
--    Verifies price transparency, hidden fees, and booking validity.
--    NOTE: Logical reference to fare_quotes and scrape_runs (no FK due
--    to composite PK partitioning on parent tables).
-- ---------------------------------------------------------------------

CREATE TABLE IF NOT EXISTS checkout_audits (
    audit_id            BIGSERIAL PRIMARY KEY,
    run_id              BIGINT NOT NULL,          -- Logical reference to scrape_runs.run_id
    quote_id            BIGINT,                   -- Logical reference to fare_quotes.quote_id
    audit_timestamp     TIMESTAMPTZ NOT NULL DEFAULT now(),

    checkout_successful BOOLEAN NOT NULL,
    base_fare           NUMERIC(10,2),
    taxes               NUMERIC(10,2),
    discount            NUMERIC(10,2),            -- e.g. -275.00
    convenience_fee     NUMERIC(10,2),
    other_surcharges    NUMERIC(10,2) DEFAULT 0,
    total_fare          NUMERIC(10,2),            -- Final payable amount audited at checkout

    status              TEXT NOT NULL CHECK (status IN ('success', 'partial', 'failed')),
    notes               TEXT,
    screenshot_path     TEXT                      -- Path to checkout review proof screenshot
);

CREATE INDEX IF NOT EXISTS idx_checkout_audits_run_id
    ON checkout_audits (run_id);
CREATE INDEX IF NOT EXISTS idx_checkout_audits_quote_id
    ON checkout_audits (quote_id);
