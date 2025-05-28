from coupons.base_strategy import CouponStrategy


class PercentageCouponStrategy(CouponStrategy):
    """Concrete strategy for percentage-based discounts."""

    def apply_discount(self, plan_amount: float, discount_value: float) -> float:
        return (plan_amount * discount_value) / 100


class FlatCouponStrategy(CouponStrategy):
    """Concrete strategy for flat discounts."""

    def apply_discount(self, plan_amount: float, discount_value: float) -> float:
        return min(discount_value, plan_amount)


class NoDiscountStrategy(CouponStrategy):
    """Concrete strategy when no discount is applied."""

    def apply_discount(self, plan_amount: float, discount_value: float) -> float:
        return 0.0
