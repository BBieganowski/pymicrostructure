import pytest
from unittest.mock import MagicMock, patch
from pymicrostructure.markets.continuous import ContinuousDoubleAuction
from pymicrostructure.orders.limit import LimitOrder
from pymicrostructure.traders.market_maker import *


@pytest.fixture
def mock_market():
    return MagicMock(spec=ContinuousDoubleAuction(initial_fair_price=1000))


@pytest.fixture
def mock_fair_price_strategy():
    return MagicMock(return_value=100)


@pytest.fixture
def mock_volume_strategy():
    return MagicMock(return_value=(50, -50))


@pytest.fixture
def mock_spread_strategy():
    return MagicMock(return_value=(-1, 1))


def test_base_market_maker_initialization(
    mock_market, mock_fair_price_strategy, mock_volume_strategy, mock_spread_strategy
):
    mm = BaseMarketMaker(
        market=mock_market,
        fair_price_strategy=mock_fair_price_strategy,
        volume_strategy=mock_volume_strategy,
        spread_strategy=mock_spread_strategy,
        max_inventory=1000,
        name="TestMM",
    )

    assert mm.market == mock_market
    assert mm.fair_price_strategy == mock_fair_price_strategy
    assert mm.volume_strategy == mock_volume_strategy
    assert mm.spread_strategy == mock_spread_strategy
    assert mm.max_inventory == 1000
    assert mm.name == "TestMM"


def test_base_market_maker_update(
    mock_market, mock_fair_price_strategy, mock_volume_strategy, mock_spread_strategy
):
    mm = BaseMarketMaker(
        market=mock_market,
        fair_price_strategy=mock_fair_price_strategy,
        volume_strategy=mock_volume_strategy,
        spread_strategy=mock_spread_strategy,
        max_inventory=1000,
    )

    mm.update()

    assert mm.fair_price == 100
    mock_market.submit_order.assert_called_once()
    orders = mock_market.submit_order.call_args[0][0]
    assert len(orders) == 2
    assert isinstance(orders[0], LimitOrder)
    assert isinstance(orders[1], LimitOrder)
    assert orders[0].volume == 50
    assert orders[0].price == 99
    assert orders[1].volume == -50
    assert orders[1].price == 101


def test_dummy_market_maker(mock_market):
    mm = DummyMarketMaker(market=mock_market, name="DummyMM")

    assert isinstance(mm, BaseMarketMaker)
    assert mm.name == "DummyMM"
    assert mm.max_inventory == 1000

    mm.update()
    mock_market.submit_order.assert_called_once()


@patch("pymicrostructure.traders.market_maker.OrderFlowSignFairPrice")
def test_kyle_market_maker(mock_fair_price, mock_market):
    mm = KyleMarketMaker(market=mock_market, name="KyleMM")

    assert isinstance(mm, BaseMarketMaker)
    assert mm.name == "KyleMM"
    assert mm.max_inventory == 1000

    mock_fair_price.assert_called_once_with(window=5, aggressiveness=2)


@patch("pymicrostructure.traders.market_maker.OrderFlowMagnitudeFairPrice")
@patch("pymicrostructure.traders.market_maker.MaxFractionVolume")
@patch("pymicrostructure.traders.market_maker.OrderFlowImbalanceSpread")
def test_adaptive_market_maker(mock_spread, mock_volume, mock_fair_price, mock_market):
    mm = AdaptiveMarketMaker(market=mock_market, name="AdaptiveMM")

    assert isinstance(mm, BaseMarketMaker)
    assert mm.name == "AdaptiveMM"
    assert mm.max_inventory == 1000

    mock_fair_price.assert_called_once_with(window=10, aggressiveness=1)
    mock_volume.assert_called_once_with(0.1)
    mock_spread.assert_called_once_with(window=10, aggressiveness=5, min_halfspread=5)
