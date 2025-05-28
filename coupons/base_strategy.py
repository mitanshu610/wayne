from abc import ABC, abstractmethod
from plans.schemas import DiscountType

class CouponStrategy(ABC):
    """Abstract strategy for coupon discount calculation."""

    @abstractmethod
    def apply_discount(self, plan_amount: float, discount_value: float) -> float:
        """Apply discount and return the final discounted amount."""
        pass
