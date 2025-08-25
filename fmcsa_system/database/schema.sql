-- FMCSA Database Schema with Partitioning Support
-- Handles 2.2M+ carrier records with optimized performance

-- Enable required extensions
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS pg_trgm;  -- For text search
CREATE EXTENSION IF NOT EXISTS btree_gin; -- For compound indexes

-- Drop existing tables if they exist (for clean setup)
DROP TABLE IF EXISTS carriers CASCADE;

-- Main carriers table (partitioned by created_at for time-series data)
CREATE TABLE carriers (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    usdot_number INTEGER UNIQUE NOT NULL,
    legal_name TEXT NOT NULL,
    dba_name TEXT,
    
    -- Address information
    physical_address TEXT,
    physical_city TEXT,
    physical_state VARCHAR(2),
    physical_zip VARCHAR(10),
    physical_country VARCHAR(2) DEFAULT 'US',
    
    mailing_address TEXT,
    mailing_city TEXT,
    mailing_state VARCHAR(2),
    mailing_zip VARCHAR(10),
    
    -- Contact information
    telephone VARCHAR(20),
    fax VARCHAR(20),
    email TEXT,
    
    -- Carrier details
    mcs_150_date DATE,
    mcs_150_mileage INTEGER,
    entity_type VARCHAR(50),
    operating_status VARCHAR(50),
    out_of_service_date DATE,
    
    -- Operations
    power_units INTEGER,
    drivers INTEGER,
    carrier_operation VARCHAR(100),
    cargo_carried TEXT[],
    
    -- Insurance information
    liability_insurance_date DATE,
    liability_insurance_amount DECIMAL(12,2),
    cargo_insurance_date DATE,
    cargo_insurance_amount DECIMAL(12,2),
    bond_insurance_date DATE,
    bond_insurance_amount DECIMAL(12,2),
    
    -- Hazmat information
    hazmat_flag BOOLEAN DEFAULT FALSE,
    hazmat_placardable BOOLEAN DEFAULT FALSE,
    
    -- Safety ratings
    safety_rating VARCHAR(50),
    safety_rating_date DATE,
    safety_review_date DATE,
    
    -- Metadata
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    raw_data JSONB  -- Store complete FMCSA record for reference
) PARTITION BY RANGE (created_at);

-- Create indexes on partition parent (will be inherited by partitions)
CREATE INDEX idx_carriers_usdot ON carriers(usdot_number);
CREATE INDEX idx_carriers_state ON carriers(physical_state);
CREATE INDEX idx_carriers_entity_type ON carriers(entity_type);
CREATE INDEX idx_carriers_operating_status ON carriers(operating_status);
CREATE INDEX idx_carriers_insurance_exp ON carriers(liability_insurance_date);
CREATE INDEX idx_carriers_legal_name_trgm ON carriers USING gin(legal_name gin_trgm_ops);
CREATE INDEX idx_carriers_dba_name_trgm ON carriers USING gin(dba_name gin_trgm_ops);
CREATE INDEX idx_carriers_created_at ON carriers(created_at DESC);
CREATE INDEX idx_carriers_safety_rating ON carriers(safety_rating);
CREATE INDEX idx_carriers_hazmat ON carriers(hazmat_flag) WHERE hazmat_flag = TRUE;

-- Create initial partitions (monthly partitions for better management)
-- We'll create partitions for the current year and next year
DO $$
DECLARE
    start_date DATE := DATE_TRUNC('month', CURRENT_DATE);
    end_date DATE;
    partition_name TEXT;
BEGIN
    FOR i IN 0..23 LOOP
        end_date := start_date + INTERVAL '1 month';
        partition_name := 'carriers_' || TO_CHAR(start_date, 'YYYY_MM');
        
        EXECUTE format('
            CREATE TABLE IF NOT EXISTS %I PARTITION OF carriers
            FOR VALUES FROM (%L) TO (%L)',
            partition_name,
            start_date,
            end_date
        );
        
        start_date := end_date;
    END LOOP;
END $$;

-- Function for automatic partition creation (for future dates)
CREATE OR REPLACE FUNCTION create_monthly_partition()
RETURNS VOID AS $$
DECLARE
    partition_date DATE;
    partition_name TEXT;
    start_date DATE;
    end_date DATE;
BEGIN
    partition_date := DATE_TRUNC('month', CURRENT_DATE + INTERVAL '2 months');
    partition_name := 'carriers_' || TO_CHAR(partition_date, 'YYYY_MM');
    start_date := partition_date;
    end_date := partition_date + INTERVAL '1 month';
    
    -- Check if partition already exists
    IF NOT EXISTS (
        SELECT 1 FROM pg_class
        WHERE relname = partition_name
    ) THEN
        EXECUTE format('
            CREATE TABLE %I PARTITION OF carriers
            FOR VALUES FROM (%L) TO (%L)',
            partition_name,
            start_date,
            end_date
        );
        RAISE NOTICE 'Created partition: %', partition_name;
    END IF;
END;
$$ LANGUAGE plpgsql;

-- Function for insurance expiration calculations
CREATE OR REPLACE FUNCTION get_insurance_expiring(days_ahead INTEGER)
RETURNS TABLE (
    id UUID,
    usdot_number INTEGER,
    legal_name TEXT,
    dba_name TEXT,
    physical_state VARCHAR(2),
    telephone VARCHAR(20),
    email TEXT,
    liability_insurance_date DATE,
    liability_insurance_amount DECIMAL(12,2),
    days_until_expiration INTEGER
) AS $$
BEGIN
    RETURN QUERY
    SELECT 
        c.id,
        c.usdot_number,
        c.legal_name,
        c.dba_name,
        c.physical_state,
        c.telephone,
        c.email,
        c.liability_insurance_date,
        c.liability_insurance_amount,
        (c.liability_insurance_date - CURRENT_DATE)::INTEGER as days_until_expiration
    FROM carriers c
    WHERE c.liability_insurance_date BETWEEN CURRENT_DATE AND CURRENT_DATE + INTERVAL '1 day' * days_ahead
    AND c.operating_status = 'ACTIVE'
    ORDER BY c.liability_insurance_date, c.legal_name;
