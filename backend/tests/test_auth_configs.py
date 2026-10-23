import pytest
from httpx import AsyncClient, ASGITransport
from unittest.mock import AsyncMock, patch, MagicMock
from app.main import app
from app.core.auth import AuthService
from app.core.models import User


@pytest.fixture
async def client():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        yield ac


@pytest.fixture
def mock_user():
    user = MagicMock(spec=User)
    user.id = 1
    user.username = "testuser"
    user.email = "test@example.com"
    user.get_roles.return_value = ["viewer"]
    return user


    @pytest.mark.asyncio
    async def test_callback_missing_code(self, client):
        with patch('app.api.auth.settings') as mock_settings:
            mock_settings.oidc_enabled = True
            mock_settings.oidc_issuer_url = "http://localhost:8080/realms/test"
            mock_settings.oidc_client_id = "test"
            mock_settings.oidc_client_secret = ""
        response = await client.post("/auth/callback", json={"code": "valid-code", "redirect_uri": "http://localhost:5173/callback"})
        # Should fail with 400 because token exchange fails (no real Keycloak)
        assert response.status_code in (400, 503)

    @pytest.mark.asyncio
    async def test_logout_returns_url(self, client):
        with patch('app.api.auth.settings') as mock_settings:
            mock_settings.oidc_enabled = True
            mock_settings.oidc_issuer_url = "http://localhost:8080/realms/test"
            mock_settings.oidc_logout_uri = "http://localhost:5173"
            response = await client.post("/auth/logout")
            assert response.status_code == 200
            assert "logout_url" in response.json()

    @pytest.mark.asyncio
    async def test_me_requires_auth(self, client):
        response = await client.get("/auth/me")
        assert response.status_code == 401

    @pytest.mark.asyncio
    async def test_me_invalid_token(self, client):
        response = await client.get("/auth/me", headers={"Authorization": "Bearer invalid-token"})
        assert response.status_code == 401


class TestConfigEndpoints:
    @pytest.mark.asyncio
    async def test_list_configs_requires_auth(self, client):
        response = await client.get("/configs")
        assert response.status_code == 401

    @pytest.mark.asyncio
    async def test_create_config_requires_auth(self, client):
        response = await client.post("/configs", json={"name": "test", "config_data": "{}"})
        assert response.status_code == 401

    @pytest.mark.asyncio
    async def test_get_config_requires_auth(self, client):
        response = await client.get("/configs/1")
        assert response.status_code == 401

    @pytest.mark.asyncio
    async def test_update_config_requires_auth(self, client):
        response = await client.put("/configs/1", json={"name": "updated"})
        assert response.status_code == 401

    @pytest.mark.asyncio
    async def test_delete_config_requires_auth(self, client):
        response = await client.delete("/configs/1")
        assert response.status_code == 401


class TestAuthService:
    @pytest.mark.asyncio
    async def test_decode_session_token_valid(self):
        from app.core.config import settings
        token = AuthService.create_access_token(MagicMock(
            id=1, username="test", email="test@example.com", get_roles=lambda: ["viewer"]
        ))
        payload = AuthService.decode_session_token(token)
        assert payload is not None
        assert payload["sub"] == "1"
        assert payload["username"] == "test"

    @pytest.mark.asyncio
    async def test_decode_session_token_invalid(self):
        payload = AuthService.decode_session_token("invalid-token")
        assert payload is None

    @pytest.mark.asyncio
    async def test_create_access_token(self, mock_user):
        token = AuthService.create_access_token(mock_user)
        assert isinstance(token, str)
        assert len(token) > 0
        payload = AuthService.decode_session_token(token)
        assert payload["sub"] == "1"
        assert payload["username"] == "testuser"