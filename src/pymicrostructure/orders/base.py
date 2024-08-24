"""Base order class."""

from typing import Union
import numpy as np


class Order:
    """
    Represents a generic order.

    This class serves as a base class for specific order types. It provides the basic
    structure for managing order status and volume.

    Attributes:
    -----------
    trader_id : int
        The ID of the trader submitting the order.
    volume : int
        The volume of the order.
    time : int or float
        The timestamp of the order submission.
    status : str
        The status of the order.
    filled : int
        The volume of the order that has been filled.

    Methods:
    --------
    active_volume()
        Calculate the volume of the order that has not yet been filled.
    """

    _id_counter = 0

    def __init__(self, trader_id: int, volume: int) -> None:
        """Initialize a new Order."""
        if volume == 0:
            raise ValueError("Order volume must be non-zero.")
        self.trader_id = trader_id
        self.volume = volume
        self.time = None
        self.status = "created"
        self.filled = 0
        self.id = Order._id_counter
        Order._id_counter += 1

    @property
    def active_volume(self) -> int:
        """Calculate the volume of the order that has not yet been filled."""
        return self.volume - self.filled
