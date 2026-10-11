import hashlib, json, os, re
from datetime import datetime, timezone
from flask import Flask, jsonify, request, render_template
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.exc import IntegrityError
app=Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI']=os.getenv('DATABASE_URL','sqlite:///redundancy.db').replace('postgres://','postgresql://',1)
db=SQLAlchemy(app)
class Record(db.Model):
 id=db.Column(db.Integer,primary_key=True)
 name=db.Column(db.String(120),nullable=False)
 email=db.Column(db.String(254),nullable=False,unique=True)
 fingerprint=db.Column(db.String(64),nullable=False,unique=True)
 created_at=db.Column(db.DateTime,default=lambda:datetime.now(timezone.utc))
def normalize(data):
 name=' '.join(str(data.get('name','')).split()).strip()
 email=str(data.get('email','')).strip().lower()
 if not (2<=len(name)<=120 and re.fullmatch(r'[^\s@]+@[^\s@]+\.[^\s@]+',email)):
  raise ValueError('Valid name (2-120 characters) and email are required')
 return name,email
@app.get('/')
def home():return render_template('index.html')
@app.get('/health')
def health():return jsonify(status='ok')
@app.get('/api/records')
def list_records():return jsonify([{'id':r.id,'name':r.name,'email':r.email} for r in Record.query.order_by(Record.id.desc()).limit(100).all()])
@app.post('/api/records')
def create():
 data=request.get_json(silent=True) or {}
 try:name,email=normalize(data)
 except ValueError as e:return jsonify(status='invalid',error=str(e)),400
 fingerprint=hashlib.sha256(email.encode()).hexdigest()
 existing=Record.query.filter((Record.email==email)|(Record.fingerprint==fingerprint)).first()
 if existing:return jsonify(status='redundant',classification='duplicate',existing_id=existing.id),409
 try:
  row=Record(name=name,email=email,fingerprint=fingerprint);db.session.add(row);db.session.commit()
 except IntegrityError:
  db.session.rollback();return jsonify(status='redundant',classification='duplicate'),409
 return jsonify(status='unique_verified',id=row.id),201
with app.app_context():db.create_all()
if __name__=='__main__':app.run(debug=os.getenv('FLASK_DEBUG')=='1')
