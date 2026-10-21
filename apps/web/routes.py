"""
Browser page routes: login, register, dashboard, reading detail, PDF export.
Served as HTML via Jinja2 templates, using cookie-based auth.
"""

import os
import json
from fastapi import (
    APIRouter,
    Request,
    Depends,
    Form,
    HTTPException,
)
from fastapi.responses import HTMLResponse, RedirectResponse, StreamingResponse
from fastapi.templating import Jinja2Templates

from apps.api.auth.security import hash_password, verify_password, create_access_token
from apps.web.web_auth import get_current_user_from_cookie
from apps.models.db_models import SessionLocal, User, Machine, SensorReading, Prediction
from apps.web.pdf_generator import generate_pdf_report
from apps.explainability.llm_reformulator import reformulate_diagnosis, generate_full_report_narrative
from apps.storage.report_storage import ReportStorage
from apps.models.db_models import Report
from apps.config import CONFIDENCE_ALERT_THRESHOLD
from io import BytesIO
 
router = APIRouter(tags=["web"])

TEMPLATES_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "templates")
templates = Jinja2Templates(directory=TEMPLATES_DIR)

def _parse_root_causes(recommendation_str):
    if not recommendation_str:
        return []

    try:
        return json.loads(recommendation_str)

    except (json.JSONDecodeError, TypeError):
        return []
# ============================================================
# ROLE-BASED ACCESS CONTROL
# ============================================================

def require_role(*allowed_roles):
    def dependency(
        user=Depends(get_current_user_from_cookie)
    ):
        if user.role not in allowed_roles:
            raise HTTPException(
                status_code=403,
                detail="You do not have permission to access this page.",
            )
        return user

    return dependency


require_administrator = require_role("administrator")

require_operational_user = require_role(
    "administrator",
    "engineer",
    "technician",
)

# ---------------------------------------------------------------------
# Login
# ---------------------------------------------------------------------

@router.get("/login", response_class=HTMLResponse)
def login_page(request: Request):
    return templates.TemplateResponse("login.html", {"request": request, "error": None})


@router.post("/login")
def login_submit(email: str = Form(...), password: str = Form(...)):
    session = SessionLocal()
    try:
        user = session.query(User).filter(User.email == email).first()
        if not user or not verify_password(password, user.hashed_password):
            return RedirectResponse(url="/login?error=1", status_code=303)
        if not user.active:
            return RedirectResponse(url="/login?error=disabled", status_code=303)

        token = create_access_token(data={"sub": user.email})
        response = RedirectResponse(url="/dashboard", status_code=303)
        response.set_cookie(key="access_token", value=token, httponly=True, max_age=3600)
        return response
    finally:
        session.close()


# ---------------------------------------------------------------------
# Register
# ---------------------------------------------------------------------

@router.get("/register", response_class=HTMLResponse)
def register_page(request: Request):
    return templates.TemplateResponse("register.html", {"request": request, "error": None})

@router.post("/register")
def register_submit(
    email: str = Form(...),
    password: str = Form(...),
):
    session = SessionLocal()

    try:
        existing = (
            session.query(User)
            .filter(User.email == email)
            .first()
        )

        if existing:
            return RedirectResponse(
                url="/register?error=1",
                status_code=303,
            )

        # First account becomes the administrator.
        # All later accounts created through public
        # registration are technicians.
        is_first_user = (
            session.query(User).count() == 0
        )

        new_user = User(
            email=email,
            hashed_password=hash_password(password),
            role=(
                "administrator"
                if is_first_user
                else "technician"
            ),
            active=True,
        )

        session.add(new_user)
        session.commit()

        return RedirectResponse(
            url="/login",
            status_code=303,
        )

    finally:
        session.close()

# ---------------------------------------------------------------------
# Logout
# ---------------------------------------------------------------------

@router.get("/logout")
def logout():
    response = RedirectResponse(url="/login", status_code=303)
    response.delete_cookie("access_token")
    return response


# ---------------------------------------------------------------------
# Dashboard
# ---------------------------------------------------------------------

@router.get("/dashboard", response_class=HTMLResponse)
def dashboard(request: Request, user=Depends(require_operational_user)):
    session = SessionLocal()
    try:
        results = (
            session.query(Prediction, SensorReading, Machine)
            .join(SensorReading, Prediction.reading_id == SensorReading.id)
            .join(Machine, SensorReading.machine_id == Machine.id)
            .order_by(Prediction.created_at.desc())
            .limit(50)
            .all()
        )
        readings = [
            {
                "prediction_id": pred.id,
                "reading_id": reading.id,
                "machine_code": machine.machine_code,
                "machine_name": machine.name,
                "predicted_class": pred.predicted_class,
                "confidence": pred.confidence,
                "created_at": pred.created_at,
                "is_normal": pred.predicted_class == "normal",
            }
            for pred, reading, machine in results
        ]
        machines = sorted(set(r["machine_name"] for r in readings))
        return templates.TemplateResponse(
            "dashboard.html",
            {"request": request, "user": user, "readings": readings, "machines": machines}
        )
    finally:
        session.close()


