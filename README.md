# Smart Data Quality Platform — CodeAlpha

## Features
- Normalized-email SHA-256 duplicate detection backed by a database uniqueness constraint.
- CSV upload (UTF-8, maximum 500 records and 2 MB) with unique/duplicate/invalid row report; uploaded files are processed in memory, not persisted.
- Download cleaned CSV from the browser. Compare two names using an indicative similarity score (not identity verification).
- Statistics endpoint and masked email listing for the public demo.

## API
- GET /health, GET /api/stats, GET /api/records
- POST /api/records JSON: {"name":"Alice","email":"alice@example.com"}
- POST /api/analyze multipart form-data: file=sample.csv
- POST /api/similarity JSON: {"first":"Alice Smith","second":"alice smith"}

## Deployment
Run `pip install -r requirements.txt && gunicorn app:app`. Set `DATABASE_URL` to a PostgreSQL connection URL for persistence. Without it, SQLite is used and data on ephemeral cloud storage may disappear. Do not put credentials in GitHub.

## Testing
`python -m pytest -q`. GitHub Actions runs tests on pushes and pull requests.

## Limitations
Educational demo: no authentication for writes; public listing masks emails but still shows names. Use access control and abuse prevention before handling real customer data. Fuzzy matching is advisory, not automatic merging.
