import os
import logging
from datetime import datetime
from pymongo import MongoClient
import psycopg2
from bson import ObjectId

# -------- CONFIG ----------
MONGO_URI = os.getenv("MONGODB_CONNECTION_STRING", "mongodb+srv://trailr_dev:Password1%21@cluster0.g3k54zd.mongodb.net/truckr")
MONGO_DB = os.getenv("MONGO_DB", "truckr")
TICKETS_COLLECTION = os.getenv("TICKETS_COLLECTION", "tickets")

def get_mongo_client():
    return MongoClient(MONGO_URI)

def get_pg_conn():
    return psycopg2.connect(
        dbname="etl_db",
        user="etl_user",
        password="Haulr@10thSep2025",
        host="localhost",
        port="5432"
    )

mongo_client = get_mongo_client()
db = mongo_client[MONGO_DB]
pg_conn = get_pg_conn()
pg_cursor = pg_conn.cursor()

def get_name(collection, id_value, field="name"):
    """
    Fetches a field from another collection using ObjectId.
    """
    if not id_value:
        return None

    _id = None
    if isinstance(id_value, ObjectId):
        _id = id_value
    elif isinstance(id_value, dict) and "$oid" in id_value:
        _id = ObjectId(id_value["$oid"])
    elif isinstance(id_value, str):
        try:
            _id = ObjectId(id_value)
        except Exception:
            return None

    if not _id:
        return None

    doc = db[collection].find_one({"_id": _id})
    return doc.get(field) if doc else None

def get_project_name(job_id):
    """Resolve project name from jobId -> projectId -> project.name"""
    if not job_id:
        return None

    # Handle both {"$oid": "..."} and raw ObjectId
    if isinstance(job_id, dict) and "$oid" in job_id:
        job_oid = ObjectId(job_id["$oid"])
    elif isinstance(job_id, ObjectId):
        job_oid = job_id
    else:
        return None

    # Lookup job
    job_doc = db["jobs"].find_one({"_id": job_oid})
    if not job_doc or "projectId" not in job_doc:
        return None

    project_id = job_doc["projectId"]

    # Handle projectId both as dict and ObjectId
    if isinstance(project_id, dict) and "$oid" in project_id:
        project_oid = ObjectId(project_id["$oid"])
    elif isinstance(project_id, ObjectId):
        project_oid = project_id
    else:
        return None

    project_doc = db["projects"].find_one({"_id": project_oid})
    return project_doc.get("name") if project_doc else None


def get_int(field):
    if isinstance(field, dict):
        return int(field.get("$numberInt") or field.get("$numberDouble") or 0)
    if isinstance(field, (int, float)):
        return int(field)
    return 0


for ticket in db[TICKETS_COLLECTION].find():
    # lookups from related collections
    project_name = get_project_name(ticket.get("jobId"))
    job_name = get_name("jobs", ticket.get("jobId"), field="name")
    company_name = get_name("companies", ticket.get("constructionId"), field="name")  # construction company
    trucking_company_name = get_name("companies", ticket.get("companyId"), field="name")  # trucking company
    driver_name = get_name("users", ticket.get("driverId"), field="firstName")

    # timestamps
    created_at = datetime.fromtimestamp(ticket.get("createdAt", 0)/1000) if ticket.get("createdAt") else None
    ticket_date = datetime.fromtimestamp(ticket.get("startDate", 0)/1000) if ticket.get("startDate") else None
    start_date = datetime.fromtimestamp(ticket.get("startDate", 0)/1000) if ticket.get("startDate") else None
    end_date = datetime.fromtimestamp(ticket.get("endDate", 0)/1000) if ticket.get("endDate") else None

    # insert with upsert
    pg_cursor.execute("""
        INSERT INTO tickets (
            ticket_number, project_name, job_name, company_name, price_per_hour,
            trucking_company_name, driver_name, created_at, ticket_date,
            start_date, end_date, travel_time_minutes, pricing_model,
            ticket_status, completed_trip_count, total_cost,
            total_time_minutes, truck_charges
        ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
        ON CONFLICT (ticket_number) DO UPDATE
        SET
            project_name = EXCLUDED.project_name,
            job_name = EXCLUDED.job_name,
            company_name = EXCLUDED.company_name,
            price_per_hour = EXCLUDED.price_per_hour,
            trucking_company_name = EXCLUDED.trucking_company_name,
            driver_name = EXCLUDED.driver_name,
            created_at = EXCLUDED.created_at,
            ticket_date = EXCLUDED.ticket_date,
            start_date = EXCLUDED.start_date,
            end_date = EXCLUDED.end_date,
            travel_time_minutes = EXCLUDED.travel_time_minutes,
            pricing_model = EXCLUDED.pricing_model,
            ticket_status = EXCLUDED.ticket_status,
            completed_trip_count = EXCLUDED.completed_trip_count,
            total_cost = EXCLUDED.total_cost,
            total_time_minutes = EXCLUDED.total_time_minutes,
            truck_charges = EXCLUDED.truck_charges;
    """, (
        ticket.get("ticketNumber"),
        project_name,
        job_name,
        company_name,
        ticket.get("pricePerHour"),
        trucking_company_name,
        driver_name,
        created_at,
        ticket_date,
        start_date,
        end_date,
        ticket.get("travelTimeMinutes"),
        ticket.get("pricingModel"),
        ticket.get("ticketStatus"),
        ticket.get("completedTripCount"),
        ticket.get("totalCost"),
        ticket.get("totalTimeMinutes"),
        ticket.get("truckCharges")
    ))

pg_conn.commit()
pg_cursor.close()
pg_conn.close()
mongo_client.close()