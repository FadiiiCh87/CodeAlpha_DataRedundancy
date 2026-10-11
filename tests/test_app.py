import sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from app import app,db,Record
def test_unique_and_duplicate():
 app.config['TESTING']=True
 with app.app_context():
  db.session.query(Record).delete();db.session.commit()
 with app.test_client() as c:
  assert c.post('/api/records',json={'name':'Test User','email':'TEST@example.com'}).status_code==201
  assert c.post('/api/records',json={'name':'Other','email':'test@example.com'}).status_code==409
  assert c.post('/api/records',json={'name':'X','email':'invalid'}).status_code==400
