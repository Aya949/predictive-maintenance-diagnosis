"""
History route — returns past predictions.
"""

from fastapi import APIRouter, Depends
from apps.api.auth.dependencies import get_current_user
from apps.models.db_models import SessionLocal, Prediction, SensorReading

router = APIRouter(tags=["history"])


@router.get("/history")
def get_history(machine_id: str = None, limit: int = 20, current_user=Depends(get_current_user)):
    session = SessionLocal()
    try:
        query = session.query(Prediction).join(SensorReading)
        if machine_id:
            query = query.filter(SensorReading.machine_id == machine_id)
        results = query.order_by(Prediction.created_at.desc()).limit(limit).all()

        return [
            {
                "id": r.id,
                "predicted_class": r.predicted_class,
                "confidence": r.confidence,
                "created_at": r.created_at,
            }
            for r in results
        ]
    finally:
        session.close()