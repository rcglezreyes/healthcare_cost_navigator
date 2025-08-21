# MS-DRG Provider API

Minimal FastAPI service with async SQLAlchemy, PostgreSQL, Swagger, ETL from the official CMS CSV link, ratings, and an NL assistant. Radius filtering uses ZIP centroids with pgeocode. No styling.

## Run

docker compose up -d --build
http://localhost:8000/docs

## ETL

On startup the app runs migrations and ETL. It reads from ETL_CSV_URL if set; otherwise ETL_CSV_PATH. Ratings are loaded from RATINGS_CSV_PATH if present; otherwise generated 1–10.

Default env in compose:
ETL_CSV_URL=https://data.cms.gov/sites/default/files/2024-05/7d1f4bcd-7dd9-4fd1-aa7f-91cd69e452d3/MUP_INP_RY24_P03_V10_DY22_PrvSvc.CSV

## Endpoints

GET /providers
Params: drg (code or text), zip, radius_km, limit, offset, sort_by in [average_covered_charges, average_total_payments, rating, distance_km], order in [asc, desc]

Examples:
curl "http://localhost:8000/providers?drg=470&zip=10001&radius_km=40"
curl "http://localhost:8000/providers?drg=Heart%20Failure&zip=10032&radius_km=50&sort_by=rating&order=desc"

POST /ask
Body: {"question": "..."}
Examples:
curl -X POST http://localhost:8000/ask -H "Content-Type: application/json" -d '{"question":"Who is cheapest for DRG 470 within 25 miles of 10001?"}'
curl -X POST http://localhost:8000/ask -H "Content-Type: application/json" -d '{"question":"Who has the best ratings for heart surgery near 10032?"}'
curl -X POST http://localhost:8000/ask -H "Content-Type: application/json" -d '{"question":"Top ratings for DRG 003 near 10029 within 60 km"}'
curl -X POST http://localhost:8000/ask -H "Content-Type: application/json" -d '{"question":"Cheapest for knee replacement near 10016 within 30 km"}'
curl -X POST http://localhost:8000/ask -H "Content-Type: application/json" -d '{"question":"What is the weather today?"}'

Out-of-scope questions return guidance.

## Concurrency

The service is fully async. The /ask endpoint runs concurrent ranking tasks with asyncio.gather.

## Schema

providers(provider_id, provider_name, provider_city, provider_state, provider_zip_code)
drg_prices(provider_id, ms_drg_definition, ms_drg_code, totals and costs)
ratings(provider_id, rating, created_at)

## Notes

Distance is computed at request time using ZIP centroids via pgeocode. No lat/lon is stored in the database.
