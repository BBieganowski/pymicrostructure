from microstructpy.market import Market
import matplotlib.pyplot as plt


def price_path(market: Market):
    """
    Visualize the price path of a market.

    Parameters
    ----------
    market : Market
        The market to visualize.

    Returns
    -------
    None
    """
    print(market.trade_history)
    prices = [trade['price'] for trade in market.trade_history] 
    agressor_side = [trade['agressor_side'] for trade in market.trade_history]
    time = [trade['time'] for trade in market.trade_history]

    best_bid = [snapshot['bid'][0]['price'] if snapshot['bid'] else None for snapshot in market.ob_snapshots]
    best_ask = [snapshot['ask'][0]['price'] if snapshot['ask'] else None for snapshot in market.ob_snapshots] 
    ob_time = [snapshot['time'] for snapshot in market.ob_snapshots]



    plt.plot(ob_time, best_bid, label="Best Bid", color="green")
    plt.plot(ob_time, best_ask, label="Best Ask", color="red")

    plt.scatter(time, prices, c=agressor_side, cmap='RdYlGn_r', label="Trades")
    
    plt.xlabel("Time")
    plt.ylabel("Price")
    plt.title("Price Path")
    plt.legend()
    plt.show()
