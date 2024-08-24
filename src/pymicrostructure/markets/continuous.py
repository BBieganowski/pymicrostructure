"""Continuous type markets module for financial markets."""

from pymicrostructure.markets.base import Market
from pymicrostructure.orders.market import MarketOrder
from pymicrostructure.orders.base import Order
from pymicrostructure.traders.base import Trader
from operator import itemgetter, attrgetter
import random
from typing import Union, List, Dict, Any, Optional, Tuple
from tqdm import tqdm
from dill import load, dump
from collections import defaultdict


class ContinuousDoubleAuction(Market):
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
    execute_trade(buyer, seller, price, volume, aggressor_side)
        Execute a trade between two participants.
    update_order_status(order)
        Update the status of an order after matching.
    run(ticks=10)
        Run the market simulation for a specified number of ticks.

    """

    def __init__(self, initial_fair_price: int = 100):
        """
        Initialize a new ContinuousDoubleAuction instance.

        Sets up empty order books, snapshots, midprices, and other tracking attributes.
        """
        super().__init__()
        self.bid_ob: List[Order] = []
        self.ask_ob: List[Order] = []
        self.ob_snapshots: List[Dict[str, Any]] = []
        self.midprices: List[Tuple[int, float]] = [(0, 0)]
        self.cancellations: List[Order] = []
        self.duration: Optional[int] = None
        self.current_tick: int = 0
        self.initial_fair_price: int = initial_fair_price
        self.news_arrival_rate: float = 0.1
        self.good_news_prob: float = 0.5
        self.news_history: List[int] = [0]
        self.msg_history: List[Tuple[int, str, Any]] = []

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
            submitting_trader = self.get_participant(order.trader_id)
            if isinstance(order, MarketOrder):
                if order.volume > 0 and not self.ask_ob:
                    self.msg_history.append(
                        (self.last_submission_time, "REJECT", order)
                    )

                    order.status = "rejected"
                    submitting_trader.inactive_orders.append(order)
                    break
                elif order.volume < 0 and not self.bid_ob:
                    self.msg_history.append(
                        (self.last_submission_time, "REJECT", order)
                    )
                    order.status = "rejected"
                    submitting_trader.inactive_orders.append(order)
                    break

            order.time = self.last_submission_time
            self.msg_history.append((self.last_submission_time, "ADD", order))

            if order.volume > 0:
                self.bid_ob.append(order)
            else:
                self.ask_ob.append(order)
            order.status = "active"
            try:
                submitting_trader = next(
                    participant
                    for participant in self.participants
                    if participant.trader_id == order.trader_id
                )
                submitting_trader.active_orders.append(order)
            except StopIteration:
                raise ValueError(f"No trader found with ID {order.trader_id}")

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
        from collections import defaultdict

        bid_volumes = defaultdict(int)
        ask_volumes = defaultdict(int)

        for order in self.bid_ob:
            bid_volumes[order.price] += order.volume
        for order in self.ask_ob:
            ask_volumes[order.price] += order.volume

        bid_ob_snapshot = [
            {"price": price, "volume": volume} for price, volume in bid_volumes.items()
        ]
        ask_ob_snapshot = [
            {"price": price, "volume": volume} for price, volume in ask_volumes.items()
        ]

        bid_ob_snapshot.sort(key=lambda x: x["price"], reverse=True)
        ask_ob_snapshot.sort(key=lambda x: x["price"])

        self.ob_snapshots.append(
            {
                "bid": bid_ob_snapshot,
                "ask": ask_ob_snapshot,
                "time": self.last_submission_time,
            }
        )

        if bid_ob_snapshot and ask_ob_snapshot:
            new_midprice = (
                bid_ob_snapshot[0]["price"] + ask_ob_snapshot[0]["price"]
            ) / 2
        elif self.current_tick == 0:
            new_midprice = 0
        else:
            new_midprice = self.midprices[-1][1]

        self.midprices.append((self.last_submission_time, new_midprice))

    def match_orders(self):
        """
        Match and execute orders in the order book.

        This method sorts the order books, identifies matching orders, and executes
        trades when possible.
        """
        self.bid_ob.sort(key=attrgetter("price"), reverse=True)
        self.ask_ob.sort(key=attrgetter("price"))
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
            aggressor_side = -1 if bid_order.time < ask_order.time else 1

            buyer = self.get_participant(bid_order.trader_id)
            seller = self.get_participant(ask_order.trader_id)

            self.execute_trade(buyer, seller, fill_price, fill_volume, aggressor_side)

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
        try:
            return next(p for p in self.participants if p.trader_id == trader_id)
        except StopIteration:
            raise ValueError(f"No trader found with ID {trader_id}")

    def execute_trade(
        self,
        buyer: Trader,
        seller: Trader,
        price: float,
        volume: Union[int, float],
        aggressor_side: int,
    ) -> None:
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
        aggressor_side : int
            Indicates which side initiated the trade (1 for buy, -1 for sell).
        """
        buyer.position += volume
        seller.position -= volume

        trade_info = {
            "price": price,
            "volume": volume,
            "aggressor_side": aggressor_side,
            "time": self.last_submission_time,
        }

        buyer_trade = trade_info.copy()
        buyer_trade["volume"] = volume
        buyer.filled_trades.append(buyer_trade)

        seller_trade = trade_info.copy()
        seller_trade["volume"] = -volume
        seller.filled_trades.append(seller_trade)

        self.msg_history.append(
            (
                self.last_submission_time,
                "TRADE",
                f"{trade_info['volume']} @ {trade_info['price']}, AGG: {trade_info['aggressor_side']}",
            )
        )
        self.trade_history.append(trade_info)

    def update_order_status(self, order: Order):
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

    def run(self, ticks: int = 10):
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

            # News Arrival
            if random.random() < self.news_arrival_rate:
                self.news_history.append(
                    1 if random.random() < self.good_news_prob else -1
                )
            else:
                self.news_history.append(0)

            random.shuffle(self.participants)
            for participant in self.participants:
                participant.update()
        self.completed = True

    @property
    def best_bid(self) -> Optional[float]:
        return self.bid_ob[0].price if self.bid_ob else None

    @property
    def best_ask(self) -> Optional[float]:
        return self.ask_ob[0].price if self.ask_ob else None

    @property
    def midprice(self) -> Optional[float]:
        if self.ask_ob and self.bid_ob:
            return (self.best_ask + self.best_bid) / 2
        else:
            return None

    @property
    def spread(self) -> Optional[float]:
        return (
            self.best_ask - self.best_bid
            if self.best_bid is not None and self.best_ask is not None
            else None
        )

    def get_recent_trades(self, n: int = 10) -> List[dict]:
        return (
            self.trade_history[-n:]
            if len(self.trade_history) > n
            else self.trade_history
        )

    def save(self, filename) -> None:
        with open(filename, "wb") as f:
            dump(self, f)

    @staticmethod
    def load(filename: str) -> "ContinuousDoubleAuction":
        with open(filename, "rb") as f:
            return load(f)
