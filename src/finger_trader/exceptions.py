"""Public exception hierarchy for API and transport failures."""

from dataclasses import dataclass, field
from typing import Any


@dataclass
class APIError(Exception):
    """A bounded, credential-safe API failure."""

    message: str
    code: Any = None
    status: int | None = None
    path: str | None = None
    details: Any = field(default=None, repr=False)

    def __str__(self) -> str:
        label = self.code if self.code is not None else self.status
        return f"Finger Trader API error {label or ''}: {self.message}".strip()

    @classmethod
    def from_payload(cls, payload, *, status=None, path=None):
        if not isinstance(payload, dict):
            payload = {}
        return cls(
            str(payload.get("message") or payload.get("msg") or "Request failed")[:1024],
            payload.get("code"),
            status,
            path,
            None,
        )


class NetworkError(APIError):
    """The request could not be completed by the transport."""


class UnknownOutcomeError(NetworkError):
    """A state-changing request may have reached the server; outcome is unknown."""

    def __init__(
        self,
        message="Request outcome is unknown; reconcile with the server before retrying",
        **kwargs,
    ):
        super().__init__(message=message, code="UNKNOWN_OUTCOME", **kwargs)
