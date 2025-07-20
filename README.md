Airport Baggage Tracking API
A simple FastAPI backend to track baggage scans across airport gates with time and location metadata.

🚀 Features
Log new baggage scans

Fetch all scans by Bag ID

Fetch all scans at a specific gate

View active bags scanned in recent time

Get unique bag counts per gate

🛠 Tech Stack
FastAPI – Web framework

SQLite – Lightweight DB

SQLAlchemy – ORM

📦 Run the Project
bash
Copy
Edit
pip install fastapi uvicorn sqlalchemy
uvicorn main:app --reload
🔗 Example Endpoints
POST /baggage/scan

GET /baggage/scans/bag/{bag_tag_id}

GET /baggage/scans/gate/{destination_gate}

GET /baggage/active/gate/{destination_gate}

GET /baggage/stats/gate-counts/since_minutes?since_minutes=60
