# User Guide

This section is a more detailed guide on how to use the PyMicrostructure package. It will cover how the package is structed, how to use the different modules, and how to run simulations.

## Basic Concepts

PyMicrostructure is designed with a modular, object-oriented architecture that allows for flexible and extensible market simulations. The core components of the package - Markets, Traders, and Strategies - interact in a well-defined manner to create a dynamic market environment.

### Markets
Markets are the central hubs of activity in PyMicrostructure. The primary market class is `ContinuousDoubleAuction`, which inherits from a base `Market` class.

Key characteristics:
- Maintains order books (bid and ask)
- Handles order matching and execution
- Keeps track of trade history and order book snapshots
- Manages the simulation timeline


### Traders
Traders are the actors in the market. Different types of traders (e.g., MarketMaker, NoiseTrader, InformedTrader) inherit from a base `Trader` class.

Key characteristics:
- Associated with a specific market
- Have their own trading logic (implemented in the `update()` method)
- Maintain their own state (position, orders, trades)

### Strategies

Strategies are modular components that define specific aspects of a trader's behavior. They are typically implemented as callable classes or functions.

Key characteristics:
- Can be easily swapped or combined to create complex trading behaviors
- Often focus on a specific aspect of trading (e.g., fair price calculation, spread determination, volume decision)

### Object Interactions

1. **Market-Trader Relationship:**
   - Traders are added to a market's `participants` list.
   - The market calls each trader's `update()` method during the simulation.
   - Traders submit orders to the market using the market's `submit_order()` method.

2. **Trader-Strategy Relationship:**
   - Traders use strategies to make decisions.
   - Strategies are passed to traders upon initialization or can be changed dynamically.
   - Traders call their strategies (which are callable objects) to determine actions.

3. **Strategy-Market Interaction:**
   - Strategies don't directly interact with the market.
   - Instead, they use market data provided by the trader to make decisions.

4. **Market-Order Interaction:**
   - Orders are objects (e.g., `LimitOrder`, `MarketOrder`) submitted to the market.
   - The market processes these orders, updates order books, and executes trades.

### Simulation Flow

1. A market is created.
2. Traders are instantiated with their respective strategies and added to the market.
3. The market's `run()` method is called to start the simulation.
4. For each time step:
   - The market updates its state (e.g., processes news events).
   - Each trader's `update()` method is called.
   - Traders use their strategies to make decisions and submit orders.
   - The market processes submitted orders, matches trades, and updates its state.
5. After the simulation, market data and trader performance can be analyzed.

### Extensibility

This architecture allows for easy extensibility:
- New market types can be created by inheriting from the base `Market` class.
- New trader types can be implemented by inheriting from the base `Trader` class.
- New strategies can be created as standalone callable objects.

## Markets - Detailed Guide


The markets module in PyMicrostructure is designed to simulate financial market mechanisms. Currently, it features the ContinuousDoubleAuction market, which models a continuous order book market commonly found in many financial exchanges.

### ContinuousDoubleAuction Market

The ContinuousDoubleAuction class represents a market where orders are continuously matched as they arrive. It maintains separate bid and ask order books and handles order submission, matching, and execution.


To create a new ContinuousDoubleAuction market:

```python
from pymicrostructure.markets.continuous import ContinuousDoubleAuction

market = ContinuousDoubleAuction(initial_fair_price=100)
```

The `initial_fair_price` parameter sets the starting price for the market.

Key Attributes:

- `bid_ob` and `ask_ob`: Lists containing bid and ask orders.
- `ob_snapshots`: List of order book snapshots over time.
- `midprices`: List of midprice values at each snapshot.
- `current_tick`: The current time step of the simulation.
- `news_history`: List tracking the arrival of market news.

Main Methods:

1. `submit_order(orders)`: Submit one or more orders to the market. Orders are added to the appropriate order book and matched if possible.
2. `match_orders()`: Match and execute orders in the order book. This method is called automatically after order submission.
3. `run(ticks)`: Run the market simulation for a specified number of ticks. This method updates all participants and processes their actions in each time step.
4. `save(filename)` and `load(filename)`: Save the current market state to a file or load a market state from a file.

Properties:

- `best_bid` and `best_ask`: The highest bid and lowest ask prices in the order book.
- `midprice`: The average of the best bid and best ask prices.
- `spread`: The difference between the best ask and best bid prices.


The market automatically manages the order book, including:

- Sorting orders by price (highest to lowest for bids, lowest to highest for asks).
- Removing filled or cancelled orders.
- Updating order statuses after matching.


