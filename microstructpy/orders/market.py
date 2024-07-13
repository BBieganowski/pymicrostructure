import numpy as np
from microstructpy.orders.base import Order

class MarketOrder(Order):
    def __init__(self, trader_id: int, quantity) -> None:
        super().__init__(trader_id, quantity)
        self.price = np.inf if quantity > 0 else -np.inf

    def __repr__(self) -> str:
        return f"MKT V: {self.quantity:+}."