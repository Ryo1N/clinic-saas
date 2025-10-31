from sqlmodel import SQLModel, create_engine, Session, select
from app.model import Doctor
from app.config import settings

# SQLite (single file). For another RDB, replace the URL accordingly.
engine = create_engine("sqlite:///./app.db", connect_args={"check_same_thread": False})

def init_db() -> None:
    """Create tables and seed a single default Doctor if missing."""
    SQLModel.metadata.create_all(engine)
    with Session(engine) as session:
        doctor = session.exec(select(Doctor)).first()
        if not doctor:
            session.add(Doctor(
                name="Default Doctor",
                # Use model defaults for timezone; do not depend on removed DEFAULT_TZ
                booking_slot_minutes=settings.BOOKING_SLOT_MINUTES,
            ))
            session.commit()

def get_session() -> Session:
    """Session factory (caller is responsible for closing)."""
    return Session(engine)
