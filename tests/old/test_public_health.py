def test_health_ok(client):
    r = client.get("/api/public/health")
    assert r.status_code == 200
    assert r.json() == {"ok": True}