When orders are matched, the `execute_trade()` method:

- Updates the positions of the buyer and seller.
- Records trade information in the market's trade history.
- Updates the traders' filled trades lists.


The market simulates some basic market dynamics:
- Random news arrivals (controlled by `news_arrival_rate` and `good_news_prob`).
- Random shuffling of participant order to avoid bias.


Features:
- The market supports both limit orders and market orders.
- Order book snapshots are saved at each time step, allowing for detailed analysis of market dynamics.
- The `get_recent_trades()` method allows retrieval of the most recent trades.

Best Practices:

1. Always initialize at least two traders (e.g., market makers and noise traders) before running the simulation.
2. Use the `run()` method to simulate market activity, rather than manually updating traders.
3. Utilize the saved order book snapshots and trade history for post-simulation analysis.
4. Consider using the save and load functionality for long simulations or to analyze specific market states.


## Market Makers


Market makers play a crucial role in providing liquidity to financial markets. In PyMicrostructure, market makers are implemented as sophisticated traders that continuously post buy and sell orders to profit from the bid-ask spread while managing their inventory risk.

### BaseMarketMaker

The `BaseMarketMaker` class serves as the foundation for all market maker implementations in PyMicrostructure. It encapsulates the core logic of a market maker's operation.

Key Components

1. **Fair Price Strategy**: Determines the market maker's estimate of the asset's true value.
2. **Spread Strategy**: Decides the width of the bid-ask spread.
3. **Volume Strategy**: Determines the quantity to be traded on each side.
4. **Max Inventory**: Limits the market maker's position to manage risk.

Operation Cycle

In each update cycle, the `BaseMarketMaker`:

1. Calculates the current fair price using its fair price strategy.
2. Determines the bid and ask offsets using its spread strategy.
3. Decides on the volumes to trade using its volume strategy.
4. Cancels all existing orders.
5. Submits new limit orders based on the calculated prices and volumes.

Specific Market Maker Implementations

### DummyMarketMaker

A simple market maker using constant strategies:

- Constant fair price
- Constant volume
- Constant spread

Useful for testing and basic simulations.

### KyleMarketMaker

Based on Kyle's model, this market maker:

- Adjusts fair price based on recent order flow
- Maintains constant volume and spread

Provides a more dynamic pricing strategy while keeping other parameters simple.

### AdaptiveMarketMaker

A more sophisticated market maker that adapts to market conditions:

- Adjusts fair price based on order flow magnitude
- Sets volume as a fraction of market volume
- Adjusts spread based on order flow imbalance


## Noise Traders

Noise Traders are a key component of financial market simulations. They add randomness and liquidity to the market by submitting random market orders at a fixed rate.

### NoiseTrader

The `NoiseTrader` class represents a simple noise trader that submits random market orders at a specified rate.

Inheritance
`NoiseTrader` inherits from the base `Trader` class.

Attributes:
- `market` (Market): The market instance in which the trader participates.
- `submission_rate` (float): The rate at which the trader submits orders.
- `volume_size` (int or Callable[[], int]): The size of the orders submitted by the trader.

Constructor:
```python
NoiseTrader(market: Market, submission_rate: float = 1.00, volume_size: Union[int, Callable[[], int]] = 1)
```

Parameters:
- `market` (Market): The market instance for the trader.
- `submission_rate` (float, optional): The rate of order submission. Default is 1.00.
- `volume_size` (int or Callable[[], int], optional): The volume size for orders. Can be a fixed integer or a callable that returns an integer. Default is 1.

Notes:
- The `NoiseTrader` submits market orders, which are immediately executed at the best available price.
- The trader's behavior is randomized:
  - It submits orders based on the `submission_rate` probability.
  - The order volume is determined by the `volume_size` attribute.
  - The order direction (buy or sell) is randomly chosen.
- This trader is useful for simulating market noise and providing baseline liquidity in market simulations.

## Informed Traders

The Informed Traders module is designed to simulate traders who have opinions about the future price of securities. These traders use various strategies to determine fair prices and trading volumes, making them more sophisticated than simple noise traders.

Informed traders are market participants who believe they have valuable information about the future price of a security. In real markets, these could be analysts, institutional investors, or traders with access to proprietary information. In our simulation, we model these traders with different strategies to reflect various trading styles and information sources.

### Base Informed Trader

The `BaseInformedTrader` class serves as the foundation for all informed traders in our system. It encapsulates the core behavior of an informed trader:

