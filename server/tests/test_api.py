def signup(client, username="alice", password="password123"):
    r = client.post("/signup", json={
        "username": username,
        "password": password,
        "password_confirmation": password
    })
    assert r.status_code == 201
    data = r.get_json()
    return data["token"], data["user"]["id"]

def auth_header(token):
    return {"Authorization": f"Bearer {token}"}

def test_health(client):
    r = client.get("/health")
    assert r.status_code == 200
    assert r.get_json()["status"] == "ok"

def test_auth_and_me(client):
    token, uid = signup(client)
    r = client.get("/me", headers=auth_header(token))
    assert r.status_code == 200
    assert r.get_json()["id"] == uid

def test_login_bad_creds(client):
    signup(client, "bob", "password123")
    r = client.post("/login", json={"username":"bob","password":"wrong"})
    assert r.status_code == 401
    assert "errors" in r.get_json()

def test_notes_crud_and_acl(client):
    a_tok, _ = signup(client, "alice", "password123")
    b_tok, _ = signup(client, "bob", "password123")

    r = client.post("/notes", json={"title":"t","content":"c"}, headers=auth_header(a_tok))
    assert r.status_code == 201
    note_id = r.get_json()["id"]

    r = client.get("/notes?page=1&per_page=1", headers=auth_header(a_tok))
    assert r.status_code == 200
    payload = r.get_json()
    assert "items" in payload and "total_items" in payload and payload["per_page"] == 1

    r = client.patch(f"/notes/{note_id}", json={"title":"hack"}, headers=auth_header(b_tok))
    assert r.status_code == 403

    r = client.patch(f"/notes/{note_id}", json={"content":"updated"}, headers=auth_header(a_tok))
    assert r.status_code == 200
    assert r.get_json()["content"] == "updated"

    r = client.delete(f"/notes/{note_id}", headers=auth_header(a_tok))
    assert r.status_code == 204

def test_requires_token(client):
    r = client.get("/notes")
    assert r.status_code in (401, 422)
