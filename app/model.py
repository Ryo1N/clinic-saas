from datetime import datetime, timezone
from typing import Optional
from sqlmodel import SQLModel, Field

def _uuid() -> str:
    import uuid as _u
    return str(_u.uuid4())

def _utcnow_naive() -> datetime:
    """Return current UTC as naive datetime (tzinfo=None) for consistent storage."""
    return datetime.now(timezone.utc).replace(tzinfo=None)

class Doctor(SQLModel, table=True):
    """Single-doctor assumption for MVP."""
    id: str = Field(default_factory=_uuid, primary_key=True)
    name: str
    timezone: str = "Asia/Kolkata"       # Display hint only; comparisons use UTC
    booking_slot_minutes: int = 30

class DailyAvailability(SQLModel, table=True):
    """Active availability range (stored as UTC-naive)."""
    id: str = Field(default_factory=_uuid, primary_key=True)
    doctor_id: str = Field(foreign_key="doctor.id")
    start_at: datetime   # stored as UTC-naive
    end_at: datetime     # stored as UTC-naive
    is_active: bool = True

class Appointment(SQLModel, table=True):
    """Appointments; only 'scheduled' blocks new bookings."""
    id: str = Field(default_factory=_uuid, primary_key=True)
    doctor_id: str = Field(foreign_key="doctor.id")
    start_at: datetime   # stored as UTC-naive
    end_at: datetime     # stored as UTC-naive
    patient_name: str
    note: Optional[str] = None
    status: str = "scheduled"
    created_at: datetime = Field(default_factory=_utcnow_naive)
    updated_at: datetime = Field(default_factory=_utcnow_naive)
