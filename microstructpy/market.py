from microstructpy.order import MarketOrder
import random

class Market:
    def __init__(self):
        self.orders       = []
        self.participants = []
        self.trade_history = []
    
    def submit_order(self, order):
        raise NotImplementedError("This method should be overridden by subclasses")

class ContinousOrderBookMarket(Market):
    def __init__(self):
        super().__init__()
        self.bid_ob = []
        self.ask_ob = []

    def submit_order(self, order):
        if isinstance(order, MarketOrder):
            if order.quantity > 0 and self.ask_ob == []:
                order.status = "rejected"
                print(f"REJECT {order}")
                return None
            elif order.quantity < 0 and self.bid_ob == []:
                order.status = "rejected"
                print(f"REJECT {order}")
                return None
        
        if order.quantity > 0:
            self.bid_ob.append(order)
        else:
            self.ask_ob.append(order)
        print(f"INSERT {order}")
        order.status = "active"
        submitting_trader = [participant for participant in self.participants if participant.trader_id == order.trader_id][0]
        submitting_trader.orders.append(order)
        self.match_orders()

    def visualize_order_book(self):
        # Visualize the order book
        print("\n\n")
        for order in self.ask_ob:
            print(order)
        print("="*20)
        for order in self.bid_ob:
            print(order)
        print("\n\n")

    def match_orders(self):
        # Logic to match orders in the order book
        self.bid_ob = sorted(self.bid_ob, key=lambda x: x.price, reverse=True)
        self.ask_ob = sorted(self.ask_ob, key=lambda x: x.price)
        self.visualize_order_book() 
        if self.bid_ob and self.ask_ob:
            while self.bid_ob[0].price >= self.ask_ob[0].price:
                if self.bid_ob[0].quantity == abs(self.ask_ob[0].quantity):
                    self.bid_ob[0].status = "filled"
                    self.ask_ob[0].status = "filled"
                    fill_volume = abs(self.bid_ob[0].quantity)
                    fill_price = self.bid_ob[0].price if self.bid_ob[0].time < self.ask_ob[0].time else self.ask_ob[0].price
                    self.bid_ob.pop(0)
                    self.ask_ob.pop(0)
                elif self.bid_ob[0].quantity > abs(self.ask_ob[0].quantity):
                    self.bid_ob[0].quantity += self.ask_ob[0].quantity
                    self.ask_ob[0].status = "filled"
                    self.bid_ob[0].status = "partial"
                    fill_volume = abs(self.ask_ob[0].quantity)
                    fill_price = self.bid_ob[0].price if self.bid_ob[0].time < self.ask_ob[0].time else self.ask_ob[0].price
                    self.ask_ob.pop(0)
                else:
                    self.ask_ob[0].quantity += self.bid_ob[0].quantity
                    self.bid_ob[0].status = "filled"
                    self.ask_ob[0].status = "partial"
                    fill_volume = abs(self.bid_ob[0].quantity)
                    fill_price = self.bid_ob[0].price if self.bid_ob[0].time < self.ask_ob[0].time else self.ask_ob[0].price
                    self.bid_ob.pop(0)
                print(f"TRADE: {fill_volume} @ {fill_price}") 
                self.trade_history.append((fill_price, int(fill_volume)))
                if self.bid_ob == [] or self.ask_ob == []:
                    break


    def run(self, ticks=10):
        for tick in range(ticks):
            print(tick)
            random.shuffle(self.participants)
            for participant in self.participants:
                participant.update()
            
