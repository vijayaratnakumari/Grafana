-- ===========================
--  MAIN JOBS TABLE (Corrected)
-- ===========================

DROP TABLE IF EXISTS job_truck_categories CASCADE;
DROP TABLE IF EXISTS job_pickup_locations CASCADE;
DROP TABLE IF EXISTS job_drop_locations CASCADE;
DROP TABLE IF EXISTS job_trucking_companies CASCADE;
DROP TABLE IF EXISTS job_supervisors CASCADE;
DROP TABLE IF EXISTS jobs CASCADE;

CREATE TABLE IF NOT EXISTS jobs (
    job_id TEXT PRIMARY KEY,
    name TEXT,
    createdBy TEXT,
    project_name VARCHAR(255),
    status TEXT,
    costPerUnit NUMERIC,
    notes TEXT,
    travelTime NUMERIC,
    pricingModel TEXT,
    scheduleStart TIMESTAMP,
    scheduleEnd TIMESTAMP,
    pickupTime TIMESTAMP,
    pickupFrequency TEXT,
    createdAt TIMESTAMP,
    version INT,
    created_at TIMESTAMP DEFAULT NOW()
);

-- =================================
--  JOB TRUCK CATEGORIES (Sub-table)
-- =================================

CREATE TABLE IF NOT EXISTS job_truck_categories (
    id SERIAL PRIMARY KEY,
    job_id TEXT REFERENCES jobs(job_id) ON DELETE CASCADE,
    name TEXT,
    count INT,
    allocated INT
);

-- ==============================
--  JOB PICKUP LOCATIONS (Sub-table)
-- ==============================

CREATE TABLE IF NOT EXISTS job_pickup_locations (
    id SERIAL PRIMARY KEY,
    job_id TEXT REFERENCES jobs(job_id) ON DELETE CASCADE,
    description TEXT,
    latitude NUMERIC,
    longitude NUMERIC,
    address TEXT,
    city TEXT,
    state TEXT,
    zip TEXT
);

-- =============================
--  JOB DROP LOCATIONS (Sub-table)
-- =============================

CREATE TABLE IF NOT EXISTS job_drop_locations (
    id SERIAL PRIMARY KEY,
    job_id TEXT REFERENCES jobs(job_id) ON DELETE CASCADE,
    description TEXT,
    latitude NUMERIC,
    longitude NUMERIC,
    address TEXT,
    city TEXT,
    state TEXT,
    zip TEXT
);

-- ====================================
--  JOB TRUCKING COMPANIES (Sub-table)
-- ====================================

CREATE TABLE IF NOT EXISTS job_trucking_companies (
    id SERIAL PRIMARY KEY,
    job_id TEXT REFERENCES jobs(job_id) ON DELETE CASCADE,
    company_id TEXT
);

-- =============================
--  JOB SUPERVISORS (Sub-table)
-- =============================

CREATE TABLE IF NOT EXISTS job_supervisors (
    id SERIAL PRIMARY KEY,
    job_id TEXT REFERENCES jobs(job_id) ON DELETE CASCADE,
    supervisor_id TEXT
);