# %%
from microstructpy.markets.continous import ContinousOrderBookMarket
from microstructpy.traders.noise import NoiseTrader
from microstructpy.traders.market_maker import MarketMaker, BayesianMarketMaker
from microstructpy.traders.informed import InformedTrader, TWAPTrader
from microstructpy.visualization.summary import participant_comparison, price_path
from microstructpy.metrics.trader_metrics import *

import time
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

# %%
market = ContinousOrderBookMarket()


# %%
def noise_volume():
    return np.random.normal(5, 5)


# %%
liq_trader = NoiseTrader(
    1, market, submission_rate=1, volume_size=lambda: np.random.normal(5, 5)
)
dealer = BayesianMarketMaker(2, market, initial_fair_value=100)
dealer2 = BayesianMarketMaker(5, market, initial_fair_value=100, spread=4)
inf_trader = TWAPTrader(3, market, position_target=500, target_price=120)

# %%
market.run(1000)

# %%
participant_comparison(market.participants)
price_path(market)

# %%
participants_report(market.participants)

# %%
plt.plot([x[1] for x in market.midprices if x[1] > 0])

# %%
market.midprices

# %%
market.ob_snapshots[-10:]

# %%
