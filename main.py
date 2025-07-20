from fastapi import FastAPI, HTTPException, Query
from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime, timedelta
from sqlalchemy import create_engine, Column, String, Integer, DateTime
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

# App and DB setup
app = FastAPI()
DATABASE_URL = "sqlite:///./baggage.db"
engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})
Base = declarative_base()
SessionLocal = sessionmaker(bind=engine)
db = SessionLocal()

# SQLAlchemy Model
class BagScan(Base):
    __tablename__ = "bag_scans"
    id = Column(Integer, primary_key=True, index=True)
    bag_tag_id = Column(String, index=True)
    destination_gate = Column(String)
    location_scanned = Column(String)
    timestamp = Column(DateTime, default=datetime.utcnow)

Base.metadata.create_all(bind=engine)

# Pydantic Models
class BagScanInput(BaseModel):
    bag_tag_id: str
    destination_gate: str
    location_scanned: str

class BagScanOutput(BaseModel):
    bag_tag_id: str
    destination_gate: str
    location_scanned: str
    timestamp: datetime

# 1. POST /baggage/scan
@app.post("/baggage/scan")
def scan_bag(data: BagScanInput):
    record = BagScan(
        bag_tag_id=data.bag_tag_id,
        destination_gate=data.destination_gate,
        location_scanned=data.location_scanned
    )
    db.add(record)
    db.commit()
    db.refresh(record)
    return {"scan_internal_id": record.id, "status": "logged"}

# 2. GET /baggage/scans/bag/{bag_tag_id}
@app.get("/baggage/scans/bag/{bag_tag_id}", response_model=List[BagScanOutput])
def get_bag_scans(bag_tag_id: str, latest: Optional[bool] = False):
    scans = db.query(BagScan).filter(BagScan.bag_tag_id == bag_tag_id).order_by(BagScan.timestamp.desc())
    if latest:
        scan = scans.first()
        if not scan:
            raise HTTPException(status_code=404, detail="No scans found")
        return [scan]
    return scans.all()

# 3. GET /baggage/scans/gate/{destination_gate}
@app.get("/baggage/scans/gate/{destination_gate}", response_model=List[BagScanOutput])
def get_scans_for_gate(destination_gate: str):
    scans = db.query(BagScan).filter(BagScan.destination_gate == destination_gate).order_by(BagScan.timestamp.desc())
    return scans.all()

# 4. GET /baggage/active/gate/{destination_gate}?since_minutes=N
@app.get("/baggage/active/gate/{destination_gate}")
def active_bags(destination_gate: str, since_minutes: int = 60):
    since_time = datetime.utcnow() - timedelta(minutes=since_minutes)
    scans = db.query(BagScan).filter(
        BagScan.destination_gate == destination_gate,
        BagScan.timestamp >= since_time
    ).order_by(BagScan.timestamp.desc()).all()

    seen = set()
    result = []
    for s in scans:
        if s.bag_tag_id not in seen:
            seen.add(s.bag_tag_id)
            result.append({
                "bag_tag_id": s.bag_tag_id,
                "last_scan_at": s.timestamp,
                "last_location": s.location_scanned
            })
    return result

# 5. GET /baggage/stats/gate-counts/since_minutes?since_minutes=60
@app.get("/baggage/stats/gate-counts/since_minutes")
def count_bags_by_gate(since_minutes: int = 60):
    since_time = datetime.utcnow() - timedelta(minutes=since_minutes)
    scans = db.query(BagScan).filter(BagScan.timestamp >= since_time).all()

    gate_counts = {}
    seen = set()

    for s in scans:
        key = (s.destination_gate, s.bag_tag_id)
        if key not in seen:
            seen.add(key)
            gate_counts[s.destination_gate] = gate_counts.get(s.destination_gate, 0) + 1

    return [{"destination_gate": g, "unique_bag_count": c} for g, c in gate_counts.items()]
