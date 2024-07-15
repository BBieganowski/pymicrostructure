"""Continous type markets module for financial markets."""

from microstructpy.markets.base import Market
from microstructpy.orders.market import MarketOrder
from microstructpy.orders.base import Order
import random
from typing import Union
from tqdm import tqdm


class ContinousOrderBookMarket(Market):
    """
    Represents a continuous order book market, extending the base Market class.

    This class implements a market with a continuous order book, where orders are
    matched continuously as they arrive. It maintains separate bid and ask order
    books, tracks order book snapshots, and handles order submission, matching,
    and execution.

    Attributes:
    -----------
    bid_ob : list
        A list of bid orders in the order book.
    ask_ob : list
        A list of ask orders in the order book.
    ob_snapshots : list
        A list of order book snapshots, capturing the state of the order book over time.
    midprices : list
        A list of tuples containing timestamp and midprice at each snapshot.
    cancellations : list
        A list to track cancelled orders.
    duration : int or None
        The duration of the market simulation in ticks.
    current_tick : int
        The current tick (time step) of the market simulation.

    Methods:
    --------
    submit_order(orders)
        Submit one or more orders to the market.
    drop_cancelled_orders()
        Remove cancelled orders from the order books.
    save_ob_state()
        Save the current state of the order book.
    match_orders()
        Match and execute orders in the order book.
    get_participant(trader_id)
        Retrieve a market participant by their trader ID.
    execute_trade(buyer, seller, price, volume, agressor_side)
        Execute a trade between two participants.
    update_order_status(order)
        Update the status of an order after matching.
    run(ticks=10)
        Run the market simulation for a specified number of ticks.

    """

    def __init__(self):
        """
        Initialize a new ContinousOrderBookMarket instance.

        Sets up empty order books, snapshots, midprices, and other tracking attributes.
        """
        super().__init__()
        self.bid_ob = []
        self.ask_ob = []
        self.ob_snapshots = []
        self.midprices = [(0, 0)]
        self.cancellations = []
        self.duration = None
        self.current_tick = 0

    def submit_order(self, orders: Union[Order, list[Order]]):
        """
        Submit one or more orders to the market.

        This method processes incoming orders, adds them to the appropriate order book,
        updates order statuses, and triggers order matching.

        Parameters:
        -----------
        orders : Union[Order, list[Order]]
            A single order or a list of orders to be submitted to the market.
        """
        if not isinstance(orders, list):
            orders = [orders]

        self.last_submission_time += 1
        for order in orders:
            if isinstance(order, MarketOrder):
                if order.volume > 0 and self.ask_ob == []:
                    order.status = "rejected"
                    break
                elif order.volume < 0 and self.bid_ob == []:
                    order.status = "rejected"
                    break

            order.time = self.last_submission_time

            if order.volume > 0:
                self.bid_ob.append(order)
            else:
                self.ask_ob.append(order)
            order.status = "active"
            submitting_trader = [
                participant
                for participant in self.participants
                if participant.trader_id == order.trader_id
            ][0]
            submitting_trader.orders.append(order)

        self.match_orders()
        self.save_ob_state()

    def drop_cancelled_orders(self):
        """Remove cancelled orders from both bid and ask order books."""
        self.bid_ob = [order for order in self.bid_ob if order.status != "canceled"]
        self.ask_ob = [order for order in self.ask_ob if order.status != "canceled"]

    def save_ob_state(self):
        """
        Save the current state of the order book.

        This method aggregates orders at each price level, creates a snapshot of the
        current order book state, and updates the midprice.
        """
        # Aggregate orders at the same price level
        bid_prices = set([order.price for order in self.bid_ob])
        bid_prices = sorted(bid_prices, reverse=True)
        ask_prices = set([order.price for order in self.ask_ob])
        bid_volumes = [
            sum([order.volume for order in self.bid_ob if order.price == price])
            for price in bid_prices
        ]
        ask_volumes = [
            sum([order.volume for order in self.ask_ob if order.price == price])
            for price in ask_prices
        ]
        bid_ob_snapshot = [
            {"price": price, "volume": volume}
            for price, volume in zip(bid_prices, bid_volumes)
        ]
        # sort
        bid_ob_snapshot.sort(key=lambda x: x["price"], reverse=True)
        ask_ob_snapshot = [
            {"price": price, "volume": volume}
            for price, volume in zip(ask_prices, ask_volumes)
        ]
        ask_ob_snapshot.sort(key=lambda x: x["price"])
        self.ob_snapshots.append(
            {
                "bid": bid_ob_snapshot,
                "ask": ask_ob_snapshot,
                "time": self.last_submission_time,
            }
        )
        if bid_ob_snapshot and ask_ob_snapshot:
            self.midprices.append(
                (
                    self.last_submission_time,
                    (bid_ob_snapshot[0]["price"] + ask_ob_snapshot[0]["price"]) / 2,
                )
            )
        elif self.current_tick == 0:
            self.midprices.append((self.last_submission_time, 0))
        else:
            # last not empty midprice
            self.midprices.append((self.last_submission_time, self.midprices[-1][1]))

    def match_orders(self):
        """
        Match and execute orders in the order book.

        This method sorts the order books, identifies matching orders, and executes
        trades when possible.
        """
        self.bid_ob.sort(key=lambda x: x.price, reverse=True)
        self.ask_ob.sort(key=lambda x: x.price)
        trade_counter = 0
        while (
            self.bid_ob and self.ask_ob and self.bid_ob[0].price >= self.ask_ob[0].price
        ):
            bid_order = self.bid_ob[0]
            ask_order = self.ask_ob[0]

            fill_price = (
                bid_order.price if bid_order.time < ask_order.time else ask_order.price
            )
            fill_volume = min(bid_order.active_volume, abs(ask_order.active_volume))
            agressor_side = -1 if bid_order.time < ask_order.time else 1

            buyer = self.get_participant(bid_order.trader_id)
            seller = self.get_participant(ask_order.trader_id)

            self.execute_trade(buyer, seller, fill_price, fill_volume, agressor_side)

            bid_order.filled += fill_volume
            ask_order.filled -= fill_volume

            self.update_order_status(bid_order)
            self.update_order_status(ask_order)

            if bid_order.status == "filled":
                self.bid_ob.pop(0)
            if ask_order.status == "filled":
                self.ask_ob.pop(0)
            trade_counter += 1
        
        # if market order remains in the order book, cancel rest
        for order in self.bid_ob + self.ask_ob:
            if isinstance(order, MarketOrder):
                order.status = "canceled"
                self.cancellations.append(order)
        self.drop_cancelled_orders()

    def get_participant(self, trader_id):
        """
        Retrieve a market participant by their trader ID.

        Parameters:
        -----------
        trader_id : str or int
            The unique identifier of the trader.

        Returns:
        --------
        Participant
            The participant object with the matching trader ID.
        """
        return next(p for p in self.participants if p.trader_id == trader_id)

    def execute_trade(self, buyer, seller, price, volume, agressor_side):
        """
        Execute a trade between two participants.

        This method updates participant positions, records trade information,
        and adds the trade to the market's trade history.

        Parameters:
        -----------
        buyer : Participant
            The participant buying in this trade.
        seller : Participant
            The participant selling in this trade.
        price : float
            The price at which the trade is executed.
        volume : int or float
            The volume of the asset being traded.
        agressor_side : int
            Indicates which side initiated the trade (1 for buy, -1 for sell).
        """
        buyer.position += volume
        seller.position -= volume

        trade_info = {
            "price": price,
            "volume": volume,
            "agressor_side": agressor_side,
            "time": self.last_submission_time,
        }

        buyer_trade = trade_info.copy()
        buyer_trade["volume"] = volume
        buyer.filled_trades.append(buyer_trade)

        seller_trade = trade_info.copy()
        seller_trade["volume"] = -volume
        seller.filled_trades.append(seller_trade)

        self.trade_history.append(trade_info)

    def update_order_status(self, order):
        """
        Update the status of an order after matching.

        Parameters:
        -----------
        order : Order
            The order whose status needs to be updated.
        """
        if order.volume == order.filled:
            order.status = "filled"
        else:
            order.status = "partial"

    def run(self, ticks=10):
        """
        Run the market simulation for a specified number of ticks.

        This method simulates the market activity for a given duration, updating
        participants and processing their actions in each tick.

        Parameters:
        -----------
        ticks : int, optional
            The number of ticks to run the simulation (default is 10).
        """
        self.duration = ticks
        for tick in tqdm(range(ticks)):
            self.current_tick = tick
            random.shuffle(self.participants)
            for participant in self.participants:
                participant.update()
        self.completed = True

    @property
    def best_bid(self):
        return self.bid_ob[0].price if self.bid_ob else None

    @property
    def best_ask(self):
        return self.ask_ob[0].price if self.ask_ob else None

    @property
    def midprice(self):
        if self.ask_ob and self.bid_ob:
            return (self.best_ask + self.best_bid) / 2
        else:
            return None

    @property
    def spread(self):
        return (
            self.best_ask - self.best_bid
            if self.best_bid is not None and self.best_ask is not None
            else None
        )

    def get_recent_trades(self, n=10):
        return (
            self.trade_history[-n:]
            if len(self.trade_history) > n
            else self.trade_history
        )
