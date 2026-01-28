-- Database initialization script for BEES Brewery Pipeline
-- Creates schemas and tables for Bronze, Silver, and Gold layers

-- ============================================
-- BRONZE SCHEMA - Raw data from API
-- ============================================
CREATE SCHEMA IF NOT EXISTS breweries_bronze;

DROP TABLE IF EXISTS breweries_bronze.tb_breweries CASCADE;

-- Bronze table accepts ANY data from API without constraints
-- All validations, type conversions, and size limits are applied in Silver layer
CREATE TABLE breweries_bronze.tb_breweries (
    id TEXT,  -- Store as TEXT, convert to UUID in Silver
    name TEXT,
    brewery_type TEXT,
    address_1 TEXT,
    address_2 TEXT,
    address_3 TEXT,
    city TEXT,
    state_province TEXT,
    postal_code TEXT,
    country TEXT,
    longitude TEXT,  -- Store as TEXT, convert to DECIMAL in Silver
    latitude TEXT,   -- Store as TEXT, convert to DECIMAL in Silver
    phone TEXT,
    website_url TEXT,
    state TEXT,
    street TEXT,
    ingestion_timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    ingestion_date DATE DEFAULT CURRENT_DATE
);

-- Indexes for Bronze layer (no PRIMARY KEY - we accept duplicates)
CREATE INDEX idx_bronze_breweries_id ON breweries_bronze.tb_breweries(id);
CREATE INDEX idx_bronze_breweries_ingestion_date ON breweries_bronze.tb_breweries(ingestion_date);
CREATE INDEX idx_bronze_breweries_country_state ON breweries_bronze.tb_breweries(country, state);
CREATE INDEX idx_bronze_breweries_type ON breweries_bronze.tb_breweries(brewery_type);

-- ============================================
-- SILVER SCHEMA - Cleaned and transformed data
-- ============================================
CREATE SCHEMA IF NOT EXISTS breweries_silver;

DROP TABLE IF EXISTS breweries_silver.tb_breweries CASCADE;

CREATE TABLE breweries_silver.tb_breweries (
    id UUID PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    brewery_type VARCHAR(50) NOT NULL,

    -- Cleaned address fields
    address_full TEXT,
    city VARCHAR(100) NOT NULL,
    state VARCHAR(100) NOT NULL,
    postal_code VARCHAR(20),
    country VARCHAR(100) NOT NULL,

    -- Geolocation
    longitude DECIMAL(11, 8),  -- Range: -180 to +180
    latitude DECIMAL(10, 8),   -- Range: -90 to +90
    has_coordinates BOOLEAN,

    -- Contact
    phone VARCHAR(50),
    website_url TEXT,
    has_website BOOLEAN,

    -- Metadata
    processed_timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    source_date DATE NOT NULL,
    data_quality_score DECIMAL(3, 2),

    -- Partitioning keys (for Parquet files)
    partition_country VARCHAR(100),
    partition_state VARCHAR(100),
    partition_city VARCHAR(100)
);

-- Indexes for Silver layer
CREATE INDEX idx_silver_breweries_type ON breweries_silver.tb_breweries(brewery_type);
CREATE INDEX idx_silver_breweries_location ON breweries_silver.tb_breweries(partition_country, partition_state, partition_city);
CREATE INDEX idx_silver_breweries_source_date ON breweries_silver.tb_breweries(source_date);
CREATE INDEX idx_silver_breweries_coordinates ON breweries_silver.tb_breweries(longitude, latitude) WHERE has_coordinates = true;
CREATE INDEX idx_silver_breweries_quality ON breweries_silver.tb_breweries(data_quality_score);

-- ============================================
-- GOLD LAYER - Managed by dbt
-- ============================================
-- Gold layer (aggregated analytical data) is created and managed by dbt
-- Schema: breweries_gold (created automatically by dbt)
-- Table: breweries_gold.fat_breweries_by_type_location
-- Views and aggregations are defined in dbt models

-- ============================================
-- GRANT PERMISSIONS
-- ============================================

-- Grant usage on schemas
GRANT USAGE ON SCHEMA breweries_bronze TO PUBLIC;
GRANT USAGE ON SCHEMA breweries_silver TO PUBLIC;

-- Grant select on all tables
GRANT SELECT ON ALL TABLES IN SCHEMA breweries_bronze TO PUBLIC;
GRANT SELECT ON ALL TABLES IN SCHEMA breweries_silver TO PUBLIC;

-- Grant insert/update/delete to airflow user for ETL operations
GRANT INSERT, UPDATE, DELETE ON ALL TABLES IN SCHEMA breweries_bronze TO airflow;
GRANT INSERT, UPDATE, DELETE ON ALL TABLES IN SCHEMA breweries_silver TO airflow;

-- Note: Gold layer permissions are managed by dbt in breweries_gold schema

-- ============================================
-- Database initialization complete
-- ============================================
-- Created schemas: breweries_bronze, breweries_silver
-- Created tables: breweries_bronze.tb_breweries, breweries_silver.tb_breweries
-- Gold layer (breweries_gold schema) is managed by dbt
