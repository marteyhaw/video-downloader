"""API layer utilities."""

from fastapi import HTTPException

from backend.services.security import SecurityError


def http_exception_from_security(exc: SecurityError) -> HTTPException:
    """Convert a domain SecurityError into an HTTP 400 response."""
    return HTTPException(status_code=400, detail=str(exc))
