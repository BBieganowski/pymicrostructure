import pytest
from unittest.mock import MagicMock, patch
from pymicrostructure.markets.continuous import ContinuousDoubleAuction
from pymicrostructure.orders.market import MarketOrder
from pymicrostructure.traders.informed import *


@pytest.fixture
def mock_market():
    return MagicMock(spec=ContinuousDoubleAuction(initial_fair_price=1000))


def test_base_informed_trader_initialization(mock_market):
    trader = BaseInformedTrader(
        market=mock_market,
        fair_price_strategy=lambda x: 1000,
        volume_strategy=lambda x: (10, 10),
        max_inventory=500,
        name="Test Trader",
    )

    assert trader.market == mock_market
    assert trader.fair_price_strategy(trader) == 1000
    assert trader.volume_strategy(trader) == (10, 10)
    assert trader.max_inventory == 500
    assert trader.name == "Test Trader"


def test_base_informed_trader_update_sell(mock_market):
    mock_market.best_bid = 1100
    mock_market.best_ask = None

    trader = BaseInformedTrader(
        market=mock_market,
        fair_price_strategy=lambda x: 1000,
        volume_strategy=lambda x: (10, 20),
        max_inventory=500,
        name="Test Trader",
    )

    trader.update()

    mock_market.submit_order.assert_called_once()
    submitted_order = mock_market.submit_order.call_args[0][0]
    assert isinstance(submitted_order, MarketOrder)
    assert submitted_order.volume == 20


def test_base_informed_trader_update_buy(mock_market):
    mock_market.best_bid = None
    mock_market.best_ask = 900

    trader = BaseInformedTrader(
        market=mock_market,
        fair_price_strategy=lambda x: 1000,
        volume_strategy=lambda x: (10, 20),
        max_inventory=500,
        name="Test Trader",
    )

    trader.update()

    mock_market.submit_order.assert_called_once()
    submitted_order = mock_market.submit_order.call_args[0][0]
    assert isinstance(submitted_order, MarketOrder)
    assert submitted_order.volume == 10


def test_base_informed_trader_update_no_action(mock_market):
    mock_market.best_bid = 950
    mock_market.best_ask = 1050

    trader = BaseInformedTrader(
        market=mock_market,
        fair_price_strategy=lambda x: 1000,
        volume_strategy=lambda x: (10, 20),
        max_inventory=500,
        name="Test Trader",
    )

    trader.update()

    mock_market.submit_order.assert_not_called()


if __name__ == "__main__":
    pytest.main()
