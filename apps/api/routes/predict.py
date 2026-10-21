"""
Prediction route — runs the full diagnostic engine on submitted sensor features.
"""

import os
import json
import pandas as pd

from fastapi import APIRouter

from apps.api.schemas import PredictRequest, PredictResponse
from apps.pipeline.diagnostic_pipeline import DiagnosticEngine
from apps.models.predictor import FaultPredictor
from apps.models.db_models import SessionLocal, SensorReading, Prediction
from apps.services.email_service import send_diagnostic_report
from apps.web.pdf_generator import generate_pdf_report


router = APIRouter(
    prefix="/predict",
    tags=["Prediction"]
)


# ----------------------------------------------------
# Load model and diagnostic engine ONCE at startup
# ----------------------------------------------------

_predictor = FaultPredictor()

_project_root = os.path.dirname(
    os.path.dirname(
        os.path.dirname(
            os.path.abspath(__file__)
        )
    )
)

_data_path = os.path.join(
    _project_root,
    "data",
    "processed",
    "mafaulda_features_final.csv"
)

_df = pd.read_csv(_data_path)

_feature_cols = [
    c for c in _df.columns
    if c not in ["fault_type", "file_id"]
]

_background_raw = _df[_feature_cols].sample(
    100,
    random_state=42
)

_background = _predictor.scaler.transform(
    _background_raw
)

_engine = DiagnosticEngine(
    background_data=_background,
    feature_cols=_feature_cols
)


# ----------------------------------------------------
# Email alert configuration
# ----------------------------------------------------

EMAIL_RECIPIENT = "aitallalaya2335@gmail.com"

# Only send an email when confidence is at least 95%
EMAIL_CONFIDENCE_THRESHOLD = 0.95


# ----------------------------------------------------
# Prediction Endpoint
# ----------------------------------------------------

@router.post(
    "/predict",
    response_model=PredictResponse
)
def predict(request: PredictRequest):

    # -----------------------------------------------
    # 1. Run diagnosis
    # -----------------------------------------------

    diagnosis = _engine.diagnose(request.features)

    session = SessionLocal()

    try:

        # -------------------------------------------
        # 2. Save sensor reading
        # -------------------------------------------

        reading = SensorReading(
            machine_id=request.machine_id,
            features=request.features,
            file_source="api_request"
        )

        session.add(reading)
        session.commit()
        session.refresh(reading)

        # -------------------------------------------
        # 3. Save prediction
        # -------------------------------------------

        prediction = Prediction(
            reading_id=reading.id,
            predicted_class=diagnosis["predicted_class"],
            confidence=diagnosis["confidence"],
            top_features=diagnosis["top_features"],
            recommendation=json.dumps(
                diagnosis["root_causes"]
            ),
        )

        session.add(prediction)
        session.commit()
        session.refresh(prediction)

        # -------------------------------------------
        # 4. Check whether an email alert is needed
        # -------------------------------------------

        is_not_normal = (
            diagnosis["predicted_class"].lower() != "normal"
        )

        is_high_confidence = (
            diagnosis["confidence"]
            >= EMAIL_CONFIDENCE_THRESHOLD
        )

        should_send_alert = (
            is_not_normal
            and is_high_confidence
        )
        print(
            f"[ALERT CHECK] "
            f"condition={diagnosis['predicted_class']} | "
            f"confidence={diagnosis['confidence']:.3f} | "
            f"not_normal={is_not_normal} | "
            f"high_confidence={is_high_confidence} | "
            f"send={should_send_alert}"
        )

        # -------------------------------------------
        # 5. Generate PDF + send email
        # -------------------------------------------

        if should_send_alert:

            print(
                f"⚠️ Important maintenance alert detected: "
                f"{diagnosis['predicted_class']} "
                f"({diagnosis['confidence']:.1%})"
            )
            print("[EMAIL] Generating diagnostic PDF...")
            
            print("[EMAIL] Sending diagnostic report...")
            # Generate PDF directly in memory
            pdf_buffer = generate_pdf_report(
                reading=reading,
                prediction=prediction,
                root_causes=diagnosis["root_causes"]
            )

            # Send PDF through Resend
            send_diagnostic_report(
                recipient=EMAIL_RECIPIENT,

                subject=(
                    f"Maintenance Alert — "
                    f"{diagnosis['predicted_class']}"
                ),

                message=(
                    f"Machine {request.machine_id} has been "
                    f"diagnosed with "
                    f"{diagnosis['predicted_class']} "
                    f"with {diagnosis['confidence']:.1%} "
                    f"confidence. "
                    f"A detailed diagnostic report is attached."
                ),

                pdf_buffer=pdf_buffer,

                filename=(
                    f"machine_{request.machine_id}"
                    f"_diagnostic_report.pdf"
                )
            )
            print("[EMAIL] Send function completed.")

        else:

            print(
                f"No email alert: "
                f"{diagnosis['predicted_class']} "
                f"({diagnosis['confidence']:.1%})"
            )

    finally:
        session.close()

    # -----------------------------------------------
    # 6. Return diagnosis to the API
    # -----------------------------------------------

    return diagnosis