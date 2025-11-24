import os
import json
from datetime import datetime

import joblib
import pandas as pd
import requests
from fastapi import FastAPI, Request
from google.cloud import bigquery

from app.schemas import Reading, PredictionOut

import vertexai
from vertexai.generative_models import (
    GenerativeModel,
    FunctionDeclaration,
    Tool,
    ToolConfig,
)

# -------------------------------------------------------------------
# Config
# -------------------------------------------------------------------
MODEL_PATH = os.getenv("MODEL_PATH", "models/waterleak_best.pkl")
PROJECT_ID = os.getenv("GCP_PROJECT", "weighty-stacker-472817-j1")
VERTEX_REGION = os.getenv("VERTEX_REGION", "us-central1")
PREDICT_URL = os.getenv(
    "PREDICT_URL",
    "https://leakguard-api-217279920936.asia-south1.run.app/predict",
)

# -------------------------------------------------------------------
# Load ML model
# -------------------------------------------------------------------
model = joblib.load(MODEL_PATH)

# -------------------------------------------------------------------
# BigQuery client + table for logging
# -------------------------------------------------------------------
bq_client = bigquery.Client()
BQ_TABLE_ID = f"{PROJECT_ID}.leakguard_db.predictions"

# -------------------------------------------------------------------
# Vertex AI (Gemini) initialization
# -------------------------------------------------------------------
vertexai.init(project=PROJECT_ID, location=VERTEX_REGION)

# Tool 1: Predict leakage risk via Cloud Run
predict_leak_fn = FunctionDeclaration(
    name="predict_leak_risk",
    description=(
        "Call the LeakGuard Cloud Run API to predict leakage risk "
        "for a given sensor reading."
    ),
    parameters={
        "type": "object",
        "properties": {
            "Pressure": {"type": "number"},
            "Flow_Rate": {"type": "number"},
            "Temperature": {"type": "number"},
            "Vibration": {"type": "number"},
            "RPM": {"type": "number"},
            "Operational_Hours": {"type": "number"},
            "Latitude": {"type": "number"},
            "Longitude": {"type": "number"},
            "Zone": {"type": "string"},
            "Block": {"type": "string"},
            "Pipe": {"type": "string"},
            "Location_Code": {"type": "string"},
        },
        "required": [
            "Pressure",
            "Flow_Rate",
            "Temperature",
            "Vibration",
            "RPM",
            "Operational_Hours",
            "Latitude",
            "Longitude",
            "Zone",
            "Block",
            "Pipe",
            "Location_Code",
        ],
    },
)

# Tool 2: Summarize recent leakage stats from BigQuery
leak_stats_fn = FunctionDeclaration(
    name="summarize_recent_leakage",
    description=(
        "Summarize leakage statistics from the BigQuery predictions table "
        "for a recent time window."
    ),
    parameters={
        "type": "object",
        "properties": {
            "hours": {
                "type": "integer",
                "description": "Look back this many hours, e.g. 24.",
                "default": 24,
            },
        },
        "required": ["hours"],
    },
)

tools = [
    Tool(function_declarations=[predict_leak_fn, leak_stats_fn])
]

gemini_model = GenerativeModel(
    "gemini-1.5-flash",
    tools=tools,
)

# -------------------------------------------------------------------
# FastAPI app
# -------------------------------------------------------------------
app = FastAPI(title="LeakGuard Water Leakage Detection API with Agent")


def risk_from_prob(p: float) -> str:
    if p < 0.25:
        return "low"
    if p < 0.5:
        return "medium"
    if p < 0.75:
        return "high"
    return "critical"


