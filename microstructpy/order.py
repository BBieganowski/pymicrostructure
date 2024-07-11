from typing import Union
import numpy as np

class Order:
    def __init__(self, trader_id: int, quantity: int, time: Union[str, float]) -> None:
        if quantity == 0:
            raise ValueError("Order quantity must be non-zero.")
        self.trader_id  = trader_id
        self.quantity   = quantity
        self.time = time
        self.status     = "created"

class MarketOrder(Order):
    def __init__(self, trader_id: int, quantity: int, time: Union[str, float]) -> None:
        super().__init__(trader_id, quantity, time)
        self.price = np.inf if quantity > 0 else -np.inf

    def __repr__(self) -> str:
        return f"MKT V: {self.quantity:+}."

class LimitOrder(Order):
    def __init__(self, trader_id: int, quantity: int, time: Union[str, float], price: int) -> None:
        super().__init__(trader_id, quantity, time)
        self.price = price

    def __repr__(self) -> str:
        return f"LMT V: {self.quantity:+} P: {round(self.price)}."


