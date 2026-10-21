"""
Real-time OPC-UA ingestion client.

Reads raw sensor values from the OPC-UA simulator,
buffers them into windows, extracts features, runs the
diagnostic engine, and saves readings + predictions to PostgreSQL.
"""

import asyncio
import sys
import os
import json
from datetime import datetime

import numpy as np
import pandas as pd
from asyncua import Client
from scipy.stats import skew, kurtosis


# ============================================================
# PROJECT ROOT
# ============================================================

current = os.path.dirname(os.path.abspath(__file__))

while (
    not os.path.exists(os.path.join(current, "apps"))
    and current != os.path.dirname(current)
):
    current = os.path.dirname(current)

if current not in sys.path:
    sys.path.append(current)


# ============================================================
# PROJECT IMPORTS
# ============================================================

from apps.models.db_models import (
    SessionLocal,
    Machine,
    SensorReading,
    Prediction,
    Report,
)

from apps.storage.report_storage import ReportStorage

from apps.models.predictor import FaultPredictor
from apps.pipeline.diagnostic_pipeline import DiagnosticEngine

from apps.services.email_service import (
    send_diagnostic_report,
)

from apps.config import (
    ALERT_RECIPIENT_EMAIL,
    CONFIDENCE_ALERT_THRESHOLD,
)

from apps.web.pdf_generator import (
    generate_pdf_report,
)


# ============================================================
# OPC-UA CONFIGURATION
# ============================================================

OPCUA_URL = (
    "opc.tcp://localhost:4840/freeopcua/server/"
)

NAMESPACE_URI = "http://jesa.plant"

CHANNEL_NAMES = [
    "tachometer",
    "underhang_axial",
    "underhang_radial",
    "underhang_tangential",
    "overhang_axial",
    "overhang_radial",
    "overhang_tangential",
    "microphone",
]

WINDOW_SIZE = 2048

MACHINE_NAMES = [
    "Machine1",
    "Machine2",
    "Machine3",
]


# ============================================================
# FEATURE CONFIGURATION
# ============================================================

STATS = [
    "max",
    "min",
    "mean",
    "sd",
    "rms",
    "skewness",
    "kurtosis",
    "crest",
    "form",
]

FEATURE_COLS = [
    f"{channel}_{stat}"
    for channel in CHANNEL_NAMES
    for stat in STATS
]


# ============================================================
# FEATURE EXTRACTION
# ============================================================

def extract_stats(signal):
    """
    Extract statistical features from one sensor signal.
    """

    rms = np.sqrt(
        np.mean(signal ** 2)
    )

    mean_abs = np.mean(
        np.abs(signal)
    )

    return {
        "max": np.max(signal),

        "min": np.min(signal),

        "mean": np.mean(signal),

        "sd": np.std(signal),

        "rms": rms,

        "skewness": skew(signal),

        "kurtosis": kurtosis(signal),

        "crest": (
            np.max(np.abs(signal)) / rms
            if rms != 0
            else 0.0
        ),

        "form": (
            rms / mean_abs
            if mean_abs != 0
            else 0.0
        ),
    }


def window_to_features(buffer):
    """
    Convert one 2048-sample window into the
    complete feature vector expected by the model.
    """

    features = {}

    for channel in CHANNEL_NAMES:

        signal = np.array(
            buffer[channel],
            dtype=float,
        )

        stats = extract_stats(
            signal
        )

        for stat_name, value in stats.items():

            features[
                f"{channel}_{stat_name}"
            ] = float(value)

    return features


# ============================================================
# MACHINE LOOKUP
# ============================================================

def get_machine(session, opcua_machine_name):
    """
    Resolve an OPC-UA machine name such as 'Machine1'
    to the corresponding Machine database object.
    """

    machine = (
        session.query(Machine)
        .filter(
            Machine.opcua_node == opcua_machine_name
        )
        .first()
    )

    if machine is None:

        raise ValueError(
            f"No machine found in the database "
            f"with opcua_node='{opcua_machine_name}'. "
            f"Run the seed script first."
        )

    return machine


# ============================================================
# SAVE DIAGNOSIS
# ============================================================