@app.get("/")
def root():
    return {
        "status": "ok",
        "message": "LeakGuard API running (ML + Agentic AI)",
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
        "Location_Code": reading.Location_Code,
    }])

    proba = model.predict_proba(input_df)[0][1]
    label = int(proba >= 0.5)
    risk = risk_from_prob(proba)

    row = [{
        "timestamp": datetime.utcnow().isoformat(),
        **input_df.iloc[0].to_dict(),
        "leakage_flag": label,
        "leakage_prob": float(proba),
        "risk_level": risk,
        "request_id": request.headers.get("X-Cloud-Trace-Context", "local"),
    }]
    bq_client.insert_rows_json(BQ_TABLE_ID, row)

    return PredictionOut(
        leakage_flag=label,
        leakage_prob=float(proba),
        risk_level=risk,
    )


# -------------------------------------------------------------------
# Tool execution helpers for the Agent
# -------------------------------------------------------------------
def tool_predict_leak_risk(args: dict) -> dict:
    """Call our own Cloud Run /predict endpoint."""
    resp = requests.post(PREDICT_URL, json=args, timeout=10)
    resp.raise_for_status()
    return resp.json()


def tool_summarize_recent_leakage(args: dict) -> dict:
    """Run a BigQuery aggregation over recent predictions."""
    hours = int(args.get("hours", 24))
    query = f"""
        SELECT
          Zone,
          COUNT(*) AS total_events,
          SUM(CASE WHEN leakage_flag = 1 THEN 1 ELSE 0 END) AS leak_events,
          AVG(leakage_prob) AS avg_leakage_prob
        FROM `{BQ_TABLE_ID}`
        WHERE timestamp >= TIMESTAMP_SUB(CURRENT_TIMESTAMP(), INTERVAL {hours} HOUR)
        GROUP BY Zone
        ORDER BY leak_events DESC, avg_leakage_prob DESC
        LIMIT 10
    """
    job = bq_client.query(query)
    rows = list(job.result())
    zones = [
        {
            "Zone": r["Zone"],
            "total_events": int(r["total_events"]),
            "leak_events": int(r["leak_events"]),
            "avg_leakage_prob": float(r["avg_leakage_prob"]),
        }
        for r in rows
    ]
    return {
        "hours": hours,
        "top_zones": zones,
    }


# -------------------------------------------------------------------
# Agent endpoint
# -------------------------------------------------------------------
class AgentRequest(pd.io.json._json.loads.__class__):
    ...


@app.post("/agent")
async def agent_endpoint(payload: dict):
    """
    Body: { "query": "..." }

    Example queries:
    - "What are the top risky zones in last 24 hours?"
    - "Given this reading, is there a leak? { ... }"
    """
    user_query = payload.get("query", "")
    if not user_query:
        return {"answer": "Please provide a 'query' field in the JSON body."}

    # First call: let Gemini decide if it wants to call tools
    response = gemini_model.generate_content(
        [user_query],
        tool_config=ToolConfig(function_call="AUTO"),
    )

    candidate = response.candidates[0]
    answer_text_parts = []
    tool_call = None

    for part in candidate.content.parts:
        if hasattr(part, "function_call") and part.function_call:
            tool_call = part.function_call
        else:
            if getattr(part, "text", None):
                answer_text_parts.append(part.text)

    # If no tool call, just return the model's text answer
    if not tool_call:
        return {
            "answer": " ".join(answer_text_parts).strip(),
            "used_tool": None,
        }

    # Execute tool call
    fn_name = tool_call.name
    fn_args = json.loads(tool_call.args) if isinstance(tool_call.args, str) else dict(tool_call.args)

    if fn_name == "predict_leak_risk":
        tool_result = tool_predict_leak_risk(fn_args)
    elif fn_name == "summarize_recent_leakage":
        tool_result = tool_summarize_recent_leakage(fn_args)
    else:
        tool_result = {"error": f"Unknown tool: {fn_name}"}

    # Second call: ask Gemini to explain the tool result to the user
    followup = gemini_model.generate_content(
        [
            user_query,
            f"Tool {fn_name} returned this JSON: {json.dumps(tool_result)}. "
            "Explain this clearly to a non-technical operator, and give a short action plan.",
        ]
    )

    final_text = followup.text

    return {
        "answer": final_text,
        "used_tool": fn_name,
        "tool_result": tool_result,
    }