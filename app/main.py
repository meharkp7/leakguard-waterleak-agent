import os
import joblib
import pandas as pd
from fastapi import FastAPI, Request
from app.schemas import Reading, PredictionOut
from google.cloud import bigquery
from datetime import datetime

MODEL_PATH = os.getenv("MODEL_PATH", "models/waterleak_best.pkl")

model = joblib.load(MODEL_PATH)

client = bigquery.Client()
table_id = "weighty-stacker-472817-j1.leakguard_db.predictions"

app = FastAPI(title="LeakGuard Water Leakage Detection API")

def risk_from_prob(p):
    if p < 0.25: return "low"
    if p < 0.5: return "medium"
    if p < 0.75: return "high"
    return "critical"

@app.get("/")
def root():
    return {
        "status": "ok",
        "message": "LeakGuard API running"
    }

@app.post("/predict", response_model=PredictionOut)
def predict(request: Request, reading: Reading):

    input_df = pd.DataFrame([{
        "Pressure": reading.Pressure,
        "Flow_Rate": reading.Flow_Rate,
        "Temperature": reading.Temperature,
        "Vibration": reading.Vibration,
        "RPM": reading.RPM,
        "Operational_Hours": reading.Operational_Hours,
        "Latitude": reading.Latitude,
        "Longitude": reading.Longitude,
        "Zone": reading.Zone,
        "Block": reading.Block,
        "Pipe": reading.Pipe,
        "Location_Code": reading.Location_Code
    }])

    proba = model.predict_proba(input_df)[0][1]
    label = int(proba >= 0.5)
    risk = risk_from_prob(proba)

    # Logging to BigQuery
    row = [{
        "timestamp": datetime.utcnow().isoformat(),
        **input_df.iloc[0].to_dict(),
        "leakage_flag": label,
        "leakage_prob": float(proba),
        "risk_level": risk,
        "request_id": request.headers.get("X-Cloud-Trace-Context", "local")
    }]
    client.insert_rows_json(table_id, row)

    return PredictionOut(
        leakage_flag=label,
        leakage_prob=float(proba),
        risk_level=risk,
    )