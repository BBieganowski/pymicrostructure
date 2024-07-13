from typing import Union
import numpy as np

class Order:
    def __init__(self, trader_id: int, quantity: int) -> None:
        if quantity == 0:
            raise ValueError("Order quantity must be non-zero.")
        self.trader_id  = trader_id
        self.quantity   = quantity
        self.time = None
        self.status     = "created"






