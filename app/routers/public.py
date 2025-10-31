# app/routers/public.py
from datetime import datetime
from fastapi import APIRouter, Query, HTTPException
from app.db import get_session
from app.schemas import AppointmentCreate, AppointmentRead, SlotRead
from app.services.appointments import create_appointment
from app.services.slots import list_free_slots  # これが必要

router = APIRouter()

@router.get("/health")
def health():
    return {"ok": True}

@router.post("/appointments", response_model=AppointmentRead, status_code=201)
def create_appointment_api(payload: AppointmentCreate):
    with get_session() as session:
        appt = create_appointment(session, payload)
        return appt

# ★ これが必要です
@router.get("/slots", response_model=list[SlotRead])
def get_slots(
    from_: datetime = Query(..., alias="from"),
    to: datetime = Query(..., alias="to"),
):
    if to <= from_:
        raise HTTPException(status_code=422, detail="'to' must be after 'from'")
    with get_session() as session:
        return list_free_slots(session, from_, to)
