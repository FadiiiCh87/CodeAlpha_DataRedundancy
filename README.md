# Data Redundancy Removal

CodeAlpha Cloud Computing Internship project.

Flask and SQLAlchemy app validating names and emails, normalizing emails, rejecting duplicate entries, and storing unique records.

## Local setup

```bash
python -m venv .venv
# Activate the virtual environment
pip install -r requirements.txt
python app.py
```

Open http://127.0.0.1:5000.

## Tests

```bash
python -m pytest -q
```

## Configuration

SQLite is used by default; set DATABASE_URL for a supported remote database.

## Files

- `app.py`: Flask backend
- `templates/index.html`: frontend
- `static/style.css`: UI
- `tests/test_app.py`: tests
- `requirements.txt`: dependencies
- `Procfile`: Gunicorn startup

## Scope

Educational prototype. Deployment and production security review have not been completed.
