from fastapi.testclient import TestClient


def test_list_resumes_returns_empty(client: TestClient):
    resp = client.get("/api/resumes/")

    assert resp.status_code == 200
    assert resp.json() == []
