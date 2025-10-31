from datetime import datetime
from typing import Literal, Optional
from pydantic import BaseModel, Field, field_validator

# ---------- Availability ----------
class AvailabilityCreate(BaseModel):
    start_at: datetime = Field(description="ISO8601 (タイムゾーン付き推奨)")
    end_at: datetime   = Field(description="ISO8601 (タイムゾーン付き推奨)")
    is_active: bool = True

    @field_validator("end_at")
    @classmethod
    def _end_after_start(cls, v, info):
        start = info.data.get("start_at")
        if start is not None and v <= start:
            raise ValueError("end_at must be after start_at")
        return v

class AvailabilityRead(BaseModel):
    id: str
    start_at: datetime
    end_at: datetime
    is_active: bool

# ---------- Appointment (no email) ----------
class AppointmentCreate(BaseModel):
    start_at: datetime
    end_at: datetime
    patient_name: str
    note: Optional[str] = None

    @field_validator("end_at")
    @classmethod
    def _end_after_start(cls, v, info):
        start = info.data.get("start_at")
        if start is not None and v <= start:
            raise ValueError("end_at must be after start_at")
        return v

class AppointmentRead(BaseModel):
    id: str
    start_at: datetime
    end_at: datetime
    patient_name: str
    note: Optional[str] = None
    status: Literal["scheduled", "completed", "no_show", "canceled"]

class AppointmentStatusUpdate(BaseModel):
    status: Literal["completed", "no_show", "canceled"]

class SlotRead(BaseModel):
    start_at: datetime
    end_at: datetime