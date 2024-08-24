"""Base class for traders in a market simulation."""

import numpy as np
import random
from typing import Type
from pymicrostructure.markets.base import Market
from pymicrostructure.orders.market import MarketOrder
from pymicrostructure.orders.limit import LimitOrder
from pymicrostructure.utils.utils import protect


class Trader(
    metaclass=protect(
        "cancel_orders_by_side", "cancel_order_by_id", "cancel_all_orders"
    )
):
    """
    Represents a trader in a financial market.

    This class serves as a base class for specific trader implementations. It provides
    the basic structure for managing orders, trades, and interactions with the market.

    Attributes:
    -----------
    market : Market
        The market instance in which the trader participates.
    orders : list
        A list of orders submitted by the trader.
    filled_trades : list
        A list of trades that have been executed for the trader.
    position : int or float
        The current position of the trader in the market.
    include_in_results : bool
        Flag indicating whether to include this trader in result calculations.
    trader_id : int
        A unique identifier for the trader within the market.

    Methods:
    --------
    cancel_orders(side)
        Cancel active or partially filled orders on a specific side.
    cancel_all_orders()
        Cancel all active or partially filled orders.
    submit_order()
        A method to be implemented by subclasses for submitting orders to the market.
    """

    def __init__(
        self, market: Market, name: str = None, include_in_results=True
    ) -> None:
        """
        Initialize a new Trader instance.

        Parameters:
        -----------
        market : Market
            The market instance in which the trader will participate.
        name : str, optional
            The name of the trader (default is None).
        include_in_results : bool, optional
            Whether to include this trader in result calculations (default is True).
        """
        self.market = market
        self.orders = []
        self.active_orders = []
        self.inactive_orders = []
        self.filled_trades = []
        self.position = 0
        self.include_in_results = include_in_results
        self.fair_price = market.initial_fair_price
        self.market.participants.append(self)
        self.trader_id = self.market.participants.index(self)
        self.name = name

    def cancel_order_by_id(self, order_id: int) -> None:
        """
        Cancel an order by its unique identifier.

        Parameters:
        -----------
        order_id : int
            The unique identifier of the order to cancel.
        """
        for order in self.active_orders:
            if order.id == order_id:
                order.status = "canceled"
                self.market.msg_history.append((self.trader_id, "CANCEL", order))
                self.market.cancellations.append(order)
                self.active_orders.remove(order)
                self.inactive_orders.append(order)
                break
        self.market.drop_cancelled_orders()

    def cancel_orders_by_side(self, side: str) -> None:
        """
        Cancel all active or partially filled orders on a specific side.

        Parameters:
        -----------
        side : str
            The side of the market (either 'buy' or 'sell') on which to cancel orders.
        """
        for order in self.active_orders:
            if order.side == side:
                order.status = "canceled"
                self.market.msg_history.append((self.trader_id, "CANCEL", order))
                self.market.cancellations.append(order)
                self.inactive_orders.append(order)
        self.active_orders = [o for o in self.active_orders if o.status == "active"]
        self.market.drop_cancelled_orders()

    def cancel_all_orders(self) -> None:
        """Cancel all active or partially filled orders for this trader."""
        for order in self.active_orders:
            order.status = "canceled"
            self.market.msg_history.append((self.trader_id, "CANCEL", order))
            self.market.cancellations.append(order)
            self.inactive_orders.append(order)
        self.active_orders = []
        self.market.drop_cancelled_orders()
