CREATE EXTENSION IF NOT EXISTS pg_trgm;
CREATE TABLE IF NOT EXISTS providers (
  provider_id TEXT PRIMARY KEY,
  provider_name TEXT NOT NULL,
  provider_city TEXT,
  provider_state TEXT,
  provider_zip_code TEXT
);
CREATE TABLE IF NOT EXISTS drg_prices (
  id BIGSERIAL PRIMARY KEY,
  provider_id TEXT NOT NULL REFERENCES providers(provider_id) ON DELETE CASCADE,
  ms_drg_definition TEXT NOT NULL,
  ms_drg_code INTEGER,
  total_discharges INTEGER,
  average_covered_charges NUMERIC,
  average_total_payments NUMERIC,
  average_medicare_payments NUMERIC
);
CREATE TABLE IF NOT EXISTS ratings (
  id BIGSERIAL PRIMARY KEY,
  provider_id TEXT NOT NULL REFERENCES providers(provider_id) ON DELETE CASCADE,
  rating SMALLINT NOT NULL CHECK (rating BETWEEN 1 AND 10),
  created_at TIMESTAMP WITHOUT TIME ZONE DEFAULT NOW()
);
