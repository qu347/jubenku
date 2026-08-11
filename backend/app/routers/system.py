"""Backward-compatible import for the health endpoint."""

from app.api.endpoints.health import router

__all__ = ["router"]