1. Determining a fair price for the security
2. Deciding on a trading volume
3. Placing market orders based on the comparison between the fair price and current market price

The base class is flexible, allowing for different strategies to be plugged in for fair price calculation and volume determination.

### Dummy Informed Trader

The `DummyInformedTrader` is the simplest type of informed trader. It's useful for basic simulations and testing.

- **Fair Price Strategy**: Uses a constant fair price (set to 1050 in this example)
- **Volume Strategy**: Always trades the maximum allowed volume
- **Behavior**: This trader will consistently try to buy when the market price is below 1050 and sell when it's above 1050, always trading at the maximum volume allowed.

### TWAP Informed Trader

The `TWAPInformedTrader` implements a Time-Weighted Average Price strategy, which is common in algorithmic trading.

- **Fair Price Strategy**: Uses the same constant fair price as the Dummy trader
- **Volume Strategy**: Employs a time-weighted approach to determine trading volume
- **Behavior**: This trader spreads out its trades over time, which can help to minimize market impact and achieve a better average price.

### News Informed Trader

The `NewsInformedTrader` simulates a trader who reacts to market news, representing a more dynamic and reactive trading style.

- **Fair Price Strategy**: Uses a news impact exponential model to adjust the fair price based on market news
- **Volume Strategy**: Uses the same time-weighted approach as the TWAP trader
- **Behavior**: This trader's fair price estimate changes in response to simulated news events, leading to more dynamic trading patterns.

### Key Concepts
1. **Fair Price**: The price at which the trader believes the security should be trading. This is the trader's internal valuation of the security.
2. **Volume Strategy**: Determines how much the trader is willing to buy or sell at any given time. This can be influenced by factors like time, current inventory, or market conditions.
3. **Market Orders**: Informed traders in this module use market orders, which are executed immediately at the best available price. This reflects the trader's confidence in their information and willingness to accept the current market price.
4. **Inventory Management**: Traders have a maximum inventory limit, preventing them from taking on unlimited positions.

Usage in Simulations

These informed traders can be used to create more realistic market simulations:

- Use `DummyInformedTrader` for simple scenarios or to provide a consistent price anchor.
- Implement `TWAPInformedTrader` to simulate more sophisticated execution strategies that aim to minimize market impact.
- Include `NewsInformedTrader` to add an element of unpredictability and responsiveness to external events in your market simulation.



## Strategies

The Strategies module is a crucial component of the `pymicrostructure` library, designed to provide various algorithms for all traders. These strategies determine how traders calculate fair prices, set trading volumes, and adjust spreads in response to market conditions.

The module defines three main types of strategies:

1. **Fair Price Strategies**: Determine the trader's estimate of the asset's true value.
2. **Volume Strategies**: Decide how much to buy or sell at any given time.
3. **Spread Strategies**: Set the difference between bid and ask prices.

Fair Price Strategies

Fair price strategies help traders estimate the true value of an asset. This estimate guides their trading decisions.

### Constant Fair Price

- **Behavior**: Always returns the same price
- **Use Case**: Simulating a trader with a fixed valuation or as a baseline for comparison

### Order Flow Sign Fair Price

- **Behavior**: Adjusts price based on the direction (sign) of recent trades
- **Use Case**: Simulating a trader who believes recent trade direction indicates future price movement

### Order Flow Magnitude Fair Price

- **Behavior**: Adjusts price based on the size and direction of recent trades
- **Use Case**: Simulating a trader who considers both trade size and direction as significant

### News Impact Fair Price

- **Behavior**: Adjusts price based on the latest news
- **Use Case**: Simulating a trader who reacts quickly to new information

### News Impact Exponential Fair Price

- **Behavior**: Adjusts price based on an exponential function of recent news
- **Use Case**: Simulating a trader who believes news has a compound effect on price

Volume Strategies

Volume strategies determine how much a trader is willing to buy or sell at any given time.

### Max Allowed Volume

- **Behavior**: Sets volume to the maximum allowed by inventory limits
- **Use Case**: Simulating an aggressive trader always willing to trade the maximum amount

### Constant Volume

- **Behavior**: Uses a fixed volume, subject to inventory constraints
- **Use Case**: Simulating a trader with a consistent trading size

### Max Fraction Volume

- **Behavior**: Sets volume as a fraction of the maximum allowed
- **Use Case**: Simulating a trader who scales their trading relative to their capacity

### Time Weighted Volume

- **Behavior**: Adjusts volume based on remaining time and market conditions
- **Use Case**: Simulating a trader trying to execute a large order over time (similar to TWAP strategy)

