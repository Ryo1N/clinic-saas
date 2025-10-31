# Clinic SaaS MVP

## Overview
A tiny, production-like full-stack MVP for a solo-doctor clinic:
- Doctor sets availability
- Public (no login) books/cancels appointments based on availability  
- Doctor tracks appointments and marks them as **completed / no_show / canceled**

Focus: clarity, correctness, and engineering judgment over polish.  
Tech: **FastAPI + SQLModel (SQLite), minimal HTML/JS (no bundler)**

---

## File Structure
```
clinic-saas/
├── app/
│   ├── main.py                    # FastAPI app entry (Routers mount, static serving)
│   ├── config.py                  # Settings (env / defaults)
│   ├── db.py                      # Engine/session, init_db()
│   ├── model.py                   # SQLModel entities (Doctor, DailyAvailability, Appointment, etc.)
│   ├── schemas.py                 # Pydantic models (request/response DTO)
│   ├── routers/
│   │   ├── public.py              # Public APIs (slots listing, appointment creation/cancel)
│   │   └── doctor.py              # Doctor APIs (auth via Basic, CRUD availability & status updates)
│   ├── services/
│   │   ├── appointments.py        # Business logic for appointments (UTC normalization, conflict check)
│   │   └── slots.py               # Free-slot generation (30-min grid, scheduled-only blocks)
│   └── web/                         # Static single-page UIs (no build step)
│       ├── index.html             # Public booking page
│       └── doctor.html            # Doctor console (Basic auth header required)
├── tests/
│   ├── conftest.py                # Test app+DB bootstrap (per-test DB reset)
│   ├── test_public_and_slots.py   # Happy-path + basic failures (double-booking / out-of-range)
│   ├── test_availability_rules.py # Overlap rejection, PUT constraints
│   └── test_doctor_appointments_filter.py # Status filters
├── pytest.ini                     # pythonpath, discovery, norecursedirs
├── .env.example                   # (optional) sample env
└── README.md
```

---

## Quick Start

### 1) Environment
```bash
# macOS/Linux (example with uv or venv)
uv venv .venv && source .venv/bin/activate
uv pip install -r requirements.txt  # or: pip install -r requirements.txt
```
> Dependencies: `fastapi`, `uvicorn`, `sqlmodel`, `pydantic`, `pydantic-settings`, `python-dotenv`, `httpx`, `pytest`

### 2) Configuration
Environment variables are loaded from .env automatically.
If no .env file is present, the app automatically falls back to default settings defined in app/config.py.

# .env example
- `BASIC_AUTH_USERNAME` (default: `doctor`)
- `BASIC_AUTH_PASSWORD` (default: `change-me`)
- `BOOKING_SLOT_MINUTES` (default: `30`)


### 3) Run the Server
```bash
uvicorn app.main:app --reload
# Server: http://127.0.0.1:8000
# UI:     /web/index.html  (public)
#         /web/doctor.html (doctor console, needs Basic Auth)
```

---

## API (Selected)

### Doctor (Basic Auth)
| Method | Endpoint | Description |
|--------|-----------|-------------|
| GET    | `/api/doctor/availability` | List availabilities |
| POST   | `/api/doctor/availability` | Create availability |
| PUT    | `/api/doctor/availability/{id}` | Update (protects overlap or reservation loss) |
| DELETE | `/api/doctor/availability/{id}` | Delete (only if safe) |
| GET    | `/api/doctor/appointments?status=\<scheduled\|completed\|no_show\|canceled\>` | Filter appointments |
| PATCH  | `/api/doctor/appointments/{id}` | Update status |

### Public (No Auth)
| Method | Endpoint | Description |
|--------|-----------|-------------|
| GET    | `/api/public/slots?from=<ISO>&to=<ISO>` | List free 30-min slots |
| POST   | `/api/public/appointments` | Book appointment |
| DELETE | `/api/public/appointments/{id}` | Cancel appointment |

> All API timestamps use **UTC (ISO8601)**.  
> UI handles local time display; API compares in UTC internally.

