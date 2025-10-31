from fastapi import APIRouter, Depends, HTTPException, status, Path
from fastapi.security import HTTPBasic, HTTPBasicCredentials
from sqlmodel import select
from datetime import datetime, timezone
from app.config import settings
from app.db import get_session
from app.model import Doctor, DailyAvailability, Appointment
from app.schemas import AvailabilityCreate, AvailabilityRead, AppointmentRead, AppointmentStatusUpdate

router = APIRouter()
security = HTTPBasic()

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def auth(credentials: HTTPBasicCredentials = Depends(security)) -> None:
    """
    Simple HTTP Basic Auth guard for doctor endpoints.
    """
    if not (
        credentials.username == settings.BASIC_AUTH_USERNAME
        and credentials.password == settings.BASIC_AUTH_PASSWORD
    ):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Unauthorized"
        )

def _to_utc_naive(dt: datetime) -> datetime:
    """
    Normalize datetimes to UTC (naive).
    Ensures consistent storage and comparison in the database.
    """
    if dt.tzinfo:
        return dt.astimezone(timezone.utc).replace(tzinfo=None)
    return dt.replace(tzinfo=None)

def _ensure_future_window(start: datetime, end: datetime):
    """
    Validate that the given time window is valid and in the future.
    """
    now = datetime.now(timezone.utc)
    if end <= start:
        raise HTTPException(422, detail="end_at must be after start_at")
    if start <= now:
        raise HTTPException(400, detail="Availability must start in the future")

def get_doctor_id(session) -> str:
    """
    Retrieve the single doctor record from DB.
    This system assumes a single doctor instance.
    """
    doc = session.exec(select(Doctor)).first()
    if not doc:
        raise HTTPException(500, "Doctor not initialized")
    return doc.id

# ---------------------------------------------------------------------------
# Routes: Availability management
# ---------------------------------------------------------------------------

@router.get("/availability", response_model=list[AvailabilityRead])
def list_availability(_: None = Depends(auth)):
    """
    List all availabilities for the doctor.
    (Filtering of expired ones is handled client-side)
    """
    with get_session() as session:
        doctor_id = get_doctor_id(session)
        rows = session.exec(
            select(DailyAvailability)
            .where(DailyAvailability.doctor_id == doctor_id)
            .order_by(DailyAvailability.start_at)
        ).all()
        return rows

@router.post("/availability", response_model=AvailabilityRead, status_code=201)
def create_availability(payload: AvailabilityCreate, _: None = Depends(auth)):
    """
    Create a new availability slot for the doctor.
    Rejects overlaps or past time windows.
    """
    _ensure_future_window(payload.start_at, payload.end_at)

    with get_session() as session:
        doctor_id = get_doctor_id(session)
        s = _to_utc_naive(payload.start_at)
        e = _to_utc_naive(payload.end_at)

        # Check for overlapping existing availabilities
        overlapping = session.exec(
            select(DailyAvailability)
            .where(DailyAvailability.doctor_id == doctor_id)
            .where(DailyAvailability.is_active == True)
            .where((DailyAvailability.start_at < e) & (DailyAvailability.end_at > s))
        ).first()
        if overlapping:
            raise HTTPException(400, "Availability overlaps with an existing schedule.")

        row = DailyAvailability(
            doctor_id=doctor_id,
            start_at=s,
            end_at=e,
            is_active=payload.is_active,
        )
        session.add(row)
        session.commit()
        session.refresh(row)
        return row

@router.put("/availability/{avail_id}", response_model=AvailabilityRead)
def update_availability(avail_id: str, payload: AvailabilityCreate, _: None = Depends(auth)):
    """
    Update an existing availability.
    - Cannot move into the past
    - Cannot overlap existing availabilities
    - Cannot shrink around existing appointments
    """
    _ensure_future_window(payload.start_at, payload.end_at)

    with get_session() as session:
        doctor_id = get_doctor_id(session)
        row = session.get(DailyAvailability, avail_id)
        if not row or row.doctor_id != doctor_id:
            raise HTTPException(404, "availability not found")

        s = _to_utc_naive(payload.start_at)
        e = _to_utc_naive(payload.end_at)

        overlapping = session.exec(
            select(DailyAvailability)
            .where(DailyAvailability.doctor_id == doctor_id)
            .where(DailyAvailability.is_active == True)
            .where(DailyAvailability.id != avail_id)
            .where((DailyAvailability.start_at < e) & (DailyAvailability.end_at > s))
        ).first()
        if overlapping:
            raise HTTPException(400, "Availability overlaps with an existing schedule.")

        # Ensure no existing appointment falls outside the new range
        bad_appt = session.exec(
            select(Appointment)
            .where(Appointment.doctor_id == doctor_id)
            .where(Appointment.status != "canceled")
            .where(Appointment.start_at < row.end_at)
            .where(Appointment.end_at > row.start_at)
            .where(~((Appointment.start_at >= s) & (Appointment.end_at <= e)))
        ).first()
        if bad_appt:
            raise HTTPException(400, "Existing appointments fall outside updated availability.")

        row.start_at = s
        row.end_at = e
        row.is_active = payload.is_active
        session.add(row)
        session.commit()
        session.refresh(row)
        return row

@router.delete("/availability/{avail_id}", status_code=204)
def delete_availability(avail_id: str = Path(...), _: None = Depends(auth)):
    """
    Delete a specific availability by ID.
    Ownership validation is enforced.
    """
    with get_session() as session:
        doctor_id = get_doctor_id(session)
        row = session.get(DailyAvailability, avail_id)
        if not row or row.doctor_id != doctor_id:
            raise HTTPException(404, "availability not found")
        session.delete(row)
        session.commit()
        return

# ---------------------------------------------------------------------------
# Routes: Appointment management
# ---------------------------------------------------------------------------

@router.get("/appointments", response_model=list[AppointmentRead])
def list_appointments(status: str = "all", _: None = Depends(auth)):
    """
    List appointments, optionally filtered by status.
    Status can be: all | scheduled | completed | no_show | canceled
    """
    allowed = {"all", "scheduled", "completed", "no_show", "canceled"}
    if status not in allowed:
        raise HTTPException(422, "Invalid status filter")

    with get_session() as session:
        doctor_id = get_doctor_id(session)
        stmt = select(Appointment).where(Appointment.doctor_id == doctor_id)
        if status != "all":
            stmt = stmt.where(Appointment.status == status)
        rows = session.exec(stmt.order_by(Appointment.start_at)).all()
        return rows

@router.patch("/appointments/{appt_id}", response_model=AppointmentRead)
def update_appointment_status_api(
    appt_id: str,
    payload: AppointmentStatusUpdate,
    _: None = Depends(auth)
):
    """
    Update appointment status (completed, no_show, canceled).
    """
    with get_session() as session:
        appt = session.get(Appointment, appt_id)
        if not appt:
            raise HTTPException(404, "Appointment not found")

        new_status = payload.status
        allowed = {"scheduled", "completed", "no_show", "canceled"}
        if new_status not in allowed:
            raise HTTPException(422, "Invalid status value")

        appt.status = new_status
        session.add(appt)
        session.commit()
        session.refresh(appt)
        return appt
