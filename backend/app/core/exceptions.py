"""
SatQuery AI — Custom Exceptions

All application-specific exceptions extend SatQueryError.
The global handler in main.py maps these to safe JSON responses.
Stack traces are NEVER sent to the client — they are logged server-side only.
"""

from typing import Any


class SatQueryError(Exception):
    """Base exception for all SatQuery AI errors."""

    error_code: str = "INTERNAL_ERROR"
    status_code: int = 500
    message: str = "An unexpected error occurred."
    details: dict[str, Any]

    def __init__(
        self,
        message: str | None = None,
        details: dict[str, Any] | None = None,
    ) -> None:
        self.message = message or self.__class__.message
        self.details = details or {}
        super().__init__(self.message)


# ---- File / Ingestion Errors -------------------------------------------

class InvalidFileFormatError(SatQueryError):
    error_code = "INVALID_FILE_FORMAT"
    status_code = 422
    message = "Only GeoTIFF/TIFF files are accepted for geospatial analysis."


class FileTooLargeError(SatQueryError):
    error_code = "FILE_TOO_LARGE"
    status_code = 413
    message = "The uploaded file exceeds the maximum allowed size."


class CorruptedRasterError(SatQueryError):
    error_code = "CORRUPTED_RASTER"
    status_code = 422
    message = "The uploaded raster file could not be read or is corrupted."


class InvalidCRSError(SatQueryError):
    error_code = "INVALID_CRS"
    status_code = 422
    message = "The raster file has an invalid or missing coordinate reference system."


class PairAlignmentError(SatQueryError):
    error_code = "PAIR_ALIGNMENT_ERROR"
    status_code = 422
    message = (
        "The uploaded images cannot be safely compared because "
        "their spatial alignment does not match."
    )


class UnsupportedConfigurationError(SatQueryError):
    error_code = "UNSUPPORTED_CONFIGURATION"
    status_code = 422
    message = "The uploaded image configuration is not supported."


# ---- Router / Registry Errors ------------------------------------------

class NoSpecialistAvailableError(SatQueryError):
    error_code = "NO_SPECIALIST_AVAILABLE"
    status_code = 503
    message = "No specialist is available to handle this request."


class InvalidToolRequestError(SatQueryError):
    error_code = "INVALID_TOOL_REQUEST"
    status_code = 400
    message = "The requested tool is not registered or is disabled."


# ---- Provider Errors ---------------------------------------------------

class ProviderError(SatQueryError):
    error_code = "PROVIDER_ERROR"
    status_code = 502
    message = "The AI provider returned an error."


class ProviderTimeoutError(SatQueryError):
    error_code = "PROVIDER_TIMEOUT"
    status_code = 504
    message = "The AI provider did not respond in time."


# ---- Evidence / Confidence Errors --------------------------------------

class InsufficientEvidenceError(SatQueryError):
    error_code = "INSUFFICIENT_EVIDENCE"
    status_code = 200  # Not a server error — a valid "cannot answer" state
    message = "Insufficient evidence to provide a reliable answer."


# ---- Not Found ---------------------------------------------------------

class NotFoundError(SatQueryError):
    error_code = "NOT_FOUND"
    status_code = 404
    message = "The requested resource was not found."
