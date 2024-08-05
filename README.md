# PyMicrostructure

pymicrostructure is a powerful Python library for simulating and analyzing financial market microstructure. It provides a flexible framework for modeling various market participants, implementing trading strategies, and evaluating market performance metrics.

## Table of Contents

1. [Features](#features)
2. [Installation](#installation)
3. [Quick Start](#quick-start)
4. [Documentation](#documentation)
5. [Examples](#examples)
6. [Contributing](#contributing)
7. [License](#license)

## Features

- Flexible market simulation framework
- Various trader types (e.g., informed traders, noise traders, market makers)
- Customizable trading strategies
- Comprehensive set of market performance metrics
- Order book visualization tools
- Easy-to-use API for creating and running simulations

### Key Components

- **Markets**: Implement different market models (e.g., continuous double auction)
- **Traders**: Model various types of market participants
- **Orders**: Support for different order types (e.g., market orders, limit orders)
- **Strategies**: Implement and test different trading strategies
- **Metrics**: Analyze market efficiency, liquidity, and other performance indicators

## Installation

To install pymicrostructure, run the following command:

```bash
pip install pymicrostructure
```

## Quick Start

Here's a simple example to get you started with pymicrostructure:

```python
from pymicrostructure.markets.continuous import ContinuousDoubleAuction
from pymicrostructure.traders.market_maker import *
from pymicrostructure.traders.informed import *
from pymicrostructure.traders.noise import *
from pymicrostructure.traders.strategy import *

from pymicrostructure.visualization.summary import participant_comparison, price_path
from pymicrostructure.metrics.trader import participants_report

market   = ContinuousDoubleAuction(initial_fair_price=1000)
mm       = BaseMarketMaker(market,
                           fair_price_strategy=OrderFlowMagnitudeFairPrice(window=10, aggressiveness=1),
                           volume_strategy=MaxFractionVolume(fraction=0.1), 
                           spread_strategy=OrderFlowImbalanceSpread(window=5, aggressiveness=10, min_halfspread=3),
                           max_inventory=1000)

informed = TWAPInformedTrader(market)
noise    = NoiseTrader(market, submission_rate=1, volume_size=lambda:np.random.randint(1, 5))

market.run(300)
participant_comparison(market.participants)
price_path(market)
```

## Documentation

For detailed documentation, please visit our [documentation site](https://pymicrostructure.readthedocs.io).

## Examples

You can find more examples in the `examples/` directory of this repository. These examples cover various scenarios and use cases, such as:

- Implementing custom trading strategies
- Analyzing market liquidity
- Visualizing order book dynamics
- Comparing performance of different trader types

## Contributing

We welcome contributions to pymicrostructure! Please see our [CONTRIBUTING.md](CONTRIBUTING.md) file for details on how to contribute, report issues, or suggest enhancements.

## License

pymicrostructure is released under the MIT License. See the [LICENSE](LICENSE) file for details.