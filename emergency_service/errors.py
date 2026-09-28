class PlatformError(Exception):
    code = "platform_error"

class NotFound(PlatformError):
    code = "not_found"

class Conflict(PlatformError):
    code = "conflict"

class PermissionDenied(PlatformError):
    code = "permission_denied"

class InvalidTransition(PlatformError):
    code = "invalid_transition"

class CapacityExceeded(PlatformError):
    code = "capacity_exceeded"

class DuplicateRequest(PlatformError):
    code = "duplicate_request"
