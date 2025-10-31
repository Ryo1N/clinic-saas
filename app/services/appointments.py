from __future__ import annotations

from datetime import datetime, timezone
from typing import List, Optional, Union, Any, Dict

from fastapi import HTTPException
from sqlmodel import select

from app.model import Appointment, DailyAvailability, Doctor
from app.schemas import AppointmentCreate, AppointmentRead, AppointmentStatusUpdate


def _to_utc_naive(dt: datetime) -> datetime:
    """Normalize to UTC-naive (tzinfo=None) for consistent storage and comparison."""
    if dt.tzinfo is None:
        return dt.replace(tzinfo=None)
    return dt.astimezone(timezone.utc).replace(tzinfo=None)


def _get_single_doctor_id(session) -> str:
    doc = session.exec(select(Doctor)).first()
    if not doc:
        raise HTTPException(500, "Doctor not initialized")
    return doc.id


def create_appointment(session, payload: AppointmentCreate) -> AppointmentRead:
    """
    Public: create an appointment if:
      - inside an active availability window
      - no conflicting 'scheduled' appointment exists
    All datetimes are stored as UTC-naive.
    """
    start_at = _to_utc_naive(payload.start_at)
    end_at = _to_utc_naive(payload.end_at)

    if end_at <= start_at:
        raise HTTPException(status_code=400, detail="end_at must be after start_at")

    doctor_id = _get_single_doctor_id(session)

    # Availability containment
    av = session.exec(
        select(DailyAvailability).where(
            DailyAvailability.doctor_id == doctor_id,
            DailyAvailability.is_active == True,  # noqa: E712
            DailyAvailability.start_at <= start_at,
            DailyAvailability.end_at >= end_at,
        )
    ).first()
    if not av:
        raise HTTPException(status_code=400, detail="Slot outside of availability")

    # Conflict with scheduled appointment
    conflict = session.exec(
        select(Appointment).where(
            Appointment.doctor_id == doctor_id,
            Appointment.status == "scheduled",
            Appointment.start_at < end_at,
            Appointment.end_at > start_at,
        )
    ).first()
    if conflict:
        raise HTTPException(status_code=409, detail="Slot already booked")

    appt = Appointment(
        doctor_id=doctor_id,
        start_at=start_at,
        end_at=end_at,
        patient_name=payload.patient_name,
        note=getattr(payload, "note", None),
        status="scheduled",
    )
    session.add(appt)
    session.commit()
    session.refresh(appt)
    return appt


def list_appointments(session, status: Optional[str] = None) -> List[AppointmentRead]:
    """Doctor: list appointments; if status specified (except 'all'), filter by it."""
    doctor_id = _get_single_doctor_id(session)
    q = select(Appointment).where(Appointment.doctor_id == doctor_id)
    if status and status != "all":
        q = q.where(Appointment.status == status)
    rows = session.exec(q.order_by(Appointment.start_at)).all()
    return rows


def update_status(session, appointment_id: str, status: Union[str, AppointmentStatusUpdate, Dict[str, Any]]) -> AppointmentRead:
    """
    Doctor: update appointment status.
    - Accepts str / Pydantic model / dict
    - Allowed: scheduled / completed / no_show / canceled
    - Only 'scheduled' blocks slots; other statuses reopen the time band
    """
    if isinstance(status, AppointmentStatusUpdate):
        new_status = status.status
    elif isinstance(status, dict):
        new_status = status.get("status")
    else:
        new_status = status

    if not isinstance(new_status, str):
        raise HTTPException(status_code=422, detail="Invalid status payload")

    allowed = {"scheduled", "completed", "no_show", "canceled"}
    if new_status not in allowed:
        raise HTTPException(status_code=422, detail="Invalid status")

    appt = session.get(Appointment, appointment_id)
    if not appt:
        raise HTTPException(status_code=404, detail="Appointment not found")

    appt.status = new_status
    session.add(appt)
    session.commit()
    session.refresh(appt)
    return appt
