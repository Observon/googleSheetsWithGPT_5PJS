# Changelog

All notable changes to this project are documented in this file.

## [Unreleased]

### Fixed
- CI stability: pinned `numpy==1.26.4` to avoid pandas/NumPy ABI mismatch in test matrix.
- CI cache determinism: pip cache key now includes Python version for matrix jobs.

## [1.0.0] - 2026-03-31

### Added
- Clean Architecture refactor across `domain`, `adapters`, `services`, `cli`, and `api` layers.
- FastAPI app with routes for sheets listing, analysis, insights, exports, batch processing, and cache cleanup.
- Docker support with `Dockerfile`, `docker-compose.yml`, and `.dockerignore`.
- Expanded test suite for services, API routes, and scheduler.

### Changed
- Entry point renamed from legacy script to `__main__.py` and standardized module execution.
- Project and metadata naming aligned to `gpt-sheets-analyzer`.
- Documentation updated across setup, contributing, and usage guides.

### Fixed
- Import-time configuration side effects that blocked test collection.
- Pytest configuration conflicts in project tooling files.
- GitHub Actions workflow upgraded to Node 24-compatible action versions.

### Quality
- Test coverage raised to ~57% with 49 passing unit tests.

[Unreleased]: https://github.com/Observon/gpt-sheets-analyzer/compare/v1.0.0...main
[1.0.0]: https://github.com/Observon/gpt-sheets-analyzer/releases/tag/v1.0.0
