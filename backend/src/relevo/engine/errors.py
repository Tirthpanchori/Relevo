"""Expected engine errors exposed through a stable API envelope."""


class EngineError(Exception):
    status_code = 400
    code = "engine_error"


class JobNotFound(EngineError):
    status_code = 404
    code = "job_not_found"


class IdempotencyConflict(EngineError):
    status_code = 409
    code = "idempotency_conflict"


class SizeLimitExceeded(EngineError):
    status_code = 413
    code = "size_limit_exceeded"


class AttemptNotFound(EngineError):
    status_code = 404
    code = "attempt_not_found"


class OwnershipConflict(EngineError):
    status_code = 409
    code = "ownership_conflict"
