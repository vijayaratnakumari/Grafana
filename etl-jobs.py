import os
from pymongo import MongoClient
import psycopg2

# -------- CONFIG ----------
MONGO_URI = os.getenv("MONGODB_CONNECTION_STRING", "mongodb+srv://trailr_dev:Password1%21@cluster0.g3k54zd.mongodb.net/truckr")
MONGO_DB = os.getenv("MONGO_DB", "truckr")
JOBS_COLLECTION = os.getenv("JOBS_COLLECTION", "jobs")
PROJECTS_COLLECTION = os.getenv("PROJECTS_COLLECTION", "projects")

PG_DBNAME = os.getenv("PG_DBNAME", "etl_db")
PG_USER = os.getenv("PG_USER", "etl_user")
PG_PASSWORD = os.getenv("PG_PASSWORD", "Haulr@10thSep2025")
PG_HOST = os.getenv("PG_HOST", "localhost")
PG_PORT = os.getenv("PG_PORT", "5432")

# -------- CONNECTIONS ----------
mongo_client = MongoClient(MONGO_URI)
db = mongo_client[MONGO_DB]

pg_conn = psycopg2.connect(
    dbname=PG_DBNAME,
    user=PG_USER,
    password=PG_PASSWORD,
    host=PG_HOST,
    port=PG_PORT
)
pg_cursor = pg_conn.cursor()

# --------------------
# Fetch projects for name resolution
# --------------------
projects = {str(p["_id"]): p.get("name") for p in db[PROJECTS_COLLECTION].find()}

# --------------------
# 2. Process jobs
# --------------------
for doc in db[JOBS_COLLECTION].find():

    job_id = str(doc.get("_id"))
    name = doc.get("name")
    createdBy = str(doc.get("createdBy")) if doc.get("createdBy") else None
    projectId = str(doc.get("projectId")) if doc.get("projectId") else None
    project_name = projects.get(projectId, None)  # Resolve project name
    status = doc.get("status")
    costPerUnit = doc.get("costPerUnit")
    notes = doc.get("notes")
    travelTime = doc.get("travelTime")
    pricingModel = doc.get("pricingModel")
    scheduleStart = doc.get("scheduleStart")
    scheduleEnd = doc.get("scheduleEnd")
    pickupTime = doc.get("pickupTime")
    pickupFrequency = doc.get("pickupFrequency")
    createdAt = doc.get("createdAt")
    version = doc.get("__v")

    # Insert into jobs table (matches your schema)
    pg_cursor.execute("""
        INSERT INTO jobs (
            job_id, name, createdBy, project_name, status, costPerUnit, notes, travelTime,
            pricingModel, scheduleStart, scheduleEnd, pickupTime, pickupFrequency, createdAt, version
        )
        VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)
        ON CONFLICT (job_id) DO NOTHING;
    """, (
        job_id, name, createdBy, project_name, status, costPerUnit, notes, travelTime,
        pricingModel, scheduleStart, scheduleEnd, pickupTime, pickupFrequency, createdAt, version
    ))

    # --------------------
    # 3. Nested: Truck Categories
    # --------------------
    for t in doc.get("truckCategories", []):
        pg_cursor.execute("""
            INSERT INTO job_truck_categories (job_id, name, count, allocated)
            VALUES (%s, %s, %s, %s)
            ON CONFLICT DO NOTHING;
        """, (
            job_id,
            t.get("name"),
            int(t.get("count", 0)),
            int(t.get("allocated", 0))
        ))

    # --------------------
    # 4. Nested: Pickup Locations
    # --------------------
    for p in doc.get("pickuplocations", []):
        pg_cursor.execute("""
            INSERT INTO job_pickup_locations (job_id, description, latitude, longitude, address, city, state, zip)
            VALUES (%s,%s,%s,%s,%s,%s,%s,%s)
            ON CONFLICT DO NOTHING;
        """, (
            job_id,
            p.get("description"),
            p.get("latitude"),
            p.get("longitude"),
            p.get("address"),
            p.get("city"),
            p.get("state"),
            p.get("zip")
        ))

    # --------------------
    # 5. Nested: Drop Locations
    # --------------------
    for d in doc.get("droplocations", []):
        pg_cursor.execute("""
            INSERT INTO job_drop_locations (job_id, description, latitude, longitude, address, city, state, zip)
            VALUES (%s,%s,%s,%s,%s,%s,%s,%s)
            ON CONFLICT DO NOTHING;
        """, (
            job_id,
            d.get("description"),
            d.get("latitude"),
            d.get("longitude"),
            d.get("address"),
            d.get("city"),
            d.get("state"),
            d.get("zip")
        ))

    # --------------------
    # 6. Nested: Trucking Companies
    # --------------------
    for c in doc.get("truckingCompanies", []):
        pg_cursor.execute("""
            INSERT INTO job_trucking_companies (job_id, company_id)
            VALUES (%s, %s)
            ON CONFLICT DO NOTHING;
        """, (
            job_id, str(c)
        ))

    # --------------------
    # 7. Nested: Supervisors
    # --------------------
    for s in doc.get("supervisors", []):
        pg_cursor.execute("""
            INSERT INTO job_supervisors (job_id, supervisor_id)
            VALUES (%s, %s)
            ON CONFLICT DO NOTHING;
        """, (
            job_id, str(s)
        ))

# --------------------
# 8. Commit changes
# --------------------
pg_conn.commit()
pg_cursor.close()
pg_conn.close()
mongo_client.close()
print("✅ Jobs ETL completed successfully!")