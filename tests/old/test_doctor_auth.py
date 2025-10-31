def test_doctor_requires_auth(client):
    r = client.get("/api/doctor/availability")
    assert r.status_code == 401

def test_doctor_with_auth_ok(client, auth_header):
    r = client.get("/api/doctor/availability", headers=auth_header)
    assert r.status_code == 200
    assert isinstance(r.json(), list)
