# Grafana dashboards and ETL (MongoDB → PostgreSQL)

This repository contains schema, a lightweight ETL, and example Grafana queries to visualize per-project daily operational KPIs (loads, trucks, billable hours, cost, trips, and derived metrics).

Contents
- `postgres.sql` — DDL for `projects`, `daily_stats`, `etl_checkpoint`, `daily_stats_view`, and useful indexes.
- `project.py` — ETL that reads MongoDB trip documents, aggregates per project+day, and upserts into Postgres.
- `requirements.txt` — Python dependencies.
- `Grafana Dashboard Panel queries/` — example panel JSONs and saved queries.

Quick start (Grafana with Docker)
Run Grafana (persistent, restart-enabled):

```bash
docker run -d \
  --name grafana \
  --restart=always \
  --add-host=host.docker.internal:host-gateway \
  -p 3002:3000 \
  -v grafana-storage:/var/lib/grafana \
  grafana/grafana:latest
```

PostgreSQL setup (example)
Replace placeholders with secure values.

Install (Amazon Linux 2 example):

```bash
amazon-linux-extras list | grep postgresql
sudo amazon-linux-extras enable postgresql14
sudo yum clean metadata
sudo yum install -y postgresql postgresql-server
```

Initialize and start:

```bash
sudo postgresql-setup --initdb
sudo systemctl enable postgresql
sudo systemctl start postgresql
sudo systemctl status postgresql
```

Create DB and user (run as postgres system user):

```bash
sudo -i -u postgres psql
CREATE DATABASE etl_db;
CREATE USER etl_user WITH ENCRYPTED PASSWORD '<change-this-secure-password>';
GRANT ALL PRIVILEGES ON DATABASE etl_db TO etl_user;
\q
```

Apply schema:

```bash
psql -U etl_user -d etl_db -f "/path/to/postgres.sql"
```

Notes on authentication and remote access
- If you see "Peer authentication failed", change the relevant method in `pg_hba.conf` from `peer` to `md5` or `scram-sha-256`, then restart Postgres.
- To allow TCP access, set `listen_addresses` in `postgresql.conf` and add an appropriate `host ...` entry to `pg_hba.conf`. Restart Postgres after changes.

ETL: project.py
Overview:
- Connects to MongoDB, queries trip documents since the last checkpoint (stored in `etl_checkpoint`), aggregates per project+day, and upserts into `daily_stats`.

Environment variables:
- `MONGO_URI` (default: `mongodb://localhost:27017`)
- `MONGO_DB` (default: `haulr`)
- `MONGO_COLLECTION` (default: `trickets`)
- `PG_CONN` (Postgres connection string, e.g. `postgresql://user:pass@host:5432/db`)

Run locally / schedule (Windows PowerShell example)

Create and activate virtualenv and install dependencies:

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

Test-run:

```powershell
python3 project.py
```

Schedule: use cron, systemd timer, Airflow, or another scheduler. The script updates `etl_checkpoint` and can run incrementally.

Important: `project.py` expects fields such as `start_time`, `end_time`, `cost`, `project_key`, `truck_id`, and `load_id`. Adjust transform logic if your Mongo schema differs.

Grafana: connect to Postgres and build dashboards
1. Add a PostgreSQL data source in Grafana:
   - Host: <postgres_host>:5432
   - Database: `etl_db`
   - User: `etl_user`
   - Password: (enter securely)
   - SSL Mode: configure for your environment

2. Use `daily_stats_view` for panels. Example queries below.

Table panel (core metrics) — SQL
Use this query in a Table panel (replace `$project_key` or set a dashboard variable):

```sql
SELECT
  day,
  number_of_trucks,
  number_of_loads,
  billable_hours,
  cost_per_day,
  average_trips_per_hour,
  average_cost_per_trip
FROM daily_stats_view
WHERE project_key = '$project_key'
ORDER BY day DESC
LIMIT 100;
```

Timeseries / SingleStat (average cost per trip) — SQL
Use this query in a Time series or SingleStat panel:

```sql
SELECT
  day,
  average_cost_per_trip
FROM daily_stats_view
WHERE project_key = 'project_abc'
ORDER BY day;
```

Troubleshooting
- ModuleNotFoundError: No module named `pymongo` — install dependencies:

```bash
pip install -r requirements.txt
```

- Permission errors for Postgres commands — run as the `postgres` system user:

```bash
sudo -i -u postgres
```

- Authentication issues — review `pg_hba.conf` and restart Postgres after changes.

Security & operational notes
- Never commit secrets. Use environment variables or a secrets manager (Vault, AWS Secrets Manager).
- Use strong passwords and restrict Postgres network access to trusted hosts.
- Enable TLS/SSL for Postgres and Grafana in production and rotate admin credentials after initial login.

AWS (example deployment summary)
- Place Grafana behind an ALB with TLS termination. Restrict ALB ingress to trusted IPs or VPN.
- Register EC2/Grafana targets on port 3002 and configure health checks.
- Use Route 53 (or equivalent) to map a DNS name to the ALB.

Contact / support
- For questions about schema or ETL logic, open an issue with sample documents and expected results.