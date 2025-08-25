## FEATURE:

 Database Management System

Centralized ingestion and management of the FMCSA Company Census File (USDOT dataset)

Enables search, lead generation, compliance monitoring, and exports

Built with PostgreSQL + Python (FastAPI/Django/Flask) + React dashboard

Automatically refreshes 2.2M+ USDOT records from the official FMCSA API/CSV
## EXAMPLES:

In the examples/ folder you should provide:

examples/import_script.py → Demonstrates API pagination ($limit + $offset) to fetch all 2.2M rows and insert into PostgreSQL.

examples/query_examples.sql → Common search queries:

Lookup by USDOT number

Filter by insurance expiring in 30/60/90 days

Search by state and carrier type

examples/dashboard_demo.py → Mock FastAPI/React integration showing how a search result flows from DB → API → frontend table.

examples/export_to_csv.py → Example of exporting query results into CSV/Excel with proper field mapping.

## DOCUMENTATION:

Primary documentation sources:

FMCSA Company Census API: https://data.transportation.gov/resource/az4n-8mr2.json

PostgreSQL Performance & Partitioning: https://www.postgresql.org/docs/current/partitioning.html

FastAPI Docs: https://fastapi.tiangolo.com/

React + Tailwind Dashboard UI: https://tailwindcss.com/docs
 & https://react.dev/

Pandas CSV/Excel Export: https://pandas.pydata.org/docs/reference/api/pandas.DataFrame.to_csv.html

(Optional for large-data handling) Dask / Polars docs for faster ETL pipelines

## OTHER CONSIDERATIONS:

Scale: Dataset is large (2.2M+ rows, ~1.5GB CSV). Must design PostgreSQL with indexes, partitions, and connection pooling.

API Limits: The FMCSA API defaults to 1000 rows per call → use $limit + $offset to paginate until all rows are collected.

Automated Refresh: Set up cron/scheduler to re-ingest updates weekly or daily.

Normalization: Data fields can be inconsistent (e.g., company names, addresses). Add preprocessing/validation.

Export Gotchas: Excel often breaks with large datasets → provide both CSV and XLSX export.

Lead Generation Logic: Must calculate insurance expiration (30/60/90 days) dynamically, not just as raw dates.

Security: Ensure authentication on dashboard (avoid exposing the full national dataset openly).

Testing: Use subsets of 50k–100k records for dev/testing to avoid full 2.2M loads.
