# Changelog

## 1.0.0 — work-in-progress checkpoint

Partial code published for continued development. Known issues: STATUS.md.

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [1.0.0] - 2026-10-20

### Added
- Initial project skeleton with FastAPI backend and React frontend
- Docker Compose setup with Keycloak, backend, and frontend services
- Health check endpoints (/health/, /health/db)
- OIDC authentication flow with Keycloak (authorization code + PKCE)
- React dashboard with login, callback, and settings pages
- Role-based access control (viewer, operator, admin)
- Comprehensive README with architecture diagram
- MIT License
- .env.example with all configuration options
- Keycloak realm export with pre-configured client and roles
- Backend tests for health endpoints
- Frontend test for App component

### Security
- Non-root Docker users
- HttpOnly cookies for session management
- PKCE for OIDC flow
- CORS restricted to configured origins
- No hardcoded secrets