import os
import uuid
import pandas as pd
import joblib
from fastapi import FastAPI, HTTPException
from google.cloud import bigquery
from vertexai.generative_models import GenerativeModel
from app.schemas import Reading, PredictionOut

# ========== CONFIGURATION ==========
MODEL_PATH = os.getenv("MODEL_PATH", "models/waterleak_best.pkl")
PROJECT_ID = os.getenv("GCP_PROJECT")
BQ_TABLE = f"{PROJECT_ID}.leakguard_db.predictions"

# Load model
model = joblib.load(MODEL_PATH)

# Initialize BigQuery client
bq_client = bigquery.Client()

# Initialize Gemini Agent Model
gemini_model = GenerativeModel(
    model_name="gemini-2.0-flash-001",
    tools=[]
)

# ========== FASTAPI APP ==========
app = FastAPI(title="LeakGuard Water Leakage Detection API")

def risk_from_prob(p):
    if p < 0.25: return "low"
    if p < 0.5: return "medium"
    if p < 0.75: return "high"
    return "critical"

def log_prediction_to_bq(payload, leakage_flag, leakage_prob, risk):
    try:
        payload_dict = payload.dict()
        row = {
            **payload_dict,
            "timestamp": bigquery.Timestamp.from_json(pd.Timestamp.utcnow().isoformat()),
            "leakage_flag": leakage_flag,
            "leakage_prob": leakage_prob,
            "risk_level": risk,
            "request_id": str(uuid.uuid4())
        }
        bq_client.insert_rows_json(BQ_TABLE, [row])
    except Exception as e:
        print("BQ logging failed:", str(e))

@app.get("/")
def root():
    return {"status": "ok", "message": "LeakGuard API running"}

# ========== PREDICT ENDPOINT ==========
@app.post("/predict", response_model=PredictionOut)
def predict(reading: Reading):
    try:
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

from vertexai.generative_models import GenerativeModel, Tool
import requests

def predict_tool(parameters: dict):
    try:
        r = requests.post(
            os.getenv("PREDICT_URL"),
            json=parameters,
            timeout=10
        )
        return r.json()
    except Exception as e:
        return {"error": str(e)}

tools = [
    Tool(
        function=predict_tool,
        name="predict_leak",
        description="Predicts leakage using pressure, temperature, flow rate etc."
    )
]

gemini_model = GenerativeModel(
    model_name="gemini-2.0-flash-001",
    tools=tools
)

SYSTEM_PROMPT = """
You are LeakGuard AI Agent. Your role: detect water leakage risk.

If user gives device inputs (pressure, flow, temperature, vibration, rpm,
op hours, latitude, longitude, zone, block, pipe, location_code):
- Identify missing values
- Call the predict_leak tool with correct keys
- DO NOT explain pipeline theory unless asked
"""

@app.post("/agent")
async def agent_endpoint(payload: dict):
    user_query = payload.get("query", "")
    try:
        response = gemini_model.generate_content(
            [SYSTEM_PROMPT, user_query]
        )
        return {"response": response.text}
    except Exception as e:
        return {"error": str(e)}