END;
$$ LANGUAGE plpgsql;

-- Function to get carriers with expired insurance
CREATE OR REPLACE FUNCTION get_expired_insurance()
RETURNS TABLE (
    id UUID,
    usdot_number INTEGER,
    legal_name TEXT,
    dba_name TEXT,
    physical_state VARCHAR(2),
    telephone VARCHAR(20),
    email TEXT,
    liability_insurance_date DATE,
    days_expired INTEGER
) AS $$
BEGIN
    RETURN QUERY
    SELECT 
        c.id,
        c.usdot_number,
        c.legal_name,
        c.dba_name,
        c.physical_state,
        c.telephone,
        c.email,
        c.liability_insurance_date,
        (CURRENT_DATE - c.liability_insurance_date)::INTEGER as days_expired
    FROM carriers c
    WHERE c.liability_insurance_date < CURRENT_DATE
    AND c.operating_status = 'ACTIVE'
    ORDER BY c.liability_insurance_date DESC;
END;
$$ LANGUAGE plpgsql;

-- Function to search carriers by name (using trigram similarity)
CREATE OR REPLACE FUNCTION search_carriers_by_name(search_term TEXT, similarity_threshold FLOAT DEFAULT 0.3)
RETURNS TABLE (
    id UUID,
    usdot_number INTEGER,
    legal_name TEXT,
    dba_name TEXT,
    physical_state VARCHAR(2),
    operating_status VARCHAR(50),
    similarity_score FLOAT
) AS $$
BEGIN
    RETURN QUERY
    SELECT 
        c.id,
        c.usdot_number,
        c.legal_name,
        c.dba_name,
        c.physical_state,
        c.operating_status,
        GREATEST(
            similarity(c.legal_name, search_term),
            COALESCE(similarity(c.dba_name, search_term), 0)
        ) as similarity_score
    FROM carriers c
    WHERE 
        c.legal_name % search_term
        OR c.dba_name % search_term
    ORDER BY similarity_score DESC
    LIMIT 100;
END;
$$ LANGUAGE plpgsql;

-- Trigger to update the updated_at timestamp
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER update_carriers_updated_at 
    BEFORE UPDATE ON carriers
    FOR EACH ROW 
    EXECUTE FUNCTION update_updated_at_column();

-- Create view for active carriers with insurance status
CREATE OR REPLACE VIEW active_carriers_insurance_status AS
SELECT 
    id,
    usdot_number,
    legal_name,
    dba_name,
    physical_state,
    physical_city,
    entity_type,
    operating_status,
    liability_insurance_date,
    liability_insurance_amount,
    CASE 
        WHEN liability_insurance_date IS NULL THEN 'unknown'
        WHEN liability_insurance_date < CURRENT_DATE THEN 'expired'
        WHEN liability_insurance_date <= CURRENT_DATE + INTERVAL '30 days' THEN 'expiring_soon'
        WHEN liability_insurance_date <= CURRENT_DATE + INTERVAL '60 days' THEN 'expiring_60_days'
        WHEN liability_insurance_date <= CURRENT_DATE + INTERVAL '90 days' THEN 'expiring_90_days'
        ELSE 'valid'
    END as insurance_status,
    CASE 
        WHEN liability_insurance_date IS NOT NULL THEN 
            (liability_insurance_date - CURRENT_DATE)::INTEGER
        ELSE NULL
    END as days_until_expiration
FROM carriers
WHERE operating_status = 'ACTIVE';

-- Create materialized view for statistics (refresh daily)
CREATE MATERIALIZED VIEW IF NOT EXISTS carrier_statistics AS
SELECT 
    physical_state,
    COUNT(*) as total_carriers,
    COUNT(CASE WHEN operating_status = 'ACTIVE' THEN 1 END) as active_carriers,
    COUNT(CASE WHEN hazmat_flag = TRUE THEN 1 END) as hazmat_carriers,
    COUNT(CASE WHEN liability_insurance_date < CURRENT_DATE THEN 1 END) as expired_insurance,
    COUNT(CASE WHEN liability_insurance_date BETWEEN CURRENT_DATE AND CURRENT_DATE + INTERVAL '30 days' THEN 1 END) as expiring_30_days,
    AVG(power_units) as avg_power_units,
    AVG(drivers) as avg_drivers,
    MAX(updated_at) as last_update
FROM carriers
GROUP BY physical_state;

-- Create index on materialized view
CREATE INDEX idx_carrier_statistics_state ON carrier_statistics(physical_state);

-- Function to refresh statistics
CREATE OR REPLACE FUNCTION refresh_carrier_statistics()
RETURNS VOID AS $$
BEGIN
    REFRESH MATERIALIZED VIEW CONCURRENTLY carrier_statistics;
END;
$$ LANGUAGE plpgsql;

-- Add comments for documentation
COMMENT ON TABLE carriers IS 'Main table storing FMCSA carrier information, partitioned by created_at for optimal performance with 2.2M+ records';
COMMENT ON COLUMN carriers.usdot_number IS 'Unique USDOT number assigned by FMCSA';
COMMENT ON COLUMN carriers.raw_data IS 'Complete FMCSA record in JSON format for reference and audit';
COMMENT ON FUNCTION get_insurance_expiring IS 'Returns carriers with insurance expiring within specified days';
COMMENT ON VIEW active_carriers_insurance_status IS 'View showing active carriers with calculated insurance status';