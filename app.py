import csv, hashlib, io, os, re
from datetime import datetime, timezone
from difflib import SequenceMatcher
from flask import Flask, jsonify, request, render_template
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.exc import IntegrityError

app = Flask(__name__)
app.config["MAX_CONTENT_LENGTH"] = 2 * 1024 * 1024
app.config["SQLALCHEMY_DATABASE_URI"] = os.getenv("DATABASE_URL", "sqlite:///redundancy.db").replace("postgres://", "postgresql://", 1)
db = SQLAlchemy(app)

class Record(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(120), nullable=False)
    email = db.Column(db.String(254), nullable=False, unique=True)
    fingerprint = db.Column(db.String(64), nullable=False, unique=True)
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))

def normalize(data):
    if not isinstance(data, dict):
        raise ValueError("A JSON object is required")
    name = " ".join(str(data.get("name") or "").split()).strip()
    email = str(data.get("email") or "").strip().lower()
    if not (2 <= len(name) <= 120 and len(email) <= 254 and re.fullmatch(r"[^\s@]+@[^\s@]+\.[^\s@]+", email)):
        raise ValueError("Valid name (2-120 characters) and email are required")
    return name, email

def fingerprint(email):
    return hashlib.sha256(email.encode("utf-8")).hexdigest()

@app.get("/")
def home():
    return render_template("index.html")

@app.get("/health")
def health():
    return jsonify(status="ok")

@app.get("/api/stats")
def stats():
    return jsonify(unique_records=db.session.query(Record).count(), algorithm="normalized email SHA-256")

@app.get("/api/records")
def list_records():
    # Public demo must not expose full customer email addresses.
    rows = Record.query.order_by(Record.id.desc()).limit(100).all()
    return jsonify([{"id": row.id, "name": row.name, "email": row.email.split("@")[0][:2] + "***@" + row.email.split("@")[1]} for row in rows])

@app.post("/api/records")
def create():
    try:
        name, email = normalize(request.get_json(silent=True))
    except ValueError as exc:
        return jsonify(status="invalid", error=str(exc)), 400
    existing = Record.query.filter_by(email=email).first()
    if existing:
        return jsonify(status="redundant", classification="duplicate", existing_id=existing.id), 409
    try:
        row = Record(name=name, email=email, fingerprint=fingerprint(email))
        db.session.add(row)
        db.session.commit()
    except IntegrityError:
        db.session.rollback()
        return jsonify(status="redundant", classification="duplicate"), 409
    return jsonify(status="unique_verified", id=row.id), 201

@app.post("/api/analyze")
def analyze():
    """Analyze an uploaded CSV in memory without storing its personal data."""
    upload = request.files.get("file")
    if not upload or not upload.filename.lower().endswith(".csv"):
        return jsonify(error="Upload a CSV file with name and email columns"), 400
    try:
        content = upload.read().decode("utf-8-sig")
        reader = csv.DictReader(io.StringIO(content))
        if not reader.fieldnames or not {"name", "email"}.issubset(set(reader.fieldnames)):
            return jsonify(error="CSV must contain name and email columns"), 400
        seen, unique, duplicates, invalid = {}, [], [], []
        for index, data in enumerate(reader, start=2):
            if index > 502:
                return jsonify(error="Maximum 500 rows per upload"), 413
            try:
                name, email = normalize(data)
            except ValueError:
                invalid.append(index)
                continue
            if email in seen:
                duplicates.append({"row": index, "original_row": seen[email], "email": email})
            else:
                seen[email] = index
                unique.append({"name": name, "email": email})
        return jsonify(total=len(unique)+len(duplicates)+len(invalid), unique=len(unique), duplicate_count=len(duplicates), invalid_rows=invalid, duplicates=duplicates, cleaned_records=unique)
    except (UnicodeError, csv.Error):
        return jsonify(error="Invalid UTF-8 CSV"), 400

@app.post("/api/similarity")
def similarity():
    data = request.get_json(silent=True) or {}
    a, b = str(data.get("first", ""))[:120], str(data.get("second", ""))[:120]
    if not a.strip() or not b.strip():
        return jsonify(error="Both names are required"), 400
    score = round(SequenceMatcher(None, " ".join(a.lower().split()), " ".join(b.lower().split())).ratio() * 100, 1)
    return jsonify(similarity_percent=score, possible_match=score >= 80, note="Suggestion only; never automatically merge")

with app.app_context():
    db.create_all()

if __name__ == "__main__":
    app.run(debug=os.getenv("FLASK_DEBUG") == "1")
