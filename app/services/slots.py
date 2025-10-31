from __future__ import annotations

from datetime import datetime, timedelta, timezone
from typing import List

from sqlmodel import select
from app.model import DailyAvailability, Appointment
from app.schemas import SlotRead
from app.config import settings



def _to_utc_naive(dt: datetime) -> datetime:
    """
    Normalize a datetime object to UTC (naive).

    - If tzinfo is present, convert to UTC and strip tzinfo.
    - If tzinfo is absent, assume it is already UTC-naive and keep as-is.
    - Ensures consistent internal comparison across all modules.
    """
    if dt.tzinfo:
        # Convert aware datetime to UTC, then drop tzinfo
        return dt.astimezone(timezone.utc).replace(tzinfo=None)
    else:
        # Already naive (assumed UTC-based)
        return dt


def list_free_slots(session, window_start: datetime, window_end: datetime) -> List[SlotRead]:
    """
    Enumerate free slots within [window_start, window_end) on a grid of BOOKING_SLOT_MINUTES.
    - Only consider is_active=True availabilities that intersect the window
    - Block only 'scheduled' appointments
    - All comparisons are UTC-naive
    """
    ws = _to_utc_naive(window_start)
    we = _to_utc_naive(window_end)

    avails = session.exec(
        select(DailyAvailability).where(
            DailyAvailability.is_active == True,  # noqa: E712
            DailyAvailability.end_at >= ws,
            DailyAvailability.start_at <= we,
        )
    ).all()

    booked = session.exec(
        select(Appointment).where(
            Appointment.status == "scheduled",
            Appointment.start_at < we,
            Appointment.end_at > ws,
        )
    ).all()

    for appt in booked:
        appt.start_at = _to_utc_naive(appt.start_at)
        appt.end_at = _to_utc_naive(appt.end_at)

    slots: List[SlotRead] = []
    step = timedelta(minutes=settings.BOOKING_SLOT_MINUTES)

    now_naive = _to_utc_naive(datetime.now(timezone.utc)) 
    for av in avails:
        av_start = _to_utc_naive(av.start_at)
        av_end = _to_utc_naive(av.end_at)

        # Trim by window
        start = max(av_start, ws)
        end = min(av_end, we)

        slot_start = start
        while slot_start + step <= end:
            slot_end = slot_start + step

            #Do not return past slots
            if slot_start < now_naive:
                slot_start += step
                continue

            # Overlap with scheduled?
            overlap = False
            for appt in booked:
                if not (slot_end <= appt.start_at or slot_start >= appt.end_at):
                    overlap = True
                    break

            if not overlap:
                slots.append(SlotRead(start_at=slot_start, end_at=slot_end))

            slot_start += step

    return slots
