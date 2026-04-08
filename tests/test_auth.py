import pytest


@pytest.mark.asyncio
async def test_register(client):
    resp = await client.post(
        "/api/v1/auth/register",
        json={
            "username": "testuser",
            "email": "test@example.com",
            "password": "password123",
        },
    )
    assert resp.status_code == 201
    data = resp.json()
    assert data["username"] == "testuser"
    assert data["email"] == "test@example.com"
    assert "id" in data


@pytest.mark.asyncio
async def test_register_duplicate_username(client):
    await client.post(
        "/api/v1/auth/register",
        json={
            "username": "dupuser",
            "email": "dup@example.com",
            "password": "password123",
        },
    )
    resp = await client.post(
        "/api/v1/auth/register",
        json={
            "username": "dupuser",
            "email": "another@example.com",
            "password": "password123",
        },
    )
    assert resp.status_code == 409


@pytest.mark.asyncio
async def test_login(client):
    # 先注册
    await client.post(
        "/api/v1/auth/register",
        json={
            "username": "loginuser",
            "email": "login@example.com",
            "password": "password123",
        },
    )
    # 登录
    resp = await client.post(
        "/api/v1/auth/login",
        data={"username": "loginuser", "password": "password123"},
    )
    assert resp.status_code == 200
    data = resp.json()
    assert "access_token" in data
    assert "refresh_token" in data
    assert data["token_type"] == "bearer"


@pytest.mark.asyncio
async def test_login_wrong_password(client):
    await client.post(
        "/api/v1/auth/register",
        json={
            "username": "wrongpw",
            "email": "wrongpw@example.com",
            "password": "password123",
        },
    )
    resp = await client.post(
        "/api/v1/auth/login",
        data={"username": "wrongpw", "password": "wrongpassword"},
    )
    assert resp.status_code == 401