# ---------------------------------------------------------------------
# Reading detail (full diagnostic report)
# ---------------------------------------------------------------------

@router.get("/reading/{prediction_id}", response_class=HTMLResponse)
def reading_detail(
    prediction_id: int,
    request: Request,
    user=Depends(require_operational_user),
):
    session = SessionLocal()
    try:
        prediction = session.query(Prediction).filter(Prediction.id == prediction_id).first()
        if not prediction:
            return HTMLResponse("Reading not found", status_code=404)
        reading = session.query(SensorReading).filter(SensorReading.id == prediction.reading_id).first()
        machine = session.query(Machine).filter(Machine.id == reading.machine_id).first()

        root_causes = _parse_root_causes(prediction.recommendation)

        diagnosis_for_llm = {
            "predicted_class": prediction.predicted_class,
            "confidence": prediction.confidence,
            "top_features": prediction.top_features or [],
            "root_causes": root_causes,
        }
        natural_summary = reformulate_diagnosis(diagnosis_for_llm)

        return templates.TemplateResponse(
            "reading_detail.html",
            {
                "request": request,
                "user": user,
                "reading": reading,
                "machine": machine,
                "prediction": prediction,
                "root_causes": root_causes,
                "natural_summary": natural_summary,
            }
        )
    finally:
        session.close()


# ---------------------------------------------------------------------
# PDF download
# ---------------------------------------------------------------------


@router.get("/reading/{prediction_id}/pdf")
def reading_pdf(
    prediction_id: int,
    user=Depends(require_operational_user),
):
    session = SessionLocal()
    try:
        prediction = session.query(Prediction).filter(Prediction.id == prediction_id).first()
        if not prediction:
            return HTMLResponse("Reading not found", status_code=404)
        reading = session.query(SensorReading).filter(SensorReading.id == prediction.reading_id).first()
        machine = session.query(Machine).filter(Machine.id == reading.machine_id).first()

        root_causes = _parse_root_causes(prediction.recommendation)
        diagnosis_for_llm = {
            "predicted_class": prediction.predicted_class,
            "confidence": prediction.confidence,
            "top_features": prediction.top_features or [],
            "root_causes": root_causes,
        }
        narrative = generate_full_report_narrative(diagnosis_for_llm)

        buffer = generate_pdf_report(reading, prediction, machine, root_causes, narrative)
        pdf_bytes = buffer.getvalue()

        # save to disk, record it in the database
        relative_path = ReportStorage.save(pdf_bytes, machine.machine_code, reading.id)

        existing_report = session.query(Report).filter(Report.prediction_id == prediction.id).first()
        if not existing_report:
            report = Report(
                prediction_id=prediction.id,
                machine_id=machine.id,
                file_path=relative_path,
                generated_by=user.id,
                email_status='not_sent',
            )
            session.add(report)
            session.commit()

        buffer.seek(0)
        filename = f"diagnostic_report_{machine.machine_code}_{prediction.id}.pdf"
        return StreamingResponse(
            buffer,
            media_type="application/pdf",
            headers={"Content-Disposition": f"attachment; filename={filename}"}
        )
    finally:
        session.close()
        
    
    
# ---------------------------------------------------------------------
# History
# ---------------------------------------------------------------------
  
@router.get("/reports", response_class=HTMLResponse)
def reports_history(
    request: Request,
    user=Depends(require_operational_user),
):
    session = SessionLocal()

    try:
        results = (
            session.query(Report, Prediction, Machine)
            .join(
                Prediction,
                Report.prediction_id == Prediction.id
            )
            .join(
                Machine,
                Report.machine_id == Machine.id
            )
            .order_by(
                Report.created_at.desc()
            )
            .limit(100)
            .all()
        )

        reports = []

        for report, prediction, machine in results:

            predicted_class = (
                prediction.predicted_class or ""
            ).strip().lower()

            confidence = float(
                prediction.confidence or 0.0
            )

            # IMPORTANT:
            # Diagnosis type determines fault vs normal.
            # Confidence determines priority.
            if predicted_class == "normal":
                severity = "normal"

            elif confidence >= CONFIDENCE_ALERT_THRESHOLD:
                severity = "fault"

            else:
                severity = "warning"

            reports.append({
                "report_id": report.id,
                "prediction_id": prediction.id,
                "machine_code": machine.machine_code,
                "machine_name": machine.name,
                "predicted_class": prediction.predicted_class,
                "confidence": confidence,
                "severity": severity,
                "email_status": report.email_status,
                "created_at": report.created_at,
            })

        return templates.TemplateResponse(
            "reports_history.html",
            {
                "request": request,
                "user": user,
                "reports": reports,
            },
        )

    finally:
        session.close()


