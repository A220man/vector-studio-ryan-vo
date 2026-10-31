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


class TestConfigCRUD:
    @pytest.fixture(autouse=True)
    async def cleanup_db(self):
        """Clean up database before each test."""
        from app.core.database import SessionLocal
        from app.core.models import AgentConfig, User
        db = SessionLocal()
        try:
            db.query(AgentConfig).delete()
            # Don't delete the test user (id=1)
            db.query(User).filter(User.id != 1).delete()
            db.commit()
        finally:
            db.close()
        yield
        # Cleanup after test too
        db = SessionLocal()
        try:
            db.query(AgentConfig).delete()
            db.query(User).filter(User.id != 1).delete()
            db.commit()
        finally:
            db.close()

    @pytest.fixture
    async def auth_client(self):
        """Create an authenticated client with a test user in the database."""
        from app.core.auth import AuthService
        from app.core.models import User
        from app.core.database import SessionLocal
        
        # Create user in database
        db = SessionLocal()
        try:
            user = db.query(User).filter(User.id == 1).first()
            if not user:
                user = User(
                    id=1,
                    keycloak_id="test-keycloak-id",
                    username="testuser",
                    email="test@example.com",
                    roles='["viewer"]'
                )
                db.add(user)
                db.commit()
                db.refresh(user)
            user_id = user.id
        finally:
            db.close()
        
        # Create token
        from unittest.mock import MagicMock
        mock_user = MagicMock(spec=User)
        mock_user.id = user_id
        mock_user.username = "testuser"
        mock_user.email = "test@example.com"
        mock_user.get_roles.return_value = ["viewer"]
        
        token = AuthService.create_access_token(mock_user)
        
        client = AsyncClient(transport=ASGITransport(app=app), base_url="http://test")
        client.headers.update({"Authorization": f"Bearer {token}"})
        yield client
        await client.aclose()

    @pytest.mark.asyncio
    async def test_create_config(self, auth_client: AsyncClient):
        response = await auth_client.post("/configs", json={
            "name": "Test Config",
            "description": "A test configuration",
            "config_data": '{"model": "gpt-4", "temperature": 0.7}'
        })
        assert response.status_code == 201
        data = response.json()
        assert data["name"] == "Test Config"
        assert data["description"] == "A test configuration"
        assert data["config_data"] == '{"model": "gpt-4", "temperature": 0.7}'
        assert "id" in data
        assert "created_at" in data
        assert "updated_at" in data

    @pytest.mark.asyncio
    async def test_create_config_invalid_json(self, auth_client: AsyncClient):
        response = await auth_client.post("/configs", json={
            "name": "Test Config",
            "config_data": "not valid json"
        })
        assert response.status_code == 400
        assert "Invalid JSON" in response.json()["detail"]

    @pytest.mark.asyncio
    async def test_list_configs(self, auth_client: AsyncClient):
        # Create a few configs
        await auth_client.post("/configs", json={
            "name": "Config 1",
            "config_data": '{}'
        })
        await auth_client.post("/configs", json={
            "name": "Config 2",
            "config_data": '{}'
        })
        
        response = await auth_client.get("/configs")
        assert response.status_code == 200
        data = response.json()
        assert data["total"] == 2
        assert len(data["items"]) == 2
        assert data["page"] == 1
        assert data["limit"] == 20

    @pytest.mark.asyncio
    async def test_list_configs_with_search(self, auth_client: AsyncClient):
        await auth_client.post("/configs", json={
            "name": "Alpha Config",
            "config_data": '{}'
        })
        await auth_client.post("/configs", json={
            "name": "Beta Config",
            "config_data": '{}'
        })
        await auth_client.post("/configs", json={
            "name": "Gamma Config",
            "config_data": '{}'
        })
        
        response = await auth_client.get("/configs?search=Alpha")
        assert response.status_code == 200
        data = response.json()
        assert data["total"] == 1
        assert data["items"][0]["name"] == "Alpha Config"

    @pytest.mark.asyncio
    async def test_list_configs_pagination(self, auth_client: AsyncClient):
        for i in range(5):
            await auth_client.post("/configs", json={
                "name": f"Config {i}",
                "config_data": '{}'
            })
        
        response = await auth_client.get("/configs?page=1&limit=2")
        assert response.status_code == 200
        data = response.json()
        assert data["total"] == 5
        assert len(data["items"]) == 2
        assert data["page"] == 1
        assert data["limit"] == 2
        
        response = await auth_client.get("/configs?page=2&limit=2")
        assert response.status_code == 200
        data = response.json()
        assert len(data["items"]) == 2
        assert data["page"] == 2

    @pytest.mark.asyncio
    async def test_get_config(self, auth_client: AsyncClient):
        create_resp = await auth_client.post("/configs", json={
            "name": "Test Config",
            "config_data": '{"key": "value"}'
        })
        config_id = create_resp.json()["id"]
        
        response = await auth_client.get(f"/configs/{config_id}")
        assert response.status_code == 200
        data = response.json()
        assert data["id"] == config_id
        assert data["name"] == "Test Config"
        assert data["config_data"] == '{"key": "value"}'

    @pytest.mark.asyncio
    async def test_get_config_not_found(self, auth_client: AsyncClient):
        response = await auth_client.get("/configs/99999")
        assert response.status_code == 404

    @pytest.mark.asyncio
    async def test_update_config(self, auth_client: AsyncClient):
        create_resp = await auth_client.post("/configs", json={
            "name": "Original Name",
            "description": "Original description",
            "config_data": '{"version": 1}'
        })
        config_id = create_resp.json()["id"]
        
        response = await auth_client.put(f"/configs/{config_id}", json={
            "name": "Updated Name",
            "config_data": '{"version": 2}'
        })
        assert response.status_code == 200
        data = response.json()
        assert data["name"] == "Updated Name"
        assert data["description"] == "Original description"
        assert data["config_data"] == '{"version": 2}'

    @pytest.mark.asyncio
    async def test_update_config_partial(self, auth_client: AsyncClient):
        create_resp = await auth_client.post("/configs", json={
            "name": "Original Name",
            "description": "Original description",
            "config_data": '{"version": 1}'
        })
        config_id = create_resp.json()["id"]
        
        response = await auth_client.put(f"/configs/{config_id}", json={
            "description": "Only description updated"
        })
        assert response.status_code == 200
        data = response.json()
        assert data["name"] == "Original Name"
        assert data["description"] == "Only description updated"
        assert data["config_data"] == '{"version": 1}'

    @pytest.mark.asyncio
    async def test_update_config_invalid_json(self, auth_client: AsyncClient):
        create_resp = await auth_client.post("/configs", json={
            "name": "Test",
            "config_data": '{}'
        })
        config_id = create_resp.json()["id"]
        
        response = await auth_client.put(f"/configs/{config_id}", json={
            "config_data": "invalid json"
        })
        assert response.status_code == 400
        assert "Invalid JSON" in response.json()["detail"]

    @pytest.mark.asyncio
    async def test_delete_config(self, auth_client: AsyncClient):
        create_resp = await auth_client.post("/configs", json={
            "name": "To Delete",
            "config_data": '{}'
        })
        config_id = create_resp.json()["id"]
        
        response = await auth_client.delete(f"/configs/{config_id}")
        assert response.status_code == 204
        
        # Verify it's gone
        response = await auth_client.get(f"/configs/{config_id}")
        assert response.status_code == 404

    @pytest.mark.asyncio
    async def test_user_isolation(self, auth_client: AsyncClient):
        """Ensure users can only see their own configs."""
        create_resp = await auth_client.post("/configs", json={
            "name": "User 1 Config",
            "config_data": '{}'
        })
        config_id = create_resp.json()["id"]
        
        # Create a second user in database
        from app.core.database import SessionLocal
        from app.core.models import User
        db = SessionLocal()
        try:
            user2 = db.query(User).filter(User.id == 2).first()
            if not user2:
                user2 = User(
                    id=2,
                    keycloak_id="test-keycloak-id-2",
                    username="testuser2",
                    email="test2@example.com",
                    roles='["viewer"]'
                )
                db.add(user2)
                db.commit()
                db.refresh(user2)
        finally:
            db.close()
        
        # Create a second user token
        from app.core.auth import AuthService
        from unittest.mock import MagicMock
        
        mock_user2 = MagicMock(spec=User)
        mock_user2.id = 2
        mock_user2.username = "testuser2"
        mock_user2.email = "test2@example.com"
        mock_user2.get_roles.return_value = ["viewer"]
        
        token2 = AuthService.create_access_token(mock_user2)
        client2 = AsyncClient(transport=ASGITransport(app=app), base_url="http://test")
        client2.headers.update({"Authorization": f"Bearer {token2}"})
        
        # User 2 should not see User 1's config
        response = await client2.get("/configs")
        assert response.status_code == 200
        assert response.json()["total"] == 0
        
        # User 2 should not be able to access User 1's config
        response = await client2.get(f"/configs/{config_id}")
        assert response.status_code == 404
        
        await client2.aclose()

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