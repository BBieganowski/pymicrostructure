import pytest
from unittest.mock import Mock, patch
import numpy as np
from pymicrostructure.markets.continuous import ContinuousDoubleAuction
from pymicrostructure.orders.market import MarketOrder
from pymicrostructure.traders.noise import (
    NoiseTrader,
)  # Assuming the NoiseTrader class is in trader.py


@pytest.fixture
def mock_market():
    return Mock(ContinuousDoubleAuction(100))


@pytest.fixture
def noise_trader(mock_market):
    return NoiseTrader(market=mock_market)


def test_noise_trader_initialization(mock_market):
    trader = NoiseTrader(market=mock_market)
    assert trader.market == mock_market
    assert trader.submission_rate == 1.00
    assert trader.volume_size == 1


def test_noise_trader_custom_initialization(mock_market):
    def custom_volume():
        return 5

    trader = NoiseTrader(
        market=mock_market, submission_rate=0.5, volume_size=custom_volume
    )
    assert trader.market == mock_market
    assert trader.submission_rate == 0.5
    assert trader.volume_size == custom_volume


def test_get_volume_constant(noise_trader):
    assert noise_trader._get_volume() == 1


def test_get_volume_callable(mock_market):
    def custom_volume():
        return 5

    trader = NoiseTrader(mock_market, volume_size=custom_volume)
    assert trader._get_volume() == 5


@patch("numpy.random.rand")
def test_update_submits_order(mock_rand, noise_trader):
    mock_rand.return_value = 0.5  # Ensure order submission
    with patch("random.choice", return_value=1):
        noise_trader.update()

    noise_trader.market.submit_order.assert_called_once()
    submitted_order = noise_trader.market.submit_order.call_args[0][0]
    assert isinstance(submitted_order, MarketOrder)
    assert submitted_order.trader_id == noise_trader.trader_id
    assert submitted_order.volume == 1 or submitted_order.volume == -1


@patch("numpy.random.rand")
def test_update_no_submission(mock_rand, noise_trader):
    mock_rand.return_value = 1.0  # Ensure no order submission
    noise_trader.update()
    noise_trader.market.submit_order.assert_not_called()


def test_update_zero_volume(mock_market):
    trader = NoiseTrader(market=mock_market, volume_size=lambda: 0)

    trader.update()
    mock_market.submit_order.assert_not_called()


@patch("numpy.random.rand")
def test_update_custom_volume(mock_rand, mock_market):
    mock_rand.return_value = 0.5  # Ensure order submission
    trader = NoiseTrader(market=mock_market, volume_size=lambda: 10)

    with patch("random.choice", return_value=-1):
        trader.update()

    mock_market.submit_order.assert_called_once()
    submitted_order = mock_market.submit_order.call_args[0][0]
    assert submitted_order.volume == -10


@patch("numpy.random.rand")
def test_update_multiple_calls(mock_rand, noise_trader):
    noise_trader.submission_rate = 0.5
    mock_rand.side_effect = [0.5, 0.9, 0.3]

    for _ in range(3):
        noise_trader.update()

    assert noise_trader.market.submit_order.call_count == 1


if __name__ == "__main__":
    pytest.main()
