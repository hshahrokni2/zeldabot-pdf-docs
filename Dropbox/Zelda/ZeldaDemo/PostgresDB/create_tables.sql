CREATE TABLE IF NOT EXISTS brfs (
    id SERIAL PRIMARY KEY,
    brf_id TEXT UNIQUE NOT NULL,
    brf_name TEXT,
    city TEXT,
    is_akta_subtitle BOOLEAN,
    subtitle_text TEXT,
    total_bostader_subtitle INT,
    byggar TEXT,
    antal_bostadsratter INT,
    antal_hyresratter INT,
    boarea_bostadsratter_value DECIMAL,
    markagande TEXT,
    akta_forening BOOLEAN,
    timestamp NUMERIC
);

CREATE TABLE IF NOT EXISTS economy_data (
    id SERIAL PRIMARY KEY,
    brf_id TEXT NOT NULL,
    lan_text TEXT,
    lan_value DECIMAL,
    avgift_text TEXT,
    avgift_per_m2_year DECIMAL,
    sparande_text TEXT,
    sparande_per_m2_year DECIMAL,
    CONSTRAINT fk_brf_economy
      FOREIGN KEY(brf_id)
      REFERENCES brfs(brf_id)
);

CREATE TABLE IF NOT EXISTS documents (
    id SERIAL PRIMARY KEY,
    brf_id TEXT NOT NULL,
    doc_text TEXT,
    href TEXT,
    doc_type TEXT,
    saved_path TEXT,
    CONSTRAINT fk_brf_docs
      FOREIGN KEY(brf_id)
      REFERENCES brfs(brf_id)
);

CREATE TABLE IF NOT EXISTS residences (
    id SERIAL PRIMARY KEY,
    brf_id TEXT NOT NULL,
    raw_address TEXT,
    address_no_lgh TEXT,
    city_appended TEXT,
    size TEXT,
    estimated_value TEXT,
    latitude DECIMAL,
    longitude DECIMAL,
    formatted_address TEXT,
    CONSTRAINT fk_brf_residences
      FOREIGN KEY(brf_id)
      REFERENCES brfs(brf_id)
);