Spread Strategies

Spread strategies determine the difference between a trader's bid and ask prices.

### Constant Spread

- **Behavior**: Maintains a fixed spread around the fair price
- **Use Case**: Simulating a trader with a consistent risk appetite

### Order Flow Imbalance Spread

- **Behavior**: Adjusts spread based on recent order flow imbalance
- **Use Case**: Simulating a trader who widens spreads when order flow is unbalanced (indicating potential price movement)

### Key Concepts

1. **Fair Price**: The trader's estimate of the asset's true value, used as a reference for setting bid and ask prices.
2. **Order Flow**: The sequence and volume of buy and sell orders in the market, used to gauge market sentiment and potential price movements.
3. **Spread**: The difference between bid and ask prices, representing the trader's profit margin and risk buffer.
4. **Inventory Management**: Many strategies consider the trader's current position to avoid excessive risk.
5. **News Impact**: Some strategies incorporate the effect of news on asset prices, simulating how traders react to new information.

These strategies can be combined to create diverse trader behaviors:
- Use `ConstantFairPrice` with `ConstantSpread` for a simple, stable market maker.
- Combine `OrderFlowSignFairPrice` with `OrderFlowImbalanceSpread` for a more reactive trader.
- Use `NewsImpactExponentialFairPrice` with `TimeWeightedVolume` to simulate a trader who reacts to news but manages execution over time.


## Trader Metrics

The Trader Performance Metrics module is an essential component of the `pymicrostructure` library, designed to analyze and quantify the performance of traders in simulated markets. These metrics provide insights into various aspects of trading strategies, including profitability, risk, efficiency, and market impact.
Evaluating trader performance involves analyzing multiple aspects of their trading activity. These metrics help in comparing different strategies, identifying strengths and weaknesses, and optimizing trading algorithms.

### Profitability Metrics

1. **Final Profit**
   - What it measures: The total profit at the end of the simulation
   - Interpretation: Higher is generally better, but should be considered alongside risk metrics

2. **Profit per State**
   - What it measures: Average profit earned in each time step
   - Interpretation: Indicates the consistency of profit generation

3. **Profit per Volume**
   - What it measures: Profit earned per unit of volume traded
   - Interpretation: Efficiency of the trading strategy in generating profits

### Risk Metrics

4. **Standard Deviation of Profit per State**
   - What it measures: Volatility of profits
   - Interpretation: Lower values indicate more consistent performance

5. **Information Ratio**
   - What it measures: Risk-adjusted performance
   - Interpretation: Higher values indicate better risk-adjusted returns

6. **Mean Absolute Position**
   - What it measures: Average size of the trader's position
   - Interpretation: Indicates the level of risk exposure

### Trading Activity Metrics

7. **Total Trades**
   - What it measures: Number of trades executed
   - Interpretation: Indicates trading frequency

8. **Volume Traded**
   - What it measures: Total volume of all trades
   - Interpretation: Overall level of trading activity

9. **Average Trade Size**
   - What it measures: Mean size of individual trades
   - Interpretation: Indicates typical trade size and potential market impact

### Execution Metrics

10. **Fill Rate**
    - What it measures: Proportion of submitted orders that were executed
    - Interpretation: Higher values indicate more successful order execution

11. **Time in Market**
    - What it measures: Proportion of time the trader held a non-zero position
    - Interpretation: Indicates how often the trader is exposed to market risk

### Market Impact Metrics

12. **Aggressor Ratio**
    - What it measures: Proportion of volume traded as the aggressor (taker)
    - Interpretation: Higher values indicate more aggressive trading, potentially higher costs

13. **Volume as Aggressor/Passive**
    - What it measures: Volume traded as aggressor vs. passive participant
    - Interpretation: Helps understand the trader's role in providing/taking liquidity

### Key Concepts
1. **Position History**: The trader's inventory over time, crucial for understanding risk exposure and trading patterns.
2. **Profit History**: The cumulative profit over time, used to analyze the trader's performance trajectory.
3. **Realized vs. Unrealized Profit**: Distinguishing between profits from closed trades and potential profits from open positions.
4. **Aggressive vs. Passive Trading**: Differentiating between trades that take liquidity (aggressive) and those that provide liquidity (passive).

Usage in Analysis

These metrics can be used in various ways:

- Compare different trading strategies to identify the most effective ones.
- Analyze a single strategy's performance across different market conditions.
- Identify areas for improvement in a trading algorithm.
- Assess the risk-adjusted performance of strategies.

