import os
import joblib
from fastapi import FastAPI
from app.schemas import Reading, PredictionOut

MODEL_PATH = os.getenv("MODEL_PATH", "models/waterleak_best.pkl")

model = joblib.load(MODEL_PATH)

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
def predict(reading: Reading):
    data = [[
        reading.Pressure,
        reading.Flow_Rate,
        reading.Temperature,
        reading.Vibration,
        reading.RPM,
        reading.Operational_Hours,
        reading.Latitude,
        reading.Longitude,
        reading.Zone,
        reading.Block,
        reading.Pipe,
        reading.Location_Code,
    ]]

    proba = model.predict_proba(data)[0][1]
    label = int(proba >= 0.5)
    return PredictionOut(
        leakage_flag=label,
        leakage_prob=float(proba),
        risk_level=risk_from_prob(proba),
    )