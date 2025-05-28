from fastapi import status

class PlanError(Exception):
    """
    Base class for Plan-related errors.
    Provides a consistent interface to store a message, detail, and status code.
    """
    def __init__(
        self,
        message: str = "An error occurred in the Plan Service",
        detail: str = None,
        status_code: int = status.HTTP_400_BAD_REQUEST
    ):
        self.message = message
        self.detail = detail or message
        self.status_code = status_code
        super().__init__(message)


class PlanNotFoundError(PlanError):
    """Raised when a plan cannot be found in the database."""
    def __init__(self, plan_id: str):
        super().__init__(
            message=f"Plan with ID '{plan_id}' not found.",
            detail="The requested plan does not exist in the database.",
            status_code=status.HTTP_404_NOT_FOUND
        )


class CouponNotFoundError(PlanError):
    """Raised when a coupon cannot be found in the database."""
    def __init__(self, coupon_id: str):
        super().__init__(
            message=f"Coupon with ID '{coupon_id}' not found.",
            detail="The requested coupon does not exist in the database.",
            status_code=status.HTTP_404_NOT_FOUND
        )


class DuplicatePlanError(PlanError):
    """Raised when attempting to create a plan or coupon that already exists."""
    def __init__(self, plan_name: str):
        super().__init__(
            message=f"Plan '{plan_name}' already exists.",
            detail="A plan with the given details already exists in the database.",
            status_code=status.HTTP_409_CONFLICT
        )


class PlanServiceError(PlanError):
    """Generic internal service error for plan-related operations."""
    def __init__(self, detail: str = None):
        super().__init__(
            message="An unexpected error occurred in the Plan Service.",
            detail=detail,
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


class DuplicateCouponError(PlanError):
    """Raised when attempting to create a coupon with duplicate details."""
    def __init__(self):
        super().__init__(
            message="Coupon with the given code already exists.",
            detail="A coupon with the same code or details already exists in the database.",
            status_code=status.HTTP_409_CONFLICT
        )


class CouponUsageLimitExceededError(PlanError):
    """Raised when a coupon's usage exceeds its limit."""
    def __init__(self):
        super().__init__(
            message="Coupon has reached its usage limit.",
            detail="The coupon's usage count has exceeded its allowed limit.",
            status_code=status.HTTP_400_BAD_REQUEST
        )


class InvalidCouponDetailsError(PlanError):
    """Raised when provided coupon details are invalid."""
    def __init__(self, detail: str):
        super().__init__(
            message="Invalid coupon details provided.",
            detail=detail,
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY
        )