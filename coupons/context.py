from coupons.strategies import PercentageCouponStrategy, NoDiscountStrategy, FlatCouponStrategy
from plans.schemas import DiscountType


class CouponContext:
    """Context class to apply the appropriate coupon strategy."""

    def __init__(self, discount_type: str):
        if discount_type == DiscountType.PERCENTAGE.value:
            self.strategy = PercentageCouponStrategy()
        elif discount_type == DiscountType.FLAT.value:
            self.strategy = FlatCouponStrategy()
        else:
            self.strategy = NoDiscountStrategy()

    def apply_coupon(self, plan_amount: float, discount_value: float) -> float:
        return self.strategy.apply_discount(plan_amount, discount_value)
