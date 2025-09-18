from unittest.mock import Mock

import pytest
from sqlalchemy import select

from src.db.models import User
from tests.conftest import TestingSessionLocal

from httpx import AsyncClient


user_data = {
    "username": "agent007",
    "email": "agent007@gmail.com",
    "password": "12345678",
    "role": "user",
}


def test_signup(client, monkeypatch):
    mock_send_email = Mock()
    monkeypatch.setattr("src.api.auth.send_email", mock_send_email)
    response = client.post("api/auth/register", json=user_data)
    assert response.status_code == 201, response.text
    data = response.json()
    assert data["username"] == user_data["username"]
    assert data["email"] == user_data["email"]
    assert "hashed_password" not in data
    assert "avatar" in data


def test_repeat_signup(client, monkeypatch):
    mock_send_email = Mock()
    monkeypatch.setattr("src.api.auth.send_email", mock_send_email)
    response = client.post("api/auth/register", json=user_data)
    assert response.status_code == 409, response.text
    data = response.json()
    assert data["detail"] == "Користувач з таким email вже існує"


def test_not_confirmed_login(client):
    response = client.post(
        "api/auth/login",
        data={
            "username": user_data.get("username"),
            "password": user_data.get("password"),
        },
    )
    assert response.status_code == 401, response.text
    data = response.json()
    assert data["detail"] == "Електронна адреса не підтверджена"


@pytest.mark.asyncio
async def test_login(client):
    async with TestingSessionLocal() as session:
        current_user = await session.execute(
            select(User).where(User.email == user_data.get("email"))
        )
        current_user = current_user.scalar_one_or_none()
        if current_user:
            current_user.confirmed = True
            await session.commit()

    response = client.post(
        "api/auth/login",
        data={
            "username": user_data.get("username"),
            "password": user_data.get("password"),
        },
    )
    assert response.status_code == 200, response.text
    data = response.json()
    assert "access_token" in data
    assert "token_type" in data


def test_wrong_password_login(client):
    response = client.post(
        "api/auth/login",
        data={"username": user_data.get("username"), "password": "password"},
    )
    assert response.status_code == 401, response.text
    data = response.json()
    assert data["detail"] == "Неправильний логін або пароль"


def test_wrong_username_login(client):
    response = client.post(
        "api/auth/login",
        data={"username": "username", "password": user_data.get("password")},
    )
    assert response.status_code == 401, response.text
    data = response.json()
    assert data["detail"] == "Неправильний логін або пароль"


def test_validation_error_login(client):
    response = client.post(
        "api/auth/login", data={"password": user_data.get("password")}
    )
    assert response.status_code == 422, response.text
    data = response.json()
    assert "detail" in data


###############################
def test_signup_email_already_exists(client, monkeypatch):
    """Try to register with an email that already exists but a different username."""
    mock_send_email = Mock()
    monkeypatch.setattr("src.api.auth.send_email", mock_send_email)
    user_data2 = {
        "username": "agent008",
        "email": "agent007@gmail.com",  # same email as user_data
        "password": "87654321",
        "role": "user",
    }
    response = client.post("api/auth/register/", json=user_data2)
    assert response.status_code == 409, response.text
    # data = response.json()
    # assert data["detail"] == f"User with email: {user_data2['email']} already exists"


def test_signup_validation_error(client, monkeypatch):
    """Try to register with missing required fields."""
    mock_send_email = Mock()
    monkeypatch.setattr("src.api.auth.send_email", mock_send_email)
    incomplete_data = {
        "username": "agent009",
        "email": "agent009@gmail.com",
        # missing password
    }
    response = client.post("api/auth/register/", json=incomplete_data)
    assert response.status_code == 422, response.text
    data = response.json()
    assert "detail" in data


def test_confirmed_email_invalid_token(client):
    """Try to confirm email with an invalid token."""
    response = client.get("api/auth/confirmed_email/invalidtoken")
    assert response.status_code == 422
    data = response.json()
    assert data["detail"] == "Невірний токен для перевірки електронної пошти"


def test_request_email_not_found(client, monkeypatch):
    """Try to request email confirmation for a non-existent email."""
    mock_send_email = Mock()
    monkeypatch.setattr("src.api.auth.send_email", mock_send_email)
    body = {"email": "notfound@gmail.com"}
    response = client.post("api/auth/request_email/", json=body)
    assert response.status_code == 404, response.text
    data = response.json()
    assert "User with this email not found" in data["detail"]


def test_request_email_already_confirmed(client):
    """Try to request email confirmation for an already confirmed user."""
    body = {"email": user_data["email"]}
    response = client.post("api/auth/request_email/", json=body)
    assert response.status_code == 200, response.text
    data = response.json()
    assert data["message"] == "Ваша електронна пошта вже підтверджена"
