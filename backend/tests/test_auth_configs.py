import json
import pytest
from httpx import AsyncClient, ASGITransport
from unittest.mock import MagicMock, patch
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


@pytest.fixture
def auth_client(client, mock_user):
    """Create an authenticated client with a test user in the database."""
    from app.core.database import SessionLocal
    
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
    
    token = AuthService.create_access_token(mock_user)
    
    client.headers.update({"Authorization": f"Bearer {token}"})
    return client


class TestConfigEndpoints:
    ...


class TestConfigCRUD:
    ...


class TestAuthService:
    ...


class TestHookValidation:
    """Hook schema validation engine tests."""

    @pytest.mark.asyncio
    async def test_validate_valid_hook_schema(self, auth_client):
        """Valid hook schema with on_start event should pass."""
        # First create a config with valid schema
        create_resp = await auth_client.post(
            "/configs",
            json={"name": "Test Hook", "description": "A test", "config_data": '{"on_start": {"command": "echo hello"}}'}
        )
        assert create_resp.status_code == 201
        config_id = create_resp.json()["id"]
        
        response = await auth_client.post(
            f"/configs/{config_id}/validate",
        )
        assert response.status_code == 200
        data = response.json()
        assert data["valid"] is True
        assert data["errors"] == []

    @pytest.mark.asyncio
    async def test_validate_crlf_rejected_at_create(self, auth_client):
        """Hook schema with CRLF should be rejected at creation time."""
        response = await auth_client.post(
            "/configs",
            json={"name": "CRLF Test", "description": "CRLF test", "config_data": '{"on_start": "command\r\n echo hello"}'},
        )
        assert response.status_code == 422

    @pytest.mark.asyncio
    async def test_validate_invalid_hook_event_via_validate_endpoint(self, auth_client):
        """Hook schema with invalid event name should be rejected via validate endpoint."""
        # Create a config with invalid event (stored because Pydantic may not catch it)
        create_resp = await auth_client.post(
            "/configs",
            json={"name": "Invalid Event Test", "description": "Test", "config_data": '{"on_unknown": {"command": "test"}}'}
        )
        assert create_resp.status_code == 201
        config_id = create_resp.json()["id"]
        
        # But the validate endpoint should catch it
        response = await auth_client.post(
            f"/configs/{config_id}/validate",
        )
        assert response.status_code == 200
        data = response.json()
        assert data["valid"] is False
        assert any("Invalid hook event" in e for e in data["errors"])

    @pytest.mark.asyncio
    async def test_validate_null_schema(self, auth_client):
        """Null hook schema should produce error when validated."""
        create_resp = await auth_client.post(
            "/configs",
            json={"name": "Null Test", "description": "Test", "config_data": 'null'},
        )
        assert create_resp.status_code == 201
        config_id = create_resp.json()["id"]
        
        response = await auth_client.post(
            f"/configs/{config_id}/validate",
        )
        assert response.status_code == 200
        data = response.json()
        assert data["valid"] is False
        assert any("null" in e.lower() for e in data["errors"])

    @pytest.mark.asyncio
    async def test_validate_missing_event(self, auth_client):
        """Hook schema with no valid events should be rejected."""
        create_resp = await auth_client.post(
            "/configs",
            json={"name": "Missing Event Test", "description": "Test", "config_data": '{"custom_event": {"command": "test"}}'}
        )
        assert create_resp.status_code == 201
        config_id = create_resp.json()["id"]
        
        response = await auth_client.post(
            f"/configs/{config_id}/validate",
        )
        assert response.status_code == 200
        data = response.json()
        assert data["valid"] is False
        assert any("must contain at least one valid hook event" in e.lower() for e in data["errors"])

    @pytest.mark.asyncio
    async def test_validate_all_events(self, auth_client):
        """Hook schema with all valid events should pass."""
        create_resp = await auth_client.post(
            "/configs",
            json={"name": "All Events Test", "description": "Test", "config_data": '{"on_start": {}, "on_end": {}, "on_error": {}}'}
        )
        assert create_resp.status_code == 201
        config_id = create_resp.json()["id"]
        
        response = await auth_client.post(
            f"/configs/{config_id}/validate",
        )
        assert response.status_code == 200
        data = response.json()
        assert data["valid"] is True
        assert data["errors"] == []
