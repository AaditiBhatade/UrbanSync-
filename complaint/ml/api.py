from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field
from typing import Optional
from ml.classifier import classifier_instance

router = APIRouter(prefix="/ml", tags=["Machine Learning"])

class PredictionRequest(BaseModel):
    title: str = Field(..., example="Water pipeline leakage")
    description: str = Field(..., example="Large amount of water leaking near main road")
    impact_level: Optional[str] = Field("MEDIUM", example="HIGH")

class PredictionResponse(BaseModel):
    category: str
    subcategory: str
    confidence: float
    department_code: str
    department_name: str
    priority: str
    status: str
    routing_reason: str

@router.post("/predict", response_model=PredictionResponse)
def predict_complaint(request: PredictionRequest):
    """
    Independent endpoint for ML categorization and routing
    """
    if not request.title and not request.description:
        raise HTTPException(status_code=400, detail="Title or description required")
    
    result = classifier_instance.predict(
        title=request.title,
        description=request.description,
        citizen_impact=request.impact_level or "MEDIUM"
    )
    return result
