-- Main Jobs table
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
    scheduleStart NUMERIC,
    scheduleEnd NUMERIC,
    pickupTime NUMERIC,
    pickupFrequency TEXT,
    createdAt NUMERIC,
    version INT,
    created_at TIMESTAMP DEFAULT NOW()
);

-- Nested arrays: truck categories
CREATE TABLE IF NOT EXISTS job_truck_categories (
    id SERIAL PRIMARY KEY,
    job_id TEXT REFERENCES jobs(job_id) ON DELETE CASCADE,
    name TEXT,
    count INT,
    allocated INT
);

-- Nested arrays: pickup locations
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

-- Nested arrays: drop locations
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

-- Nested arrays: trucking companies
CREATE TABLE IF NOT EXISTS job_trucking_companies (
    id SERIAL PRIMARY KEY,
    job_id TEXT REFERENCES jobs(job_id) ON DELETE CASCADE,
    company_id TEXT
);

-- Nested arrays: supervisors
CREATE TABLE IF NOT EXISTS job_supervisors (
    id SERIAL PRIMARY KEY,
    job_id TEXT REFERENCES jobs(job_id) ON DELETE CASCADE,
    supervisor_id TEXT
);