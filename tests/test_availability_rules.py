from datetime import datetime, timedelta, timezone

from conftest import iso

def test_overlap_availability_is_rejected(client, auth_header, tomorrow_10_to_noon):
    start, end = tomorrow_10_to_noon
    # Availability to use as base
    r1 = client.post("/api/doctor/availability", headers=auth_header, json={
        "start_at": start, "end_at": end, "is_active": True
    })
    assert r1.status_code == 201
    # Overlap as 11:00-11:30
    s2 = iso(datetime.fromisoformat(start.replace("Z","+00:00")).replace(hour=11))
    e2 = iso(datetime.fromisoformat(end.replace("Z","+00:00")) + timedelta(minutes=30))
    r2 = client.post("/api/doctor/availability", headers=auth_header, json={
        "start_at": s2, "end_at": e2, "is_active": True
    })
    assert r2.status_code == 400, r2.text  # Reject overlap

def test_put_availability_cannot_evict_existing_appointment(client, auth_header, tomorrow_10_to_noon):
    start, end = tomorrow_10_to_noon
    # Set 10:00-12:00 as available
    r = client.post("/api/doctor/availability", headers=auth_header, json={
        "start_at": start, "end_at": end, "is_active": True
    })
    assert r.status_code == 201, r.text
    avail = r.json()

    #Reserve 10:00-10:30
    s0 = iso(datetime.fromisoformat(start.replace("Z","+00:00")))
    e0 = iso(datetime.fromisoformat(s0.replace("Z","+00:00")) + timedelta(minutes=30))
    rb = client.post("/api/public/appointments", json={
        "start_at": s0, "end_at": e0, "patient_name": "Dave"
    })
    assert rb.status_code == 201, rb.text

    # Reduce availability to 10:30-11:00 (conflicts with 10:00-10:30)
    s_new = iso(datetime.fromisoformat(start.replace("Z","+00:00")) + timedelta(minutes=30))
    e_new = iso(datetime.fromisoformat(start.replace("Z","+00:00")) + timedelta(minutes=60))
    ru = client.put(f"/api/doctor/availability/{avail['id']}", headers=auth_header, json={
        "start_at": s_new, "end_at": e_new, "is_active": True
    })
    assert ru.status_code == 400, ru.text
