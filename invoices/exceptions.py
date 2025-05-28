from fastapi import status


class InvoiceError(Exception):
    """
    Base class for Invoice-related errors.
    Provides a consistent interface to store a message, detail, and status code.
    """
    def __init__(
        self,
        message: str = "An error occurred in the Invoice Service",
        detail: str = None,
        status_code: int = status.HTTP_400_BAD_REQUEST
    ):
        self.message = message
        self.detail = detail or message
        self.status_code = status_code
        super().__init__(message)


class InvoiceNotFoundError(InvoiceError):
    """Raised when an invoice cannot be found in the database."""
    def __init__(self, invoice_id: str):
        super().__init__(
            message=f"Invoice with ID '{invoice_id}' not found.",
            detail="The requested invoice does not exist in the database.",
            status_code=status.HTTP_404_NOT_FOUND
        )


class DuplicateInvoiceError(InvoiceError):
    """Raised when attempting to create a duplicate invoice."""
    def __init__(self, invoice_id: str):
        super().__init__(
            message=f"Invoice with ID '{invoice_id}' already exists.",
            detail="An invoice with the given details already exists in the database.",
            status_code=status.HTTP_409_CONFLICT
        )


class InvalidInvoiceDetailsError(InvoiceError):
    """Raised when provided invoice details are invalid."""
    def __init__(self, detail: str):
        super().__init__(
            message="Invalid invoice details provided.",
            detail=detail,
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY
        )


class InvoiceUpdateError(InvoiceError):
    """Raised when an error occurs during invoice update."""
    def __init__(self, invoice_id: str):
        super().__init__(
            message=f"Unable to update invoice with ID '{invoice_id}'.",
            detail="An error occurred while updating the invoice.",
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


class InvoiceDeletionError(InvoiceError):
    """Raised when an error occurs during invoice deletion."""
    def __init__(self, invoice_id: str):
        super().__init__(
            message=f"Unable to delete invoice with ID '{invoice_id}'.",
            detail="An error occurred while deleting the invoice.",
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
        )
