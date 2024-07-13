from microstructpy.orders.base import Order

class LimitOrder(Order):
    def __init__(self, trader_id: int, quantity: int, price: int) -> None:
        super().__init__(trader_id, quantity)
        self.price = price

    def __repr__(self) -> str:
        return f"LMT P: {self.price} V: {self.quantity:+}."