## Market Metrics

The Market Performance Metrics module is a crucial component of the `pymicrostructure` library, designed to analyze the overall efficiency and emergent properties of simulated financial markets. These metrics provide insights into market liquidity, price efficiency, order flow dynamics, and other key aspects of market microstructure.
Evaluating market performance involves analyzing various aspects of market behavior that emerge from the collective actions of traders. These metrics help in assessing market quality, identifying potential inefficiencies, and understanding the impact of different trading strategies on overall market dynamics.


Liquidity metrics measure how easily assets can be bought or sold without causing a significant price impact.

### Quoted Spread
- What it measures: The difference between the best bid and ask prices
- Interpretation: Smaller spreads indicate higher liquidity

### Effective Spread
- What it measures: The actual cost of executing a trade, including price impact
- Interpretation: Lower effective spreads suggest better liquidity for larger orders

### Amihud Illiquidity
- What it measures: The price impact per unit of volume traded
- Interpretation: Lower values indicate higher market liquidity

### Kyle's Lambda
- What it measures: The price impact per unit of order flow
- Interpretation: Lower values suggest higher market depth and resilience

Price Efficiency Metrics
These metrics assess how well the market price reflects all available information.

### Returns Autocorrelation
- What it measures: The correlation between consecutive price returns
- Interpretation: Values close to zero indicate a more efficient market

### Variance Ratio
- What it measures: The ratio of long-term to short-term return variance
- Interpretation: Values close to 1 suggest a more efficient, random walk-like price process

### Hurst Exponent
- What it measures: The long-term memory of the price series
- Interpretation: Values around 0.5 indicate a random walk; higher values suggest trend-following behavior

### Augmented Dickey-Fuller (ADF) Test
- What it measures: The presence of a unit root in the price series
- Interpretation: Stationary price series (rejecting the null hypothesis) suggest mean-reversion

Order Flow Metrics

These metrics analyze the patterns and impact of incoming orders on the market.

### Cancellation Rate
- What it measures: The proportion of orders that are cancelled
- Interpretation: High cancellation rates may indicate algorithmic trading or order spoofing

### Order Flow Imbalance
- What it measures: The imbalance between buy and sell order volumes
- Interpretation: Persistent imbalances may predict short-term price movements

### Trade Sign Autocorrelation
- What it measures: The persistence of buy or sell pressure
- Interpretation: High autocorrelation may indicate the presence of large orders being executed over time

Order Book Metrics

These metrics examine the structure and dynamics of the limit order book.

### Order Book Depth
- What it measures: The volume available at different price levels
- Interpretation: Greater depth indicates higher liquidity and potentially lower price impact

### Order Book Heatmap
- What it measures: The distribution of volume across price levels over time
- Interpretation: Helps visualize order book dynamics and identify patterns in liquidity provision

Price Dynamics Metrics

These metrics analyze how prices evolve over time.

### Volume-Weighted Average Price (VWAP)
- What it measures: The average price weighted by trading volume
- Interpretation: Used as a benchmark for assessing execution quality

### Trade-Midprice Deviation
- What it measures: How far traded prices deviate from the midpoint of the bid-ask spread
- Interpretation: Large deviations may indicate informed trading or temporary liquidity issues

### Realized Volatility
- What it measures: The variability of returns over a specific period
- Interpretation: Higher volatility may indicate increased uncertainty or information flow

Microstructure Metrics

These metrics focus on the fine details of market behavior.

### Roll Spread Estimator
- What it measures: An estimate of the effective bid-ask spread based on price reversals
- Interpretation: Provides an alternative measure of transaction costs when quote data is unavailable

### Key Concepts

1. **Market Efficiency**: The degree to which market prices reflect all available information. Efficient markets should exhibit random walk-like behavior.

2. **Liquidity**: The ease with which assets can be bought or sold without causing significant price movements.

3. **Price Discovery**: The process by which new information is incorporated into market prices.

4. **Market Impact**: The effect that a trader's actions have on the market price of an asset.

5. **Order Book Dynamics**: The evolution of the limit order book over time, reflecting the supply and demand for an asset at different price levels.

Usage in Analysis

These metrics can be used in various ways:

- Assess the overall quality and efficiency of a simulated market
- Compare different market scenarios or configurations
- Evaluate the impact of specific trading strategies on market dynamics
- Identify potential market anomalies or inefficiencies
- Analyze how market behavior changes under different conditions (e.g., high volatility, news events)
