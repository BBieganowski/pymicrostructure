import pytest
from unittest.mock import Mock
import numpy as np
from pymicrostructure.traders.base import Trader

# Import the strategies you want to test
from pymicrostructure.traders.strategy import (
    ConstantFairPrice,
    OrderFlowSignFairPrice,
    OrderFlowMagnitudeFairPrice,
    NewsImpactFairPrice,
    NewsImpactExponentialFairPrice,
    MaxAllowedVolume,
    ConstantVolume,
    MaxFractionVolume,
    TimeWeightedVolume,
    ConstantSpread,
    OrderFlowImbalanceSpread,
)


@pytest.fixture
def mock_trader():
    trader = Mock(spec=Trader)
    trader.fair_price = 100
    trader.market = Mock()
    trader.max_inventory = 100
    trader.position = 20
    return trader


class TestFairPriceStrategies:
    def test_constant_fair_price(self, mock_trader):
        strategy = ConstantFairPrice(fair_price=150)
        assert strategy(mock_trader) == 150

    def test_order_flow_sign_fair_price(self, mock_trader):
        strategy = OrderFlowSignFairPrice(window=3, aggressiveness=2)
        mock_trader.market.get_recent_trades.return_value = [
            {"volume": 10, "aggressor_side": 1},
            {"volume": 5, "aggressor_side": -1},
            {"volume": 7, "aggressor_side": 1},
        ]
        assert strategy(mock_trader) == 102

    def test_order_flow_magnitude_fair_price(self, mock_trader):
        strategy = OrderFlowMagnitudeFairPrice(window=3, aggressiveness=2)
        mock_trader.market.get_recent_trades.return_value = [
            {"volume": 10, "aggressor_side": 1},
            {"volume": 5, "aggressor_side": -1},
            {"volume": 7, "aggressor_side": 1},
        ]
        assert strategy(mock_trader) == 103

    def test_news_impact_fair_price(self, mock_trader):
        strategy = NewsImpactFairPrice(agressiveness=5)
        mock_trader.market.news_history = [0.5]
        assert strategy(mock_trader) == 102

    def test_news_impact_exponential_fair_price(self, mock_trader):
        strategy = NewsImpactExponentialFairPrice(window=3, agressiveness=1)
        mock_trader.market.news_history = [0.1, 0.2, 0.3]
        mock_trader.market.current_tick = 3
        assert strategy(mock_trader) == 101


class TestVolumeStrategies:
    def test_max_allowed_volume(self, mock_trader):
        strategy = MaxAllowedVolume()
        assert strategy(mock_trader) == (80, -120)

    def test_constant_volume(self, mock_trader):
        strategy = ConstantVolume(volume=50)
        assert strategy(mock_trader) == (50, -50)

    def test_max_fraction_volume(self, mock_trader):
        strategy = MaxFractionVolume(fraction=0.5)
        assert strategy(mock_trader) == (40, -60)

    def test_time_weighted_volume(self, mock_trader):
        strategy = TimeWeightedVolume()
        mock_trader.market.duration = 100
        mock_trader.market.current_tick = 50
        mock_trader.market.best_bid = 90
        mock_trader.market.best_ask = 110
        mock_trader.fair_price = 100
        assert strategy(mock_trader) == (0, 0)
        mock_trader.fair_price = 120
        assert strategy(mock_trader) == (1, 0)


class TestSpreadStrategies:
    def test_constant_spread(self, mock_trader):
        strategy = ConstantSpread(halfspread=5)
        assert strategy(mock_trader) == (-5, 5)

    def test_order_flow_imbalance_spread(self, mock_trader):
        strategy = OrderFlowImbalanceSpread(
            window=3, aggressiveness=2, min_halfspread=1
        )
        mock_trader.market.get_recent_trades.return_value = [
            {"volume": 10, "aggressor_side": 1},
            {"volume": 5, "aggressor_side": -1},
            {"volume": 7, "aggressor_side": 1},
        ]
        assert strategy(mock_trader) == (-1, 1)


# Additional test cases
def test_order_flow_sign_fair_price_no_trades(mock_trader):
    strategy = OrderFlowSignFairPrice(window=3, aggressiveness=2)
    mock_trader.market.get_recent_trades.return_value = []
    assert strategy(mock_trader) == 100  # No change in fair price


def test_max_allowed_volume_at_max_position(mock_trader):
    mock_trader.position = 100  # At max inventory
    strategy = MaxAllowedVolume()
    assert strategy(mock_trader) == (0, -200)


def test_time_weighted_volume_last_tick(mock_trader):
    strategy = TimeWeightedVolume()
    mock_trader.market.duration = 100
    mock_trader.market.current_tick = 99  # Last tick
    mock_trader.fair_price = 120
    mock_trader.market.best_ask = 110
    mock_trader.market.best_bid = 90
    assert strategy(mock_trader) == (80, 0)  # All remaining volume
