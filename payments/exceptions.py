from fastapi import status


class PaymentError(Exception):
    """
    Base class for payment-related errors.
    Provides a consistent interface to store an error message, detail, and status code.
    """
    def __init__(
        self,
        message: str = "An error occurred in the Payment Service",
        detail: str = None,
        status_code: int = status.HTTP_400_BAD_REQUEST
    ):
        self.message = message
        self.detail = detail or message
        self.status_code = status_code
        super().__init__(message)


class PlanNotFoundError(PaymentError):
    """
    Raised when a plan cannot be found in the database.
    """
    def __init__(self, plan_id: str):
        super().__init__(
            message=f"Plan with ID '{plan_id}' not found.",
            detail="Cannot proceed with subscription creation because the specified plan does not exist.",
            status_code=status.HTTP_404_NOT_FOUND
        )


class SubscriptionNotFoundError(PaymentError):
    """
    Raised when a subscription cannot be found in the database.
    """
    def __init__(self):
        super().__init__(
            message="Subscription not found.",
            detail="No subscription record could be located.",
            status_code=status.HTTP_404_NOT_FOUND
        )


class SubscriptionConflictError(PaymentError):
    """
    Raised when a conflicting subscription action is detected.
    E.g., user tries to subscribe again while a subscription is already in progress.
    """
    def __init__(self, message: str = None):
        message = message or "A conflicting subscription action was detected."
        super().__init__(
            message=message,
            detail="One payment is already under process. Please wait a moment before trying again.",
            status_code=status.HTTP_409_CONFLICT
        )
