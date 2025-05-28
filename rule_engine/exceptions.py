from fastapi import status


class RuleError(Exception):
    """
    Base class for payment-related errors.
    Provides a consistent interface to store an error message, detail, and status code.
    """
    def __init__(
        self,
        message: str = "An error occurred in the Rules Service",
        detail: str = None,
        status_code: int = status.HTTP_400_BAD_REQUEST
    ):
        self.message = message
        self.detail = detail or message
        self.status_code = status_code
        super().__init__(message)