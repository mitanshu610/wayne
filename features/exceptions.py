from fastapi import status

class FeatureError(Exception):
    """
    Base class for feature-related errors.
    Provides an interface to store a message, detail, and status code.
    """
    def __init__(
        self,
        message: str = "An error occurred in the Feature Service",
        detail: str = None,
        status_code: int = status.HTTP_400_BAD_REQUEST
    ):
        self.message = message
        self.detail = detail or message
        self.status_code = status_code
        super().__init__(message)


class FeatureNotFoundError(FeatureError):
    """ Raised when a feature cannot be found in the database. """
    def __init__(self, feature_id: str):
        super().__init__(
            message=f"Feature with ID '{feature_id}' not found.",
            detail="The requested feature does not exist in the database.",
            status_code=status.HTTP_404_NOT_FOUND
        )


class PlanNotFoundError(FeatureError):
    """ Raised when a plan cannot be found in the database. """
    def __init__(self, plan_id: str):
        super().__init__(
            message=f"Plan with ID '{plan_id}' not found.",
            detail="The requested plan does not exist in the database.",
            status_code=status.HTTP_404_NOT_FOUND
        )


class DuplicateFeatureAssignmentError(FeatureError):
    """ Raised when a feature is already added to a plan. """
    def __init__(self, feature_id: str, plan_id: str):
        super().__init__(
            message=f"Feature '{feature_id}' is already assigned to plan '{plan_id}'.",
            detail="A plan-feature relationship already exists and cannot be duplicated.",
            status_code=status.HTTP_409_CONFLICT
        )


class ServiceError(FeatureError):
    """ Generic catch-all for other feature service errors. """
    def __init__(self, detail: str):
        super().__init__(
            message="An unexpected service error occurred.",
            detail=detail,
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
        )