def save_diagnosis_to_db(
    opcua_machine_name,
    features,
    diagnosis,
):
    """
    Save the sensor reading and prediction using the
    new Machine foreign-key based schema.
    """

    session = SessionLocal()

    try:

        # ----------------------------------------------------
        # Resolve OPC-UA name -> Machine database object
        # ----------------------------------------------------

        machine = get_machine(
            session,
            opcua_machine_name,
        )

        machine_id = machine.id

        # ----------------------------------------------------
        # Sensor reading
        # ----------------------------------------------------

        reading = SensorReading(
            machine_id=machine_id,
            features=features,
            source="opcua_live_stream",
            ingestion_method="opcua",
        )

        session.add(reading)

        session.commit()

        session.refresh(reading)

        # ----------------------------------------------------
        # Prediction
        # ----------------------------------------------------

        prediction = Prediction(
            reading_id=reading.id,
            predicted_class=diagnosis["predicted_class"],
            confidence=diagnosis["confidence"],
            model_version="v1",
            top_features=diagnosis["top_features"],
            recommendation=json.dumps(
                diagnosis["root_causes"]
            ),
        )

        session.add(prediction)

        session.commit()

        session.refresh(prediction)

        # ----------------------------------------------------
        # Logging
        # ----------------------------------------------------

        print(
            f"[{datetime.now().strftime('%H:%M:%S')}] "
            f"Saved reading {reading.id} -> "
            f"{diagnosis['predicted_class']} "
            f"({diagnosis['confidence']:.1%}) | "
            f"Phenomenon: "
            f"{diagnosis['phenomenon']['phenomenon_id']}"
        )

        # ----------------------------------------------------
        # High-confidence fault alert
        # ----------------------------------------------------

        if (
            diagnosis["predicted_class"].lower() != "normal"
            and diagnosis["confidence"]
            >= CONFIDENCE_ALERT_THRESHOLD
        ):

            try:

                # ----------------------------------------------------
                # Generate PDF
                # ----------------------------------------------------

                pdf_buffer = generate_pdf_report(
                    reading,
                    prediction,
                    machine,
                    diagnosis["root_causes"],
                )

                pdf_bytes = pdf_buffer.getvalue()

                # ----------------------------------------------------
                # Permanently store PDF
                # ----------------------------------------------------

                relative_path = ReportStorage.save(
                    pdf_bytes,
                    machine.machine_code,
                    reading.id,
                )

                # ----------------------------------------------------
                # Create report record
                # ----------------------------------------------------

                report = Report(
                    prediction_id=prediction.id,
                    machine_id=machine.id,
                    file_path=relative_path,
                    generated_by=None,
                    email_status="not_sent",
                    email_recipient=ALERT_RECIPIENT_EMAIL,
                    version=1,
                )

                session.add(report)

                session.commit()

                session.refresh(report)

                # ----------------------------------------------------
                # Send email
                # ----------------------------------------------------

                result = send_diagnostic_report(
                    recipient=ALERT_RECIPIENT_EMAIL,
                    subject=(
                        "High-confidence fault detected — "
                        f"{opcua_machine_name}"
                    ),
                    message=(
                        "A high-confidence diagnosis was recorded "
                        f"for {opcua_machine_name}: "
                        f"<b>{diagnosis['predicted_class']}</b> "
                        f"({diagnosis['confidence']:.1%} confidence)."
                    ),
                    pdf_buffer=pdf_buffer,
                    filename=(
                        f"diagnostic_report_"
                        f"{machine.machine_code}_"
                        f"{reading.id}.pdf"
                    ),
                )

                # ----------------------------------------------------
                # Update report delivery status
                # ----------------------------------------------------

                if (
                    isinstance(result, dict)
                    and result.get("status")
                    == "saved_locally"
                ):

                    report.email_status = "failed"

                else:

                    report.email_status = "sent"

                session.commit()

                print(
                    f"[{datetime.now().strftime('%H:%M:%S')}] "
                    f"Report {report.id} stored — "
                    f"email status: {report.email_status}"
                )

            except Exception as e:

                # If report was already created, mark email/report
                # processing as failed rather than losing the record.

                try:

                    if (
                        "report" in locals()
                        and report.id
                    ):

                        report.email_status = "failed"

                        session.commit()

                except Exception:

                    session.rollback()

                print(
                    f"Email/report processing failed "
                    f"(non-critical): {e}"
                )

    finally:

        session.close()


