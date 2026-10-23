# Product development plan

Each round completes one feature or repair. Future items are planned, not implemented claims.

## Current round

auth-oidc

## Roadmap

### project-skeleton — Project skeleton with FastAPI backend and React frontend

Status: done

Acceptance:
- FastAPI app starts and serves health endpoint
- React app builds and serves frontend
- Docker compose brings up backend, frontend, and Keycloak
- Basic OIDC authentication flow configured

Implementation: `backend/app/main.py`, `backend/app/core/config.py`, `backend/app/api/health.py`, `backend/requirements.txt`, `frontend/package.json`, `frontend/src/main.tsx`, `frontend/src/App.tsx`, `docker-compose.yaml`, `Dockerfile.backend`, `Dockerfile.frontend`

Tests: `backend/tests/test_health.py`, `frontend/src/App.test.tsx`

### auth-oidc — OIDC authentication with Keycloak

Status: done

Acceptance:
- Login redirects to Keycloak
- Callback exchanges code for tokens
- Protected endpoints require valid token
- Logout clears session

Implementation: `backend/app/core/auth.py`, `backend/app/core/models.py`, `backend/app/api/auth.py`, `backend/app/api/configs.py`, `frontend/src/hooks/AuthContext.tsx`, `frontend/src/components/Callback.tsx`, `frontend/src/components/Configs.tsx`, `frontend/src/api/client.ts`, `frontend/src/App.tsx`

Tests: `backend/tests/test_auth_configs.py`, `frontend/src/App.test.tsx`

### agent-config-manager — AI agent configuration management (core domain engine)

Status: planned

Acceptance:
- Create/read/update/delete agent configurations
- Validate hook schemas and configurations
- Import/export configurations
- Search and filter configurations

### hook-validation-engine — Hook schema validation engine

Status: planned

Acceptance:
- Validate Agent Plugins schema compliance
- Detect CRLF/line ending issues
- Check hook event ordering and conflicts
- Report validation errors with actionable messages

### session-analyzer — Session transcript analysis workflow

Status: planned

Acceptance:
- Parse transcript files
- Extract hook execution patterns
- Identify skipped/failed hooks
- Generate session quality report