---

## cURL Samples

### Create availability (Doctor)
```bash
curl -u doctor:change-me -X POST http://127.0.0.1:8000/api/doctor/availability \
  -H "Content-Type: application/json" \
  -d '{"start_at":"2025-11-12T10:00:00Z","end_at":"2025-11-12T12:00:00Z","is_active":true}'
```

### List slots (Public)
```bash
curl "http://127.0.0.1:8000/api/public/slots?from=2025-11-12T00:00:00Z&to=2025-11-13T00:00:00Z"
```

### Book first slot (Public)
```bash
curl -X POST http://127.0.0.1:8000/api/public/appointments \
  -H "Content-Type: application/json" \
  -d '{"start_at":"2025-11-12T10:00:00Z","end_at":"2025-11-12T10:30:00Z","patient_name":"John Doe"}'
```

### Mark completed / cancel (Doctor)
```bash
curl -u doctor:change-me -X PATCH http://127.0.0.1:8000/api/doctor/appointments/<APPT_ID> \
  -H "Content-Type: application/json" -d '{"status":"completed"}'

curl -u doctor:change-me -X PATCH http://127.0.0.1:8000/api/doctor/appointments/<APPT_ID> \
  -H "Content-Type: application/json" -d '{"status":"canceled"}'
```

---

## Testing
```bash
pytest -q
# Example: 9 passed in 0.00s
```

### What tests cover
- **Happy path**: availability → slots → booking → status update  
- **Guards**: overlapping availability, out-of-range booking, double-booking, status filter, authentication, invalid update prevention
- **Invariants**: `canceled/completed/no_show` reopen slots automatically

## Test details (by file)
- **tests/test_availability_rules.py**: overlapping availability is rejected; updating availability cannot evict existing appointments  
- **tests/test_back_to_back_slots_are_distinct.py**: adjacent 30-minute slots (e.g., 10:00–10:30 and 10:30–11:00) are distinct and both bookable  
- **tests/test_cannot_create_past_availability.py**: creation of past availabilities is rejected  
- **tests/test_doctor_appointments_filter.py**: doctor appointment listing supports `scheduled / completed / no_show` filters  
- **tests/test_doctor_auth_required.py**: doctor endpoints require HTTP Basic Auth (401 on missing/wrong creds)  
- **tests/test_invalid_status_update_returns_422.py**: invalid status update (e.g., `"unknown_value"`) returns 422  
- **tests/test_public_and_slots.py**: happy path (availability → slots → booking → status update); double-booking and out-of-range booking are rejected; `canceled` re-opens the slot


> Tests automatically reset DB per case — fully isolated.

---

## Key Design Decisions

1. **Time normalization**  
   - All datetimes normalized to **UTC** before storage.  
   - Prevents timezone mismatches or daylight-saving bugs.

2. **Slot generation**  
   - 30-min grid.  
   - Only `scheduled` blocks availability (others reopen automatically).

3. **Doctor auth**  
   - Simple **HTTP Basic Auth** for MVP

4. **Maintainability first**  
   - Routers are thin; core logic is in `/services/`.
   - Encourages separation of concerns and easy testing.

---

## Limitations
- Single-doctor assumption (no multi-user scope)  
- No email/notification  
- SQLite locking (not production-safe for concurrent writes)  
- No recurring availability or exception dates  

---

## If Given More Time
- Doctors able to set recurring weekly availability along with exceptions
- Email notifications
- User database for patients
- OAuth doctor login
- Better and safer frontend with React & TailwindCSS (currently susceptible to XSS)
- Better slot granularity & UX (calendar picker)  

---

## How to Review
1. Open `/web/doctor.html` → create availability  
2. Open `/web/index.html` → confirm slots visible  
3. Book a slot → verify in doctor panel  
4. Cancel → slot reappears  
5. Run tests (`pytest -q`) → all pass  

---

_This MVP emphasizes clean, readable code and real-world maintainability practices for a minimal scheduling system._
