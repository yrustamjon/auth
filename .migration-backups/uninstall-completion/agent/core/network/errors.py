"""Structured backend-client failures."""


class BackendApiError(Exception):
    """Base error for an external BioGuard Backend interaction."""


class BackendUnavailableError(BackendApiError):
    """The backend could not be reached before a response was received."""


class BackendResponseError(BackendApiError):
    """The backend returned an invalid or non-successful response."""

    def __init__(
        self,
        message: str,
        *,
        status_code: int | None = None,
        response_body: str | None = None,
    ):
        super().__init__(message)
        self.status_code = status_code
        self.response_body = response_body


class BackendAuthenticationError(BackendApiError):
    """The local device-authentication header could not be generated."""
