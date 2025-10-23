# Grafana
This is for Grafana dashboard queries list. 

You can directly pull and run it using:


docker run -d --name=grafana --network ratna -p 3002:3000  -v grafana-storage:/var/lib/grafana grafana/grafana:latest
docker stop grafana
docker rm grafana
Then reload PostgreSQL:
# Grafana dashboards and ETL (MongoDB → PostgreSQL)

This repository contains SQL schema, ETL code, and example Grafana queries for building dashboards that surface per-project daily statistics (loads, trucks, billable hours, cost, trips, and derived metrics).

The goal is to provide a lightweight pipeline and Grafana-ready view that makes it simple to visualize operational KPIs per project by day.

Contents
- `postgres.sql` — DDL for the `projects`, `daily_stats`, and `etl_checkpoint` tables plus `daily_stats_view` and helpful indexes.
- `project.py` — Small ETL script that reads trip documents from MongoDB, aggregates per project+day, and upserts into PostgreSQL.
- `requirements.txt` — Python dependencies for the ETL.
- Example Grafana queries and dashboard panel JSONs are included in the "Grafana Dashboard Panel queries" folder.

Quick start (Docker Grafana)

1. Run Grafana (example):

   docker run -d --name grafana -p 3002:3000 -v grafana-storage:/var/lib/grafana grafana/grafana:latest

2. Stop / remove:

   docker stop grafana; docker rm grafana

3. Run with restart and host gateway mapping (optional):

   docker run -d --name grafana --restart=always --add-host=host.docker.internal:host-gateway -p 3002:3000 -v grafana-storage:/var/lib/grafana grafana/grafana:latest

PostgreSQL setup (example on Linux / EC2)

These are example commands and notes used while testing. Replace passwords, IPs, and usernames with secure values in your deployment.

1. Install (Amazon Linux 2 example):

   # list available PostgreSQL extras
   amazon-linux-extras list | grep postgresql

   # enable PostgreSQL 14 if available
   sudo amazon-linux-extras enable postgresql14
   sudo yum clean metadata
   sudo yum install -y postgresql postgresql-server

2. Initialize DB and start service:

   sudo postgresql-setup --initdb
   sudo systemctl enable postgresql
   sudo systemctl start postgresql
   sudo systemctl status postgresql

3. Create DB / user (example):

   sudo -i -u postgres psql
   CREATE DATABASE etl_db;
   CREATE USER etl_user WITH ENCRYPTED PASSWORD '<change-this-secure-password>';
   GRANT ALL PRIVILEGES ON DATABASE etl_db TO etl_user;
   \q

4. Run the DDL to create schema:

   psql -U etl_user -d etl_db -f "/path/to/postgres.sql"

Notes on authentication and remote access
- If you get "Peer authentication failed" change the local authentication method in `pg_hba.conf` from `peer` to `md5` (or `scram-sha-256`) for the relevant user/connection type, then restart Postgres.
- To allow TCP access, set `listen_addresses` in `postgresql.conf` (for example `'*'` or `localhost`) and add an appropriate `host ...` line to `pg_hba.conf` with `md5`/`scram-sha-256`.
- After editing config files, restart with `sudo systemctl restart postgresql`.

ETL: project.py

Overview:
- Connects to MongoDB, queries trip documents since the last checkpoint (stored in `etl_checkpoint`), aggregates into per-project-per-day rows and upserts into `daily_stats`.
- Use environment variables to configure connections:
  - `MONGO_URI` (default: `mongodb://localhost:27017`)
  - `MONGO_DB` (default: `haulr`)
  - `MONGO_COLLECTION` (default: `trickets`)
  - `PG_CONN` (Postgres connection string e.g. `postgresql://user:pass@host:5432/db`)

Run locally or schedule:

1. Install dependencies in a virtualenv (recommended):

   python -m venv .venv
   .\.venv\Scripts\Activate.ps1
   pip install -r requirements.txt

2. Test-run once:

   python project.py

3. Schedule: run via cron, systemd timer, or a scheduler (Airflow, etc.). The script updates `etl_checkpoint` so it can be run incrementally.

