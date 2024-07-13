def get_position_history(trader):
    position = 0
    position_history = [0]  # Start with initial position of 0
    position_timestamps = [0]  # Start with timestamp 0

    final_timestamp = trader.market.last_submission_time
    trade_index = 0

    for timestamp in range(1, final_timestamp + 1):
        # Process any trades at this timestamp
        while (trade_index < len(trader.filled_trades) and 
               trader.filled_trades[trade_index]['time'] == timestamp):
            trade = trader.filled_trades[trade_index]
            position += trade['volume']
            trade_index += 1

        # Append the current position to the history
        position_history.append(position)
        position_timestamps.append(timestamp)

    return position_timestamps, position_history

def get_profit_history(trader):
    realized_profit = 0
    unrealized_profit = 0
    position = 0

    profit = [0]
    profit_timestamps = [0]

    final_timestamp = trader.market.last_submission_time
    trade_history = trader.filled_trades

    for timestamp in range(final_timestamp + 1):
        # Process trades at this timestamp
        while trade_history and trade_history[0]['time'] == timestamp:
            trade = trade_history.pop(0)
            volume = trade['volume']
            price = trade['price']
            
            # Calculate realized profit
            realized_profit -= volume*price
            position += volume

        # Mark position to market
        midprice = [x[1] for x in trader.market.midprices if x[0] == timestamp][0]

        # Calculate unrealized profit
        unrealized_profit = position*midprice

        # Calculate total profit
        total_profit = realized_profit + unrealized_profit
        
        profit.append(total_profit)
        profit_timestamps.append(timestamp)

    return profit_timestamps, profit





