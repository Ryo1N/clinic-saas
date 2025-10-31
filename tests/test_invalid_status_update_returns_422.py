def test_invalid_status_update_returns_422(client, auth_header, tomorrow_10_to_noon):
    start, end = tomorrow_10_to_noon
    # Make available > reserve > invalid status
    client.post("/api/doctor/availability", headers=auth_header, json={"start_at": start, "end_at": end, "is_active": True})
    rb = client.post("/api/public/appointments", json={
        "start_at": start, "end_at": (start.replace("10:00:00Z","10:30:00Z")), "patient_name": "X"
    })
    appt_id = rb.json()["id"]
    r = client.patch(f"/api/doctor/appointments/{appt_id}", headers=auth_header, json={"status": "unknown_value"})
    assert r.status_code == 422