@router.get("/reports/{report_id}/download")
def download_stored_report(
    report_id: int,
    user=Depends(require_operational_user),
):
    session = SessionLocal()
    try:
        report = session.query(Report).filter(Report.id == report_id).first()
        if not report or not ReportStorage.exists(report.file_path):
            return HTMLResponse("Report not found", status_code=404)
        pdf_bytes = ReportStorage.read(report.file_path)
        return StreamingResponse(
            BytesIO(pdf_bytes),
            media_type="application/pdf",
            headers={"Content-Disposition": f"attachment; filename=report_{report_id}.pdf"}
        )
    finally:
        session.close()
        
# ---------------------------------------------------------------------
# Administrator — User Management
# ---------------------------------------------------------------------

@router.get(
    "/admin/users",
    response_class=HTMLResponse,
)
def admin_users(
    request: Request,
    user=Depends(require_administrator),
):
    session = SessionLocal()

    try:
        accounts = (
            session.query(User)
            .order_by(User.created_at.desc())
            .all()
        )

        return templates.TemplateResponse(
            "admin_users.html",
            {
                "request": request,
                "user": user,
                "accounts": accounts,
            },
        )

    finally:
        session.close()


@router.post("/admin/users/create")
def admin_create_user(
    email: str = Form(...),
    password: str = Form(...),
    role: str = Form(...),
    user=Depends(require_administrator),
):
    allowed_roles = {
        "administrator",
        "engineer",
        "technician",
    }

    if role not in allowed_roles:
        raise HTTPException(
            status_code=400,
            detail="Invalid role.",
        )

    session = SessionLocal()

    try:
        existing = (
            session.query(User)
            .filter(User.email == email)
            .first()
        )

        if existing:
            return RedirectResponse(
                url="/admin/users?error=exists",
                status_code=303,
            )

        new_user = User(
            email=email,
            hashed_password=hash_password(password),
            role=role,
            active=True,
        )

        session.add(new_user)
        session.commit()

        return RedirectResponse(
            url="/admin/users",
            status_code=303,
        )

    finally:
        session.close()


@router.post("/admin/users/{user_id}/role")
def admin_change_role(
    user_id: int,
    role: str = Form(...),
    user=Depends(require_administrator),
):
    allowed_roles = {
        "administrator",
        "engineer",
        "technician",
    }

    if role not in allowed_roles:
        raise HTTPException(
            status_code=400,
            detail="Invalid role.",
        )

    session = SessionLocal()

    try:
        account = (
            session.query(User)
            .filter(User.id == user_id)
            .first()
        )

        if not account:
            raise HTTPException(
                status_code=404,
                detail="User not found.",
            )

        account.role = role
        session.commit()

        return RedirectResponse(
            url="/admin/users",
            status_code=303,
        )

    finally:
        session.close()


@router.post("/admin/users/{user_id}/toggle")
def admin_toggle_user(
    user_id: int,
    user=Depends(require_administrator),
):
    session = SessionLocal()

    try:
        account = (
            session.query(User)
            .filter(User.id == user_id)
            .first()
        )

        if not account:
            raise HTTPException(
                status_code=404,
                detail="User not found.",
            )

        if account.id == user.id:
            raise HTTPException(
                status_code=400,
                detail="You cannot disable your own account.",
            )

        account.active = not account.active
        session.commit()

        return RedirectResponse(
            url="/admin/users",
            status_code=303,
        )

    finally:
        session.close()
        
# ---------------------------------------------------------------------
# Settings
# ---------------------------------------------------------------------

@router.get("/settings", response_class=HTMLResponse)
def settings_page(
    request: Request,
    user=Depends(require_operational_user),
):
    return templates.TemplateResponse(
        "settings.html",
        {
            "request": request,
            "user": user,
        },
    )


# ---------------------------------------------------------------------
# Help & Support
# ---------------------------------------------------------------------

@router.get("/help", response_class=HTMLResponse)
def help_page(
    request: Request,
    user=Depends(require_operational_user),
):
    return templates.TemplateResponse(
        "help.html",
        {
            "request": request,
            "user": user,
        },
    )