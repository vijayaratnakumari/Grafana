import os
import logging
from datetime import datetime, timezone
from dateutil import parser as date_parser
from pymongo import MongoClient
import psycopg2
from bson import ObjectId

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")

# -------- CONFIG ----------
MONGO_URI = os.getenv("MONGODB_CONNECTION_STRING", "mongodb+srv://testuser1:7lAp1YmjN00qYHzY@haulrcorpprod.eep9gif.mongodb.net")
MONGO_DB = os.getenv("MONGO_DB", "truckr")
TICKETS_COLLECTION = os.getenv("TICKETS_COLLECTION", "tickets")

PG_DB = os.getenv("PG_DB", "prod_etl_db")
PG_USER = os.getenv("PG_USER", "prod_etl_user")
PG_PASSWORD = os.getenv("PG_PASSWORD", "Haulr@4thNov2025")
PG_HOST = os.getenv("PG_HOST", "localhost")
PG_PORT = os.getenv("PG_PORT", "5432")


def get_mongo_client():
    return MongoClient(MONGO_URI)


def get_pg_conn():
    return psycopg2.connect(
        dbname=PG_DB,
        user=PG_USER,
        password=PG_PASSWORD,
        host=PG_HOST,
        port=PG_PORT
    )


def get_name(collection, id_value, field="name"):
    if not id_value:
        return None

    _id = None
    if isinstance(id_value, ObjectId):
        _id = id_value
    elif isinstance(id_value, dict) and "$oid" in id_value:
        try:
            _id = ObjectId(id_value["$oid"])
        except Exception:
            return None
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
    if not job_id:
        return None

    try:
        if isinstance(job_id, dict) and "$oid" in job_id:
            job_oid = ObjectId(job_id["$oid"])
        elif isinstance(job_id, ObjectId):
            job_oid = job_id
        else:
            return None

        job_doc = db["jobs"].find_one({"_id": job_oid})
        if not job_doc or "projectId" not in job_doc:
            return None

        project_id = job_doc["projectId"]
        if isinstance(project_id, dict) and "$oid" in project_id:
            project_oid = ObjectId(project_id["$oid"])
        elif isinstance(project_id, ObjectId):
            project_oid = project_id
        else:
            return None

        project_doc = db["projects"].find_one({"_id": project_oid})
        return project_doc.get("name") if project_doc else None
    except Exception:
        return None


def get_int(field):
    if isinstance(field, dict):
        return int(field.get("$numberInt") or field.get("$numberDouble") or 0)
    if isinstance(field, (int, float)):
        return int(field)
    return 0


def to_datetime(value):
    """Normalize Mongo exported date formats, ISO strings, numeric timestamps to python datetime (UTC)."""
    if value is None:
        return None

    # Mongo extended JSON format: {"$date": "2023-..."} or {"$date": {"$numberLong": "167..."}}
    if isinstance(value, dict):
        if "$date" in value:
            date_val = value["$date"]
            # {"$date": {"$numberLong": "167..."}}
            if isinstance(date_val, dict) and "$numberLong" in date_val:
                try:
                    ms = int(date_val["$numberLong"])
                    return datetime.fromtimestamp(ms / 1000.0, tz=timezone.utc)
                except Exception:
                    return None
            # {"$date": "2023-...Z"}
            if isinstance(date_val, str):
                try:
                    return date_parser.parse(date_val).astimezone(timezone.utc)
                except Exception:
                    return None
        # numeric wrappers
        for key in ("$numberLong", "$numberInt", "$numberDouble"):
            if key in value:
                try:
                    ms = int(value[key])
                    # heuristics: if value looks like milliseconds (>= 1e12) treat as ms
                    if ms > 1e12:
                        return datetime.fromtimestamp(ms / 1000.0, tz=timezone.utc)
                    return datetime.fromtimestamp(ms, tz=timezone.utc)
                except Exception:
                    return None
        return None

    if isinstance(value, str):
        try:
            return date_parser.parse(value).astimezone(timezone.utc)
        except Exception:
            return None

    if isinstance(value, (int, float)):
        # heuristics: > 1e12 -> ms, else seconds
        try:
            ts = float(value)
            if ts > 1e12:
                return datetime.fromtimestamp(ts / 1000.0, tz=timezone.utc)
            return datetime.fromtimestamp(ts, tz=timezone.utc)
        except Exception:
            return None

    if isinstance(value, datetime):
        if value.tzinfo is None:
            return value.replace(tzinfo=timezone.utc)
        return value.astimezone(timezone.utc)

    return None


# -------------------
mongo_client = get_mongo_client()
db = mongo_client[MONGO_DB]
pg_conn = get_pg_conn()
pg_cursor = pg_conn.cursor()

INSERT_SQL = """
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
"""


def process_tickets():
    count = 0
    for ticket in db[TICKETS_COLLECTION].find():
        try:
            # lookups from related collections
            project_name = get_project_name(ticket.get("jobId"))
            job_name = get_name("jobs", ticket.get("jobId"), field="name")
            company_name = get_name("companies", ticket.get("constructionId"), field="name")
            trucking_company_name = get_name("companies", ticket.get("companyId"), field="name")
            driver_name = get_name("users", ticket.get("driverId"), field="firstName")

            # timestamps
            created_at = to_datetime(ticket.get("createdAt"))
            ticket_date = to_datetime(ticket.get("startDate"))
            start_date = to_datetime(ticket.get("startDate"))
            end_date = to_datetime(ticket.get("endDate"))

            params = (
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
                get_int(ticket.get("completedTripCount")),
                ticket.get("totalCost"),
                ticket.get("totalTimeMinutes"),
                ticket.get("truckCharges")
            )

            pg_cursor.execute(INSERT_SQL, params)
            count += 1
            if count % 500 == 0:
                pg_conn.commit()
                logging.info("Processed %d tickets...", count)
        except Exception as e:
            logging.exception("Failed to process ticket %s: %s", ticket.get("_id"), e)

    pg_conn.commit()
    logging.info("Processed total %d tickets.", count)


if __name__ == "__main__":
    try:
        logging.info("Starting tickets ETL...")
        process_tickets()
        logging.info("✅ Tickets ETL completed successfully!")
    finally:
        try:
            pg_cursor.close()
            pg_conn.close()
            mongo_client.close()
        except Exception:
            pass