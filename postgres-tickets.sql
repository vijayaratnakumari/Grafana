CREATE TABLE tickets (
    id SERIAL PRIMARY KEY,
    ticket_number VARCHAR(255) UNIQUE,
    project_name VARCHAR(255),
    job_name VARCHAR(255),
    company_name VARCHAR(255),             -- construction company
    trucking_company_name VARCHAR(255),    -- trucking company
    driver_name VARCHAR(255),
    created_at TIMESTAMP,
    ticket_date TIMESTAMP WITH TIME ZONE,
    start_date TIMESTAMP,
    end_date TIMESTAMP,
    price_per_hour NUMERIC,
    travel_time_minutes INTEGER,
    pricing_model VARCHAR(50),
    ticket_status VARCHAR(50),
    completed_trip_count INTEGER,
    total_cost NUMERIC,
    total_time_minutes INTEGER,
    truck_charges NUMERIC,
    price_per_trip NUMERIC,
    price_per_mile NUMERIC,
    price_per_load NUMERIC,
    fixed_price NUMERIC
);