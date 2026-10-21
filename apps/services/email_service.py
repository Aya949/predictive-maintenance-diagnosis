import base64
import os
import time
from pathlib import Path

import resend

_ALERTS_DIR = Path(__file__).resolve().parents[1] / "data" / "alerts"


def _is_transient_network_error(error: Exception) -> bool:
    message = str(error).lower()
    transient_markers = (
        "getaddrinfo failed",
        "name resolution",
        "failed to resolve",
        "max retries exceeded",
        "connection aborted",
        "connection reset",
        "timed out",
        "temporary failure",
        "network is unreachable",
    )
    return any(marker in message for marker in transient_markers)


def _save_pdf_fallback(pdf_buffer, filename: str) -> Path:
    _ALERTS_DIR.mkdir(parents=True, exist_ok=True)
    path = _ALERTS_DIR / filename
    pdf_buffer.seek(0)
    path.write_bytes(pdf_buffer.read())
    return path


def send_diagnostic_report(
    recipient: str,
    subject: str,
    message: str,
    pdf_buffer,
    filename: str = "machine_diagnostic_report.pdf",
    max_retries: int = 3,
):
    api_key = os.getenv("RESEND_API_KEY")

    if not api_key:
        raise RuntimeError("RESEND_API_KEY is missing.")

    resend.api_key = api_key

    pdf_buffer.seek(0)
    pdf_content = pdf_buffer.read()
    pdf_base64 = base64.b64encode(pdf_content).decode("utf-8")

    print(f"[EMAIL] Recipient: {recipient}")
    print(f"[EMAIL] PDF size: {len(pdf_content)} bytes")

    payload = {
        "from": "onboarding@resend.dev",
        "to": [recipient],
        "subject": subject,
        "html": f"""
        <h2>Maintenance Diagnostic Alert</h2>
        <p>{message}</p>
        <p>The complete diagnostic report is attached.</p>
        <p><strong>Predictive Maintenance Diagnostic System</strong></p>
        """,
        "attachments": [
            {
                "filename": filename,
                "content": pdf_base64,
            }
        ],
    }

    last_error = None
    for attempt in range(1, max_retries + 1):
        try:
            response = resend.Emails.send(payload)
            print(f"[EMAIL] Sent successfully (attempt {attempt})")
            print(f"[EMAIL] Resend response: {response}")
            return response
        except Exception as error:
            last_error = error
            if _is_transient_network_error(error) and attempt < max_retries:
                wait_seconds = 2 ** attempt
                print(
                    f"[EMAIL] Attempt {attempt} failed ({error}). "
                    f"Retrying in {wait_seconds}s..."
                )
                time.sleep(wait_seconds)
                continue
            break

    saved_path = _save_pdf_fallback(pdf_buffer, filename)
    print(f"[EMAIL] Send failed after {max_retries} attempt(s): {last_error}")
    print(f"[EMAIL] PDF saved locally: {saved_path}")

    return {
        "status": "saved_locally",
        "path": str(saved_path),
        "error": str(last_error),
    }
