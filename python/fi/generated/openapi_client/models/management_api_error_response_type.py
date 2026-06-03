from enum import Enum


class ManagementAPIErrorResponseType(str, Enum):
    API_ERROR = "api_error"
    AUTHENTICATION_ERROR = "authentication_error"
    CLIENT_ERROR = "client_error"
    CONFLICT = "conflict"
    ENTITLEMENT_ERROR = "entitlement_error"
    NOT_FOUND = "not_found"
    PAYMENT_REQUIRED = "payment_required"
    PERMISSION_ERROR = "permission_error"
    RATE_LIMIT = "rate_limit"
    SERVER_ERROR = "server_error"
    SERVICE_UNAVAILABLE = "service_unavailable"
    TIMEOUT = "timeout"
    VALIDATION_ERROR = "validation_error"

    def __str__(self) -> str:
        return str(self.value)