# ============================================================
# MAIN
# ============================================================

async def main():

    # --------------------------------------------------------
    # Load model
    # --------------------------------------------------------

    predictor = FaultPredictor()

    # --------------------------------------------------------
    # Load processed dataset for SHAP background
    # --------------------------------------------------------

    data_path = os.path.join(
        current,
        "apps",
        "data",
        "processed",
        "mafaulda_features_final.csv",
    )

    df = pd.read_csv(
        data_path
    )

    feature_cols_for_bg = [
        column
        for column in df.columns
        if column not in [
            "fault_type",
            "file_id",
        ]
    ]

    background_raw = (
        df[feature_cols_for_bg]
        .sample(
            100,
            random_state=42,
        )
    )

    background = (
        predictor.scaler
        .transform(background_raw)
    )

    # --------------------------------------------------------
    # Diagnostic engine
    # --------------------------------------------------------

    engine = DiagnosticEngine(
        background_data=background,
        feature_cols=FEATURE_COLS,
    )

    # --------------------------------------------------------
    # Buffers
    # --------------------------------------------------------

    buffers = {
        machine: {
            channel: []
            for channel in CHANNEL_NAMES
        }
        for machine in MACHINE_NAMES
    }

    # --------------------------------------------------------
    # OPC-UA connection
    # --------------------------------------------------------

    async with Client(
        url=OPCUA_URL
    ) as client:

        print(
            "Connected to OPC-UA server"
        )

        idx = await client.get_namespace_index(
            NAMESPACE_URI
        )

        root = client.nodes.objects

        # ----------------------------------------------------
        # Locate machine OPC-UA objects
        # ----------------------------------------------------

        machine_objects = {}

        for machine_name in MACHINE_NAMES:

            machine_objects[machine_name] = (
                await root.get_child(
                    [
                        f"{idx}:{machine_name}"
                    ]
                )
            )

        # ----------------------------------------------------
        # Locate sensor nodes
        # ----------------------------------------------------

        machine_nodes = {}

        for machine_name in MACHINE_NAMES:

            machine_object = (
                machine_objects[machine_name]
            )

            machine_nodes[machine_name] = {}

            for channel in CHANNEL_NAMES:

                machine_nodes[
                    machine_name
                ][channel] = (
                    await machine_object.get_child(
                        [
                            f"{idx}:{channel}"
                        ]
                    )
                )

        print(
            "OPC-UA machine nodes resolved"
        )

        # ----------------------------------------------------
        # Main ingestion loop
        # ----------------------------------------------------

        while True:

            for machine_name in MACHINE_NAMES:

                # ------------------------------------------------
                # Read one sample from every channel
                # ------------------------------------------------

                for channel in CHANNEL_NAMES:

                    value = await machine_nodes[
                        machine_name
                    ][channel].read_value()

                    buffers[
                        machine_name
                    ][channel].append(
                        value
                    )

                # ------------------------------------------------
                # Full window available
                # ------------------------------------------------

                if (
                    len(
                        buffers[
                            machine_name
                        ][CHANNEL_NAMES[0]]
                    )
                    >= WINDOW_SIZE
                ):

                    # --------------------------------------------
                    # Feature extraction
                    # --------------------------------------------

                    features = window_to_features(
                        buffers[
                            machine_name
                        ]
                    )

                    # --------------------------------------------
                    # Diagnosis
                    # --------------------------------------------

                    diagnosis = engine.diagnose(
                        features
                    )

                    # --------------------------------------------
                    # Save everything
                    # --------------------------------------------

                    save_diagnosis_to_db(
                        machine_name,
                        features,
                        diagnosis,
                    )

                    # --------------------------------------------
                    # Reset window
                    # --------------------------------------------

                    buffers[machine_name] = {
                        channel: []
                        for channel in CHANNEL_NAMES
                    }

            # ----------------------------------------------------
            # Yield control
            # ----------------------------------------------------

            await asyncio.sleep(
                0.01
            )


# ============================================================
# ENTRY POINT
# ============================================================

if __name__ == "__main__":
    asyncio.run(main())