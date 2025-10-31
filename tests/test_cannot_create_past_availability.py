from datetime import datetime, timedelta, timezone

def test_cannot_create_past_availability(client, auth_header):
    past = datetime.now(timezone.utc) - timedelta(minutes=60)
    r = client.post("/api/doctor/availability", headers=auth_header, json={
        "start_at": past.isoformat().replace("+00:00","Z"),
        "end_at":   (past + timedelta(minutes=30)).isoformat().replace("+00:00","Z"),
        "is_active": True
    })
    assert r.status_code in (400, 422)