Important: `project.py` assumes certain fields on the Mongo documents (start_time, end_time, cost, project_key, truck_id, load_id). If your schema differs, update the transform logic inside the script.

Grafana: connect to Postgres and build dashboards

1. In Grafana add a PostgreSQL data source:
   - Host: <postgres_host>:5432
   - Database: `etl_db`
   - User: `etl_user`
   - Password: your password

2. Use the provided `daily_stats_view` for panels. Example queries:

   Table panel (core metrics):

   SELECT day, number_of_trucks, number_of_loads, billable_hours, cost_per_day, average_trips_per_hour, average_cost_per_trip
   FROM daily_stats_view
   WHERE project_key = '$project_key'
   ORDER BY day DESC
   LIMIT 100

   Single stat / timeseries (average cost per trip):

   SELECT day, average_cost_per_trip
   FROM daily_stats_view
   WHERE project_key = 'project_abc'
   ORDER BY day

Troubleshooting & common fixes
- ModuleNotFoundError: No module named 'pymongo' — install Python deps: `pip install -r requirements.txt`.
- Peer authentication failed — edit `pg_hba.conf` and change `peer` → `md5` for the relevant entry, then restart Postgres.
- Permission denied while running Postgres commands — some commands must be run as the `postgres` system user (via `sudo -i -u postgres`).

Security & operational notes
- Never commit real passwords or secrets to the repository. Use environment variables or a secrets store (Vault, AWS Secrets Manager, etc.).
- Use non-default passwords and restrict Postgres network access to trusted IPs only.
- Consider using TLS for Postgres and Grafana in production.

Files and purpose
- `postgres.sql` — schema & view used by Grafana dashboards.
- `project.py` — ETL script (MongoDB → Postgres). Edit the transform function to match your source schema.
- `requirements.txt` — Python packages required for the ETL.
- `Grafana Dashboard Panel queries/` — example panel JSONs and saved queries to import into Grafana.

Next steps (suggested enhancements)
- Add unit tests for the ETL transform logic (small sample docs → expected aggregated rows).
- Add a Dockerfile or systemd unit to run the ETL on a schedule.
- Add example Grafana dashboard JSON (exported) for quick import.

License
- This repository is provided as-is. Choose an appropriate license for your project.

Contact / support
- For questions about the schema or ETL logic, open an issue with example documents and expected results.

AWS (example deployment)

The following is an example pattern used to expose Grafana behind an AWS Application Load Balancer (ALB). Replace placeholder names, IPs and credentials with secure values and apply your organization's security controls.

1. Create a Target Group
   - Create a target group (e.g., bastion-tg) using the instance target type.
   - Configure the health check to use the appropriate path/port for Grafana (e.g., HTTP / on port 3002).

2. Configure the ALB and Route 53
   - Create or select an ALB and add a listener (typically 80/443) that forwards to the bastion-tg.
   - In Route 53, create a DNS record (e.g., dashboard.dev.sarithm.com) pointing to the ALB.

3. Register targets
   - Register the bastion (or EC2 instance running Grafana) with the target group and ensure it's reachable on port 3002.
   - Confirm the ALB health checks show the instance as healthy.

4. Verify access
   - Browse to: https://dashboard.dev.sarithm.com (use HTTPS in production).
   - Log in with the Grafana admin account and change the default password immediately.

5. Update Grafana PostgreSQL data source
   - In Grafana UI → Configuration → Data sources → PostgreSQL:
     - Host: host.docker.internal:5432 (or your Postgres host)
     - Database: etl_db
     - User: etl_user
     - Password: (enter securely)
     - SSL Mode: disable (only for local/testing). For production, use require/verify-full and provide certificates.
   - Click Save & Test and confirm a successful connection.

Operational and security notes
- Use HTTPS for the ALB listener and terminate TLS at the ALB or a reverse proxy — do not expose Grafana plaintext to the public internet.
- Restrict ALB security group ingress to known IPs or VPNs where possible.
- Do not store credentials in the repository; use environment variables or a secrets manager (AWS Secrets Manager, Parameter Store).
- Consider enabling Grafana authentication providers (OAuth, SSO) and enforcing strong passwords for admin accounts.
