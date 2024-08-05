from typing import Callable
from microstructpy.traders.base import Trader
from microstructpy.markets.continuous import ContinuousDoubleAuction
from microstructpy.traders.market_maker import BaseMarketMaker
from microstructpy.traders.noise import NoiseTrader
from microstructpy.traders.informed import BaseInformedTrader
from microstructpy.traders.ensemble import ensemble_traders
import src.microstructpy.traders.strategy as pol
import numpy as np

def create_simple_market(initial_fair_price: int = 1000) -> ContinuousDoubleAuction:
    """
    Creates a simple market with a single market maker and a noise trader.

    Args:
        initial_fair_price (int): The initial fair price for the market.

    Returns:
        ContinuousDoubleAuction: A market instance with configured traders.
    """
    market = ContinuousDoubleAuction(initial_fair_price=initial_fair_price)
    
    mm = BaseMarketMaker(
        market=market,
        fair_price_strategy=pol.fairprice_orderflow_sign(window=10, agressiveness=1),
        spread_strategy=pol.spread_mm_orderflow_imbalance(10, 10),
        volume_strategy=pol.volume_mm_max_fraction(fraction=0.2),
        max_inventory=1000,
    )
    
    nt = NoiseTrader(
        market=market,
        submission_rate=1,
        volume_size=lambda: np.random.randint(1, 50),
    )

    market.participants = [mm, nt]
    return market

def create_kyle_market(initial_fair_price: int = 1000) -> ContinuousDoubleAuction:
    """
    Creates a Kyle-style market with one noise trader, one market maker, and one informed trader.

    Args:
        initial_fair_price (int): The initial fair price for the market.

    Returns:
        ContinuousDoubleAuction: A market instance with configured traders.
    """
    market = ContinuousDoubleAuction(initial_fair_price=initial_fair_price)
    
    mm = BaseMarketMaker(
        market=market,
        fair_price_strategy=pol.fairprice_orderflow_sign(window=20, agressiveness=1),
        spread_strategy=pol.spread_mm_orderflow_imbalance(10, 40),
        volume_strategy=pol.volume_mm_max_fraction(fraction=0.2),
        max_inventory=1500,
    )
    
    nt = NoiseTrader(
        market=market, 
        submission_rate=1, 
        volume_size=lambda: np.random.randint(1, 50)
    )

    it = BaseInformedTrader(
        market=market,
        price_strategy=pol.fairprice_constant(fair_price=1050),
        volume_strategy=pol.volume_informed_constant(20),
    )

    market.participants = [mm, nt, it]
    return market

# Usage examples:
simple_market = create_simple_market()
kyle_market = create_kyle_market()