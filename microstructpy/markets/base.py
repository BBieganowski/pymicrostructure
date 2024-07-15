"""Base module for financial markets."""

from microstructpy.orders.market import MarketOrder
import random


class Market:
    """
    Represents a financial market with order management and trade history.

    This class serves as a base class for specific market implementations. It provides
    the basic structure for managing orders, market participants, and trade history.

    Attributes:
    -----------
    orders : list
        A list to store all orders submitted to the market.
    participants : list
        A list of all participants in the market.
    trade_history : list
        A chronological list of all trades executed in the market.
    last_submission_time : int or float
        The timestamp of the last order submission.
    completed : bool
        A flag indicating whether the market session is completed.

    Methods:
    --------
    submit_order(order)
        A method to be implemented by subclasses for submitting orders to the market.
    """

    def __init__(self):
        """
        Initialize a new Market.

        Cretes instance with empty lists for orders, participants,
        and trade history, and set initial values for last submission time and completion
        status.
        """
        self.orders = []
        self.participants = []
        self.trade_history = []
        self.last_submission_time = 0
        self.completed = False

    def submit_order(self, order):
        """
        Submit an order to the market.

        This method should be overridden by subclasses to implement specific order
        submission logic.

        Parameters:
        -----------
        order : object
            The order to be submitted to the market.

        Raises:
        -------
        NotImplementedError
            If this method is not overridden by a subclass.
        """
        raise NotImplementedError("This method should be overridden by subclasses")
