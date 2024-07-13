from microstructpy.order import MarketOrder
import random

class Market:
    def __init__(self):
        self.orders       = []
        self.participants = []
        self.trade_history = []
        self.last_submission_time = 0
        self.completed = False

    def submit_order(self, order):
        raise NotImplementedError("This method should be overridden by subclasses")

class ContinousOrderBookMarket(Market):
    def __init__(self):
        super().__init__()
        self.bid_ob = []
        self.ask_ob = []
        self.ob_snapshots = []

    def submit_order(self, order):
        if isinstance(order, MarketOrder):
            if order.quantity > 0 and self.ask_ob == []:
                order.status = "rejected"
                return None
            elif order.quantity < 0 and self.bid_ob == []:
                order.status = "rejected"
                return None
        
        self.last_submission_time += 1
        order.time = self.last_submission_time

        if order.quantity > 0:
            self.bid_ob.append(order)
        else:
            self.ask_ob.append(order)
        order.status = "active"
        submitting_trader = [participant for participant in self.participants if participant.trader_id == order.trader_id][0]
        submitting_trader.orders.append(order)
        self.match_orders()
        self.save_ob_state()

    def save_ob_state(self):
        # Aggregate orders at the same price level
        bid_prices = set([order.price for order in self.bid_ob])
        bid_prices = sorted(bid_prices, reverse=True)
        ask_prices = set([order.price for order in self.ask_ob])
        bid_volumes = [sum([order.quantity for order in self.bid_ob if order.price == price]) for price in bid_prices]
        ask_volumes = [sum([order.quantity for order in self.ask_ob if order.price == price]) for price in ask_prices]
        bid_ob_snapshot = [{"price": price, "volume": volume} for price, volume in zip(bid_prices, bid_volumes)]
        ask_ob_snapshot = [{"price": price, "volume": volume} for price, volume in zip(ask_prices, ask_volumes)]
        self.ob_snapshots.append({"bid": bid_ob_snapshot, "ask": ask_ob_snapshot, 'time': self.last_submission_time})

        
    def match_orders(self):
        # Logic to match orders in the order book
        self.bid_ob = sorted(self.bid_ob, key=lambda x: x.price, reverse=True)
        self.ask_ob = sorted(self.ask_ob, key=lambda x: x.price)
        
        if self.bid_ob and self.ask_ob:
            while self.bid_ob[0].price >= self.ask_ob[0].price:
                if self.bid_ob[0].quantity == abs(self.ask_ob[0].quantity):
                    self.bid_ob[0].status = "filled"
                    self.ask_ob[0].status = "filled"

                    # update trader positions
                    buyer = [participant for participant in self.participants if participant.trader_id == self.bid_ob[0].trader_id][0]
                    seller = [participant for participant in self.participants if participant.trader_id == self.ask_ob[0].trader_id][0]
                    buyer.position += self.bid_ob[0].quantity
                    seller.position += self.ask_ob[0].quantity

                    fill_volume = abs(self.bid_ob[0].quantity)
                    fill_price = self.bid_ob[0].price if self.bid_ob[0].time < self.ask_ob[0].time else self.ask_ob[0].price
                    agressor_side =( self.bid_ob[0].time < self.ask_ob[0].time)*2 - 1
                    buyer.filled_trades.append({"price": fill_price, "volume": self.bid_ob[0].quantity, "agressor_side": agressor_side,
                                                "time": self.last_submission_time})
                    seller.filled_trades.append({"price": fill_price, "volume": self.ask_ob[0].quantity, "agressor_side": agressor_side,
                                                "time": self.last_submission_time})
                    self.bid_ob.pop(0)
                    self.ask_ob.pop(0)
                elif self.bid_ob[0].quantity > abs(self.ask_ob[0].quantity):
                    self.bid_ob[0].quantity += self.ask_ob[0].quantity
                    self.ask_ob[0].status = "filled"
                    self.bid_ob[0].status = "partial"

                    # update trader positions
                    buyer = [participant for participant in self.participants if participant.trader_id == self.bid_ob[0].trader_id][0]
                    seller = [participant for participant in self.participants if participant.trader_id == self.ask_ob[0].trader_id][0]
                    buyer.position += self.ask_ob[0].quantity
                    seller.position += self.ask_ob[0].quantity

                    fill_volume = abs(self.ask_ob[0].quantity)
                    fill_price = self.bid_ob[0].price if self.bid_ob[0].time < self.ask_ob[0].time else self.ask_ob[0].price
                    agressor_side =( self.bid_ob[0].time < self.ask_ob[0].time)*2 - 1
                    buyer.filled_trades.append({"price": fill_price, "volume": self.bid_ob[0].quantity, "agressor_side": agressor_side,
                                                "time": self.last_submission_time})
                    seller.filled_trades.append({"price": fill_price, "volume": self.ask_ob[0].quantity, "agressor_side": agressor_side,
                                                "time": self.last_submission_time})
                    self.ask_ob.pop(0)
                else:
                    self.ask_ob[0].quantity += self.bid_ob[0].quantity
                    self.bid_ob[0].status = "filled"
                    self.ask_ob[0].status = "partial"

                    # update trader positions
                    buyer = [participant for participant in self.participants if participant.trader_id == self.bid_ob[0].trader_id][0]
                    seller = [participant for participant in self.participants if participant.trader_id == self.ask_ob[0].trader_id][0]
                    buyer.position += self.bid_ob[0].quantity
                    seller.position += self.bid_ob[0].quantity
                    fill_volume = abs(self.bid_ob[0].quantity)
                    fill_price = self.bid_ob[0].price if self.bid_ob[0].time < self.ask_ob[0].time else self.ask_ob[0].price
                    agressor_side =( self.bid_ob[0].time < self.ask_ob[0].time)*2 - 1
                    buyer.filled_trades.append({"price": fill_price, "volume": self.bid_ob[0].quantity, "agressor_side": agressor_side,
                                                "time": self.last_submission_time})
                    seller.filled_trades.append({"price": fill_price, "volume": self.ask_ob[0].quantity, "agressor_side": agressor_side,
                                                "time": self.last_submission_time})
                    self.bid_ob.pop(0)
                trade = {"price": fill_price, "volume": fill_volume, "agressor_side": agressor_side,
                            "time": self.last_submission_time} 
                self.trade_history.append(trade)
                if self.bid_ob == [] or self.ask_ob == []:
                    break


    def run(self, ticks=10):
        for tick in range(ticks):
            random.shuffle(self.participants)
            for participant in self.participants:
                participant.update()
        self.completed = True 
