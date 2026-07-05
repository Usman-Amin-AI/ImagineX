# Changelog

## Unreleased

### Added
- ImagineX branding and fork-specific support messaging in the README.
- Docker packaging for GPU-enabled deployment with Redis-backed queue support.
- Environment-based backend selection via IMAGINEX_BACKEND.
- Headless API mode support and queue-based job orchestration.
- Optional safety filtering and configurable runtime settings.

### Changed
- The web UI title now identifies the distribution as ImagineX while remaining Fooocus-compatible.
- The API service name now reflects the ImagineX distribution.
- Container defaults now target a persistent data volume and GPU-enabled deployment.

### Notes on upstream divergence
- This fork is an independently maintained extension of the public Fooocus project, not a copy-only rebrand.
- It remains compatible with the existing Fooocus WebUI workflow while adding a stronger API, queue, safety, and deployment experience.
- Runtime and packaging changes are maintained independently from upstream lllyasviel/Fooocus, with a distinct ImagineX support scope and direction.
