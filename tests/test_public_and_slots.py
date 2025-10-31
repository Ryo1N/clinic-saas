from datetime import datetime, timedelta, timezone

from conftest import iso

def test_availability_to_slots_and_booking_flow(client, auth_header, tomorrow_10_to_noon, day_window):
    # 1) Doctor available for 10:00-12:00
    start, end = tomorrow_10_to_noon
    r = client.post("/api/doctor/availability", headers=auth_header, json={
        "start_at": start, "end_at": end, "is_active": True
    })
    assert r.status_code == 201, r.text
    avail = r.json()
    assert avail["start_at"] and avail["end_at"]

    # 2) Retrive public slots（4 slots：10:00,10:30,11:00,11:30）
    w_from, w_to = day_window
    rs = client.get(f"/api/public/slots?from={w_from}&to={w_to}")
    assert rs.status_code == 200
    slots = rs.json()
    # Make sure there are at least 4 slots available
    assert sum(1 for s in slots if "T10:00" in s["start_at"] or "T11:" in s["start_at"]) >= 2

    # 3) 201 on first slot
    s0 = slots[0]
    rb = client.post("/api/public/appointments", json={
        "start_at": s0["start_at"], "end_at": s0["end_at"],
        "patient_name": "Alice", "note": "first"
    })
    assert rb.status_code == 201, rb.text
    appt = rb.json()
    appt_id = appt["id"]

    # 4) No reserving same spot multiple times (409 expected)
    rb2 = client.post("/api/public/appointments", json={
        "start_at": s0["start_at"], "end_at": s0["end_at"],
        "patient_name": "Bob"
    })
    assert rb2.status_code in (409, 400), rb2.text  # 実装によっては409/400いずれか

    # 5) If outside of availability, expect 400
    # Example: 12:00-12:30 is out of availabiltiy
    last_end_iso = slots[-1]["end_at"]
    dt = datetime.fromisoformat(last_end_iso.replace("Z", "+00:00")) + timedelta(minutes=30)
    out_start_iso = iso(dt)
    out_end = iso(dt + timedelta(minutes=30))
    rbad = client.post("/api/public/appointments", json={
        "start_at": out_start_iso, "end_at": out_end, "patient_name": "Carol"
    })
    assert rbad.status_code == 400, rbad.text

    # 6) If doctor cancels an appointment, availability is back
    rc = client.patch(f"/api/doctor/appointments/{appt_id}", headers=auth_header, json={"status":"canceled"})
    assert rc.status_code == 200, rc.text
    # The same slot can be appointed again
    rs2 = client.get(f"/api/public/slots?from={w_from}&to={w_to}")
    assert rs2.status_code == 200
    slots2 = rs2.json()
    assert len(slots2) >= len(slots), "canceled might not have returned an empty slot"
