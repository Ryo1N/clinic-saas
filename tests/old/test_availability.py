from datetime import datetime, timedelta, timezone

def test_create_and_list_availability(client, auth_header):
    # 09:00-12:00 (+05:30) の例。UTC+0 のISOでも可だが、ここではUTCで送る
    start = datetime.now(timezone.utc).replace(hour=3, minute=30, second=0, microsecond=0)
    end   = start + timedelta(hours=3)

    payload = {
        "start_at": start.isoformat(),
        "end_at": end.isoformat(),
        "is_active": True
    }
    r = client.post("/api/doctor/availability", headers=auth_header, json=payload)
    assert r.status_code == 201, r.text
    created = r.json()
    assert created["is_active"] is True

    r2 = client.get("/api/doctor/availability", headers=auth_header)
    assert r2.status_code == 200
    rows = r2.json()
    assert any(row["id"] == created["id"] for row in rows)

def test_availability_end_after_start_validation(client, auth_header):
    now = datetime.now(timezone.utc)
    payload = {
        "start_at": now.isoformat(),
        "end_at": now.isoformat(),  # 同一 → 422 を期待
        "is_active": True
    }
    r = client.post("/api/doctor/availability", headers=auth_header, json=payload)
    assert r.status_code == 422
