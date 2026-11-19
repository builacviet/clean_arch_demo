from src.domain.shared.exceptions import DomainError


class EmptyOrderError(DomainError):
    def __init__(self) -> None:
        super().__init__("Order must contain at least one item.")


class InvalidItemQuantityError(DomainError):
    def __init__(self, product_id: str) -> None:
        super().__init__(f"Quantity for product {product_id} must be greater than 0.")
