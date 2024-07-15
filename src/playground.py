# %%
from microstructpy.markets.continous import ContinousOrderBookMarket
from microstructpy.traders.noise import *
from microstructpy.traders.market_maker import *
from microstructpy.traders.informed import *
from microstructpy.traders.ensemble import ensemble_traders
from microstructpy.visualization.summary import participant_comparison, price_path
from microstructpy.metrics.trader_metrics import *
from microstructpy.metrics.market import *
from functools import partial

import time
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import math

# %%
def noise_volume():
    return np.random.normal(5, 5)

# %%
market      = ContinousOrderBookMarket()

liq_trader  = NoiseTrader(market, submission_rate=1, volume_size=lambda: np.random.normal(5, 10))

dealer2     = BaseMarketMaker(market, fair_price_strategy=fairprice_of_sign,
                              spread_strategy            =spread_fixed,
                              volume_strategy            =volume_max_fraction,
                              initial_fair_price=100, 
                              max_inventory=200)



# %%
market.run(5000)

# %%
participant_comparison(market.participants)
price_path(market)

# %%
participants_report(market.participants)

# %%
quoted_spread(market).plot(figsize=(15,5))
effective_spread(market, volume=50).plot(figsize=(15,5))
amihud_illiquidity(market).plot(figsize=(15,5))
order_book_depth(market).plot(figsize=(15,5))
order_flow_imbalance(market).plot(figsize=(15,5))

# %%
market.ob_snapshots[-20:]

# %%
ts, profit = profit_history(liq_trader)
ts[-1]

# %%
pd.Series(profit, index=ts)

# %%
len(profit)

# %%
math.isnan(profit[-1])

# %%



