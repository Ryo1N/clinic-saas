def test_doctor_auth_required(client):
    r = client.get("/api/doctor/availability")  # no auth
    assert r.status_code == 401

def test_doctor_auth_wrong_password(client):
    hdr = {"Authorization": "Basic ZG9jdG9yOndyb25n"}  # doctor:wrong
    r = client.get("/api/doctor/availability", headers=hdr)
    assert r.status_code == 401
