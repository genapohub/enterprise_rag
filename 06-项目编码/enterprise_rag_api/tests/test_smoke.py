"""Core path smoke: login → kb → upload → status → ask citations."""
from pathlib import Path

FIXTURE = Path(__file__).parent / "fixtures" / "sample.txt"


def test_healthz(client):
    r = client.get("/healthz")
    assert r.status_code == 200
    body = r.json()
    assert body["code"] == 0
    assert body["data"]["status"] == "ok"


def test_login_and_me(client, auth_header):
    r = client.get("/api/v1/auth/me", headers=auth_header)
    assert r.status_code == 200
    assert r.json()["data"]["role"] == "admin"
    assert "password" not in r.text.lower() or "password_hash" not in r.text


def test_kb_upload_status_ask_citations(client, auth_header):
    # create KB
    r = client.post(
        "/api/v1/knowledge-bases",
        headers=auth_header,
        json={"name": "制度库", "description": "smoke"},
    )
    assert r.status_code == 200
    kb = r.json()["data"]
    assert kb["id"]
    kb_id = kb["id"]

    # upload txt
    files = {"file": ("sample.txt", FIXTURE.read_bytes(), "text/plain")}
    r = client.post(f"/api/v1/knowledge-bases/{kb_id}/documents", headers=auth_header, files=files)
    assert r.status_code == 200, r.text
    doc = r.json()["data"]
    assert "status" in doc
    assert doc["status"] == "ready", doc
    assert doc.get("fail_reason") is None
    assert doc["chunk_count"] > 0
    doc_id = doc["id"]

    # status fields present on get
    r = client.get(f"/api/v1/documents/{doc_id}", headers=auth_header)
    assert r.status_code == 200
    d = r.json()["data"]
    for key in ("status", "fail_reason", "is_archived", "chunk_count", "indexed_at"):
        assert key in d

    # conversation + ask
    r = client.post("/api/v1/conversations", headers=auth_header, json={"kb_id": kb_id, "title": "smoke"})
    assert r.status_code == 200
    conv_id = r.json()["data"]["id"]

    r = client.post(
        f"/api/v1/conversations/{conv_id}/messages",
        headers=auth_header,
        json={"content": "请假要提前几天？"},
    )
    assert r.status_code == 200, r.text
    data = r.json()["data"]
    asst = data["assistant_message"]
    assert asst["role"] == "assistant"
    assert isinstance(asst["citations"], list)
    assert len(asst["citations"]) >= 1
    cite = asst["citations"][0]
    for key in ("doc_id", "doc_name", "chunk_id", "snippet"):
        assert key in cite
    assert cite["doc_id"] == doc_id


def test_members_admin(client, auth_header):
    r = client.get("/api/v1/members", headers=auth_header)
    assert r.status_code == 200
    assert r.json()["data"]["total"] >= 1


def test_login_fail(client):
    r = client.post("/api/v1/auth/login", json={"username": "admin", "password": "wrong"})
    assert r.status_code == 401
    assert r.json()["code"] == 40101
