from pydantic import BaseModel
from typing import Literal

class Reading(BaseModel):
    Pressure: float
    Flow_Rate: float
    Temperature: float
    Vibration: float
    RPM: float
    Operational_Hours: float
    Latitude: float
    Longitude: float
    Zone: str
    Block: str
    Pipe: str
    Location_Code: str

class PredictionOut(BaseModel):
    leakage_flag: int
    leakage_prob: float
    risk_level: Literal["low", "medium", "high", "critical"]