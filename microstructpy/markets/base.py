from microstructpy.orders.market import MarketOrder
import random


class Market:
    def __init__(self):
        self.orders = []
        self.participants = []
        self.trade_history = []
        self.last_submission_time = 0
        self.completed = False

    def submit_order(self, order):
        raise NotImplementedError("This method should be overridden by subclasses")
