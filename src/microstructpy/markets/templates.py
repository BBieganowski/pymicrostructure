from microstructpy.traders.base import Trader
from microstructpy.markets.continous import ContinousDoubleAuction
from microstructpy.traders.market_maker import BaseMarketMaker
from microstructpy.traders.noise import NoiseTrader
from microstructpy.traders.informed import BaseInformedTrader
from microstructpy.traders.ensemble import ensemble_traders
import microstructpy.traders.policies as pol
import numpy as np

################ MARKET TEMPLATES ################

# Market with single market maker and noise trader
simple_market = ContinousDoubleAuction(initial_fair_price=1000)
siple_mm = BaseMarketMaker(market=simple_market,
                        fair_price_strategy=pol.fairprice_orderflow_sign(window=10, agressiveness=1),
                        spread_strategy=pol.spread_mm_orderflow_imbalance(10, 10),
                        volume_strategy=pol.volume_mm_max_fraction(fraction=0.2),
                        max_inventory=1000)
simple_nt = NoiseTrader(market=simple_market, submission_rate=1, 
                 volume_size=lambda: np.random.randint(1, 50))

# Market with one noise trader, one market maker, and one informed trader
kyle_market = ContinousDoubleAuction(initial_fair_price=1000)
kyle_mm = BaseMarketMaker(market=kyle_market,
                        fair_price_strategy=pol.fairprice_orderflow_sign(window=20, agressiveness=1),
                        spread_strategy=pol.spread_mm_orderflow_imbalance(10, 40),
                        volume_strategy=pol.volume_mm_max_fraction(fraction=0.2),
                        max_inventory=1500)
kyle_nt = NoiseTrader(market=kyle_market, submission_rate=1,
                    volume_size=lambda: np.random.randint(1, 50))


kyle_it = BaseInformedTrader(market=kyle_market,
                            price_strategy=pol.fairprice_constant(fair_price=1050),
                            volume_strategy=pol.volume_informed_constant(20))


