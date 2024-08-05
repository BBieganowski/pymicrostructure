from microstructpy.traders.base import Trader
from functools import partial
from typing import Tuple, Callable
import numpy as np


##### Fairprice Strategies #####
from abc import ABC, abstractmethod
from typing import Tuple, Callable
import numpy as np

class Strategy(ABC):
    @abstractmethod
    def __call__(self, trader):
        pass

class FairPriceStrategy(Strategy):
    @abstractmethod
    def __call__(self, trader) -> int:
        pass

class VolumeStrategy(Strategy):
    @abstractmethod
    def __call__(self, trader) -> Tuple[int, int]:
        pass

class SpreadStrategy(Strategy):
    @abstractmethod
    def __call__(self, trader) -> Tuple[int, int]:
        pass

class ConstantFairPrice(FairPriceStrategy):
    def __init__(self, fair_price: int):
        self.fair_price = fair_price

    def __call__(self, trader) -> int:
        return self.fair_price

class OrderFlowSignFairPrice(FairPriceStrategy):
    def __init__(self, window: int, aggressiveness: int):
        self.window = window
        self.aggressiveness = aggressiveness

    def __call__(self, trader) -> int:
        orderflow = trader.market.get_recent_trades(self.window)
        orderflow = sum([trade["volume"] * trade["agressor_side"] for trade in orderflow])
        return trader.fair_price + self.aggressiveness * int(np.sign(orderflow))


class OrderFlowMagnitudeFairPrice(FairPriceStrategy):
    def __init__(self, window: int, aggressiveness: int):
        self.window = window
        self.aggressiveness = aggressiveness

    def __call__(self, trader) -> int:
        trades = trader.market.get_recent_trades(self.window)
        orderflow = sum([trade["volume"] * trade["agressor_side"] for trade in trades])
        total_volume = sum([trade["volume"] for trade in trades])
        indicator = orderflow / total_volume if total_volume != 0 else 0
        return trader.fair_price + int(indicator * self.aggressiveness * 3)


class NewsImpactFairPrice(FairPriceStrategy):
    def __init__(self, agressiveness: int):
        self.agressiveness = agressiveness

    def __call__(self, trader) -> int:
        news = trader.market.news_history[-1]
        if news == 0:
            return trader.fair_price
        return trader.fair_price + int(news * self.agressiveness)


class NewsImpactExponentialFairPrice(FairPriceStrategy):
    def __init__(self, window: int, agressiveness: int):
        self.window = window
        self.agressiveness = agressiveness

    def __call__(self, trader) -> int:
        if trader.market.current_tick < self.window:
            return trader.fair_price
        news = sum(trader.market.news_history[-self.window:]) / self.window
        return trader.fair_price + int(np.exp(news * self.agressiveness))



##### Volume Strategies #####

class MaxAllowedVolume(VolumeStrategy):
    def __init__(self) -> None:
        super().__init__()

    def __call__(self, trader) -> Tuple[int, int]:
        bid_volume = trader.max_inventory - trader.position
        ask_volume = trader.max_inventory + trader.position
        return bid_volume, -ask_volume

class ConstantVolume(VolumeStrategy):
    def __init__(self, volume: int) -> None:
        self.volume = volume

    def __call__(self, trader) -> Tuple[int, int]:
        max_bid = trader.max_inventory - trader.position
        max_ask = trader.max_inventory + trader.position
        return min(self.volume, max_bid), -min(self.volume, max_ask)


class MaxFractionVolume(VolumeStrategy):
    def __init__(self, fraction: float) -> None:
        self.fraction = fraction

    def __call__(self, trader) -> Tuple[int, int]:
        bid_volume = int((trader.max_inventory - trader.position) * self.fraction)
        ask_volume = int((trader.max_inventory + trader.position) * self.fraction)
        return bid_volume, -ask_volume


class TimeWeightedVolume(VolumeStrategy):       
    def __call__(self, trader) -> Tuple[int, int]:
        self.duration = trader.market.duration
        fairprice = trader.fair_price
        if fairprice is None:
            return 0, 0
        
        if trader.market.best_bid:
            if fairprice < trader.market.best_bid:
                volume_left = -trader.max_inventory - trader.position
                time_left = self.duration - trader.market.current_tick
                return int(volume_left / time_left), 0
        if trader.market.best_ask:
            if fairprice > trader.market.best_ask:
                volume_left = trader.max_inventory - trader.position
                time_left = self.duration - trader.market.current_tick
                return 0, int(volume_left / time_left)
        return 0, 0


#### Spread Strategies ####

class ConstantSpread(SpreadStrategy):
    def __init__(self, halfspread: int) -> None:
        self.halfspread = halfspread

    def __call__(self, trader) -> Tuple[int, int]:
        return -self.halfspread, self.halfspread

class OrderFlowImbalanceSpread(SpreadStrategy):
    def __init__(self, window: int, aggressiveness: int, min_halfspread: int) -> None:
        self.window = window
        self.aggressiveness = aggressiveness
        self.min_halfspread = min_halfspread

    def __call__(self, trader) -> Tuple[int, int]:
        trades = trader.market.get_recent_trades(self.window)
        orderflow = sum([trade["volume"] * trade["agressor_side"] for trade in trades])

        total_volume = sum([trade["volume"] for trade in trades])
        indicator = orderflow / total_volume if total_volume != 0 else 0
        bid_offset = min(int(indicator * self.aggressiveness), -self.min_halfspread)
        ask_offset = max(int(indicator * self.aggressiveness), self.min_halfspread)

        return bid_offset, ask_offset