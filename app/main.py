import os
import uuid
import pandas as pd
import joblib
import requests
from fastapi import FastAPI, HTTPException
from google.cloud import bigquery
from vertexai.generative_models import GenerativeModel, Tool
from app.schemas import Reading, PredictionOut

# ENV CONFIG
MODEL_PATH = os.getenv("MODEL_PATH", "models/waterleak_best.pkl")
PROJECT_ID = os.getenv("GCP_PROJECT")
PREDICT_URL = os.getenv("PREDICT_URL")
BQ_TABLE = f"{PROJECT_ID}.leakguard_db.predictions"

# Load ML Model
model = joblib.load(MODEL_PATH)

# BigQuery client
bq_client = bigquery.Client()

# ---- AI Tools ----
def predict_tool(parameters: dict):
    try:
        r = requests.post(PREDICT_URL, json=parameters, timeout=10)
        return r.json()
    except Exception as e:
        return {"error": str(e)}

tools = [
    Tool(
        function=predict_tool,
        name="predict_leak",
        description="Predict leakage probability based on sensor inputs"
    )
]

# Gemini Model — SINGLE Initialization
gemini_model = GenerativeModel(
    model_name="gemini-2.0-flash-001",
    tools=tools
)

# FastAPI App
app = FastAPI(title="LeakGuard Water Leakage Detection API")

# Risk level mapping
def risk_from_prob(p):
    if p < 0.25: return "low"
    if p < 0.50: return "medium"
    if p < 0.75: return "high"
    return "critical"

# Log to BQ
def log_prediction_to_bq(payload, flag, prob, risk):
    try:
        row = payload.dict()
        row.update({
            "timestamp": pd.Timestamp.utcnow(),
            "leakage_flag": flag,
            "leakage_prob": prob,
            "risk_level": risk,
            "request_id": str(uuid.uuid4())
        })
        bq_client.insert_rows_json(BQ_TABLE, [row])
    except Exception as e:
        print("BQ logging failed:", e)

@app.get("/")
def health():
    return {"status": "ok", "message": "LeakGuard API running"}

@app.post("/predict", response_model=PredictionOut)
def predict(reading: Reading):
    try:
        data = [[
            reading.Pressure, reading.Flow_Rate, reading.Temperature,
            reading.Vibration, reading.RPM, reading.Operational_Hours,
            reading.Latitude, reading.Longitude, reading.Zone,
            reading.Block, reading.Pipe, reading.Location_Code,
        ]]
        proba = float(model.predict_proba(data)[0][1])
        flag = int(proba >= 0.5)
        risk = risk_from_prob(proba)

        log_prediction_to_bq(reading, flag, proba, risk)

        return PredictionOut(
            leakage_flag=flag,
            leakage_prob=proba,
            risk_level=risk
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

SYSTEM_PROMPT = """
You are LeakGuard AI Agent. Your role: detect water leakage risk.
If a query contains sensor values, extract them and call the predict_leak tool.
Return only prediction insights.
"""

@app.post("/agent")
async def agent_endpoint(payload: dict):
    try:
        user_query = payload.get("query", "")
        response = gemini_model.generate_content([SYSTEM_PROMPT, user_query])
        return {"response": response.text}
    except Exception as e:
        return {"error": str(e)}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=int(os.getenv("PORT", 8080)),
        workers=1
    )