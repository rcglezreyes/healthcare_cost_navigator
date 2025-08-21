CREATE INDEX IF NOT EXISTS idx_drg_prices_code ON drg_prices(ms_drg_code);
CREATE INDEX IF NOT EXISTS idx_drg_prices_def_trgm ON drg_prices USING gin (ms_drg_definition gin_trgm_ops);
CREATE INDEX IF NOT EXISTS idx_providers_zip ON providers(provider_zip_code);
CREATE INDEX IF NOT EXISTS idx_ratings_provider ON ratings(provider_id);
