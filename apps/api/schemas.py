"""
Pydantic schemas — define the shape of API requests and responses.
"""

from pydantic import BaseModel, EmailStr
from typing import Dict, Any, List

class PredictionRequest(BaseModel):
    horizontal_rms: float
    vertical_rms: float
    temperature: float

class UserCreate(BaseModel):
    email: EmailStr
    password: str


class UserLogin(BaseModel):
    email: EmailStr
    password: str


class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"


class PredictRequest(BaseModel):
    machine_id: str
    features: Dict[str, float]  # e.g. {"tachometer_max": 4.82, ...}


class PredictResponse(BaseModel):
    predicted_class: str
    confidence: float
    top_features: List[Dict[str, Any]]
    phenomenon: Dict[str, Any]
    root_causes: List[Dict[str, Any]]