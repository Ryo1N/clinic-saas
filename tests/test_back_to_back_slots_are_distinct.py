def test_back_to_back_slots_are_distinct(client, auth_header, tomorrow_10_to_noon):
    start, end = tomorrow_10_to_noon
    client.post("/api/doctor/availability", headers=auth_header, json={"start_at": start, "end_at": end, "is_active": True})
    # 10:00–10:30 reservaton
    rb1 = client.post("/api/public/appointments", json={"start_at": start, "end_at": start.replace("10:00","10:30"), "patient_name": "A"})
    assert rb1.status_code == 201
    # 10:30–11:00 reservation (OK)
    rb2 = client.post("/api/public/appointments", json={"start_at": start.replace("10:00","10:30"), "end_at": start.replace("10:00","11:00"), "patient_name": "B"})
    assert rb2.status_code == 201
