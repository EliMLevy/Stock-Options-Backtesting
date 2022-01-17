from tqdm import tqdm
import pandas as pd
from datetime import (timedelta, datetime)
from functions import (grand_selector, bid_ask_mean, select_contract, update_hedge_info)
import math
from Portfolio import Portfolio
import json


def load_data(start, end):
    print("loading data...")
    data = dict()
    file_prefix = "UnderlyingOptionsEODCalcs_"

    for current in tqdm(pd.date_range(start=start, end=end)):
        try:
            data[str(current.date())] = pd.read_csv(
                "../data/" + file_prefix + str(current.date()) + ".csv")
        except FileNotFoundError:
            continue

    return data


def backtest(params, data):
    final_result = {}
    # Load in the dataset
    # data = load_data(params["start"], params["end"])

    # Process one strategy at a time
    # for strategy in params["strategies"]:
    strategy = params["strategy"]
    logs = []
    y_axis = []
    stats = {
        "# of days":0,
        "# of SPY trades": 0,
        "# of SPY shares bought": 0,
        "# of put trades": 0,
        "# of put contracts bought": 0,
        "largest % drawdown": 0,
        "largest % drawup": 0,
        "avg. profit per day": 0,
        "total profit": 0,
    }
    portfolio = Portfolio(params["starting balance"], strategy["SPY"], strategy["hedge"])
    portfolio.hedge_fragments = strategy["hedge fragmentation"]
    

    print("Beginging processing for strategy: " + strategy["name"])
    """
    There are three actions that our portfolio takes:
        1) Rebalance 
            -Selling enough SPY to regain X%
            -Buying hedge with the money we got from the sale
        3) Allocate more cash to the portfolio's hedge 
            -The portfolio manages what money is allocated to hedge/SPY
            and what money is reserved to be allocated to hedge
        2) Rollover a hedge 
            -The portfolio manages a queue of contracts which have rollover dates
            -If the head of the queue is ready to be rolled over then
            -sell all contracts ready to be roll over
            -Use the money from the sale and any hedge allocated money to buy more hedge
    We initialize these to 0 because the portfolio needs to 
    take these actions immediately
    """
    rebalancing_in = 0
    frag_timer = 0

    for current in tqdm(pd.date_range(start=params["start"],end=params["end"])):
        stats["# of days"] += 1
        # Grab todays data
        if str(current.date()) in data:
            today_data = data[str(current.date())]
        else:
            # The dataset is missing this day (weekend, holiday, or deliquency)
            # Push the timers down by one to signal the passage of a day and 
            # record the portfolio's value
            rebalancing_in -= 1
            frag_timer -= 1
            y_axis.append(math.floor(portfolio.cash + portfolio.assets))
            continue

        if params["verbose"]:
            # Output day header
            logs.append("*************\n" + str(current.date()))

        portfolio.check_invariants()


        # Update the value of the portfolio's assets
        stocks_cost = (today_data.iloc[0]["underlying_bid_1545"] + today_data.iloc[0]["underlying_ask_1545"]) / 2
        portfolio.update_holding("SPY", stocks_cost)

        portfolio.check_invariants()


        new_hedge_prices = update_hedge_info(today_data, portfolio)
        if params["verbose"]:
            logs.append("SPY cost update: " + str(stocks_cost))
            logs.append("Hedge cost update: " + str(new_hedge_prices))
            logs.append("Portfolio cash: " + str(portfolio.cash) + " assets: " + str(portfolio.assets))

        # Record the new value of the portfolio
        y_axis.append(math.floor(portfolio.cash + portfolio.assets))

        portfolio.check_invariants()

        # If its time to rebalance
        if rebalancing_in <= 0:
            if params["verbose"]:
                logs.append("Rebalancing...")

            # Liquidate assets to rebalance portfolio
            portfolio.hedge_fragments = strategy["hedge fragmentation"]
            result = portfolio.rebalance(strategy["SPY"], strategy["hedge"], verbose=params["verbose"])
            stats["# of SPY trades"] += result[1]["# of SPY trades"]
            stats["# of put trades"] += result[1]["# of put trades"]
            if params["verbose"]:
                logs.append(result[0])

            # Spend allocated cash on respective assets
            if params["verbose"]:
                logs.append("SPY allocation: " + str(portfolio.allocated_for_stock))
                logs.append("Hedge allocation: " + str(portfolio.allocated_for_hedge))

            stocks_quantity = math.floor(portfolio.allocated_for_stock / float(stocks_cost))
            portfolio.buy_stock(stocks_cost, stocks_quantity)
            stats["# of SPY trades"] += 1
            stats["# of SPY shares bought"] += stocks_quantity
            if params["verbose"]:
                logs.append("BUYing " + str(stocks_quantity) + " stock's for $" + str(stocks_cost))

            # Wait for buying puts bc more money may be allocated to puts before the day is over
            
            # Reset rebalancing timer
            rebalancing_in = strategy["rebalancing period"]
            # Reset fragmentation timer
            frag_timer = math.floor(strategy["rebalancing period"] / strategy["hedge fragmentation"])

        
        portfolio.check_invariants()

        # Time to allocate more cash to hedge 
        if frag_timer <= 0:
            # This function moves money from the portfolios hedge reserves
            # to the portfolios allocated container
            portfolio.slice_liquid_hedge()

            frag_timer = math.floor(strategy["rebalancing period"] / strategy["hedge fragmentation"])
            if params["verbose"]:
                logs.append("Allocating another slice to hedge. Currently: " + str(portfolio.allocated_for_hedge))

        portfolio.check_invariants()


        # Check for any contracts ready to rollover
        if len(portfolio.hedge_queue) > 0 and portfolio.hedge_queue[0]["date"] <= current:
            # 1) sell all holdings that are ready to be rolled over
            while len(portfolio.hedge_queue) > 0:
                if portfolio.hedge_queue[0]["date"] <= current:
                    put = portfolio.hedge_queue.popleft()
                    value = portfolio.sell_asset(put["name"], "ALL")
                    stats["# of put trades"] += 1
                    portfolio.allocated_for_hedge += value
                    if params["verbose"]:
                        logs.append("Rolling over " + str(put["name"]) + " adding $" + str(value) + " to hedge allocation")
                else:
                    break
        
        portfolio.check_invariants()
        
        
        try:
            target_contract = grand_selector(
                today_data,
                "P",
                strategy["target delta"],
                current + timedelta(days=strategy["expiry"])
            )
            put_cost = bid_ask_mean(target_contract) * 100
            if put_cost == 0:
                print(current.date())
                raise Exception("Put cost should not be 0")
            hedge_quantity = math.floor(portfolio.allocated_for_hedge / put_cost)
            if hedge_quantity > 0:
                contract_name = target_contract["expiration"] + str(target_contract["strike"]) + str(current.date())
                portfolio.buy_puts(contract_name, put_cost, hedge_quantity, target_contract, current + timedelta(days=strategy["rollover"]))
                stats["# of put trades"] += 1
                stats["# of put contracts bought"] += hedge_quantity
                if params["verbose"]:
                    logs.append("BUYing " + str(hedge_quantity) + " contracts of " + str(target_contract["expiration"]) + ", " + str(target_contract["strike"]) + " for $" + str(put_cost))
        except ValueError:
            logs.append("Could not find contract to buy on: " + str(current.date()))
        rebalancing_in -= 1
        frag_timer -= 1

        
        # Data collection
        if len(y_axis) > 1:
            day_profit = y_axis[-1] - y_axis[-2]
            percent_profit = day_profit / y_axis[-2] * 100
            if percent_profit < stats["largest % drawdown"]:
                stats["largest % drawdown"] = percent_profit
            if percent_profit > stats["largest % drawup"]:
                stats["largest % drawup"] = percent_profit
        
        """
        Debugging invariants:
        1) SPY value + sum of hedge value = portfolio.assets
        2) allocatedforhedge + allocatedforstock + reservedforhedge = portfolio.cash
        3) no contracts on queue past rollover
        
        """
        portfolio.check_invariants()

        # 1)
        assets = 0
        for name in portfolio.holdings:
            holding = portfolio.holdings[name]
            assets += (holding["price"] * holding["quantity"])
        assert abs(round(assets, 1) - round(portfolio.assets, 1)) < 1, "Portfolio assets are " + str(portfolio.assets) + " however sum of assets is " + str(assets) + "\n" + str(portfolio) 

        # 2)
        allocated = portfolio.allocated_for_hedge + portfolio.allocated_for_stock + portfolio.reserved_for_hedge
        assert round(portfolio.cash, 3) == round(allocated, 3), "Portfolio cash is " + str(portfolio.cash) + " however allocated cash is " + str(allocated) + "\n" + str(portfolio)

        # 3)
        for put in portfolio.hedge_queue:
            assert current <= put["date"], "Today is " + str(current.date()) + " but found contract to rollover at " + str(put["date"].date()) + "\n" + str(portfolio)

    # Final data points
    stats[ "total profit"] = y_axis[-1] - y_axis[0]
    stats["avg. profit per day"] = stats[ "total profit"] / stats["# of days"]

    final_result[strategy["name"]] = {
        "logs": logs,
        "y axis": y_axis,
        "stats": stats
    }

    return final_result
