import pytest


async def get_access_token(client, username="meuser", email="me@example.com", password="password123"):
    await client.post(
        "/api/v1/auth/register",
        json={"username": username, "email": email, "password": password},
    )
    resp = await client.post(
        "/api/v1/auth/login",
        data={"username": username, "password": password},
    )
    return resp.json()["access_token"]


@pytest.mark.asyncio
async def test_get_me(client):
    token = await get_access_token(client)
    resp = await client.get(
        "/api/v1/users/me",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert resp.status_code == 200
    assert resp.json()["username"] == "meuser"


@pytest.mark.asyncio
async def test_get_me_unauthorized(client):
    resp = await client.get("/api/v1/users/me")
    assert resp.status_code == 403


@pytest.mark.asyncio
async def test_update_me(client):
    token = await get_access_token(client, username="updateme", email="update@example.com")
    resp = await client.put(
        "/api/v1/users/me",
        headers={"Authorization": f"Bearer {token}"},
        json={"username": "updatedname"},
    )
    assert resp.status_code == 200
    assert resp.json()["username"] == "updatedname"


@pytest.mark.asyncio
async def test_change_password(client):
    token = await get_access_token(
        client, username="chgpw", email="chgpw@example.com", password="oldpassword"
    )
    resp = await client.put(
        "/api/v1/users/me/password",
        headers={"Authorization": f"Bearer {token}"},
        json={"old_password": "oldpassword", "new_password": "newpassword123"},
    )
    assert resp.status_code == 200

    # 新密码登录验证
    login_resp = await client.post(
        "/api/v1/auth/login",
        data={"username": "chgpw", "password": "newpassword123"},
    )
    assert login_resp.status_code == 200
