from datetime import datetime, timedelta, timezone
from conftest import iso

def test_doctor_appointments_status_filter(client, auth_header, tomorrow_10_to_noon):
    start, end = tomorrow_10_to_noon
    # Availability
    r = client.post("/api/doctor/availability", headers=auth_header, json={
        "start_at": start, "end_at": end, "is_active": True
    })
    assert r.status_code == 201
    base = datetime.fromisoformat(start.replace("Z","+00:00"))

    # Reserve 3 appointments
    times = [(0,"scheduled"), (30,"completed"), (60,"no_show")]
    ids = []
    for offset, st in times:
        s = iso(base + timedelta(minutes=offset))
        e = iso(base + timedelta(minutes=offset+30))
        rb = client.post("/api/public/appointments", json={
            "start_at": s, "end_at": e, "patient_name": f"P{offset}"
        })
        assert rb.status_code == 201, rb.text
        ids.append(rb.json()["id"])

    # Change 2 appointsments statuses
    client.patch(f"/api/doctor/appointments/{ids[1]}", headers=auth_header, json={"status":"completed"})
    client.patch(f"/api/doctor/appointments/{ids[2]}", headers=auth_header, json={"status":"no_show"})

    # Check filters
    r_all = client.get("/api/doctor/appointments", headers=auth_header)
    r_s   = client.get("/api/doctor/appointments?status=scheduled", headers=auth_header)
    r_c   = client.get("/api/doctor/appointments?status=completed", headers=auth_header)
    r_n   = client.get("/api/doctor/appointments?status=no_show", headers=auth_header)

    assert r_all.status_code == r_s.status_code == r_c.status_code == r_n.status_code == 200
    assert len(r_all.json()) >= 3
    assert all(a["status"]=="scheduled" for a in r_s.json())
    assert all(a["status"]=="completed" for a in r_c.json())
    assert all(a["status"]=="no_show" for a in r_n.json())
