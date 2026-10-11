import io, sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from app import app, db, Record

def test_record_validation_and_masking():
    app.config["TESTING"] = True
    with app.app_context():
        db.session.query(Record).delete()
        db.session.commit()
    with app.test_client() as c:
        assert c.post("/api/records", json={"name": "Test User", "email": "TEST@example.com"}).status_code == 201
        assert c.post("/api/records", json={"name": "Other", "email": "test@example.com"}).status_code == 409
        assert c.post("/api/records", json={"name": "X", "email": "invalid"}).status_code == 400
        assert c.post("/api/records", json=[]).status_code == 400
        assert c.get("/api/stats").json["unique_records"] == 1
        rows = c.get("/api/records").json
        assert "TEST@example.com" not in str(rows)
        assert "***@" in rows[0]["email"]

def test_csv_analysis_and_similarity():
    with app.test_client() as c:
        content = b"name,email\nAlice,ALICE@example.com\nAlice A,alice@example.com\nBob,bob@example.com\nBad,nope\n"
        r = c.post("/api/analyze", data={"file": (io.BytesIO(content), "sample.csv")})
        assert r.status_code == 200
        assert r.json["unique"] == 2
        assert r.json["duplicate_count"] == 1
        assert r.json["invalid_rows"] == [5]
        assert c.post("/api/analyze", data={}).status_code == 400
        assert c.post("/api/similarity", json={"first": "Alice Smith", "second": "alice smith"}).json["possible_match"]
