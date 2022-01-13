from tqdm import tqdm
import pandas as pd
from datetime import (timedelta, datetime)
from functions import (grand_selector, bid_ask_mean, select_contract, update_hedge_info)
import math
from Portfolio import Portfolio


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


def backtest(params):
    result = dict()
    # Load in the dataset
    data = load_data(params["start"], params["end"])

    # Process one strategy at a time
    for strategy in params["strategies"]:
        result[strategy["name"]] = dict()
        logs = []
        y_axis = []
        portfolio = Portfolio(params["starting balance"])

        print("Beginging processing for strategy: " + strategy["name"])

        # There are three actions that our portfolio takes:
        #  1) Rebalance 
        #       -Selling enough SPY to regain X%
        #       -Buying hedge with the money we got from the sale
        #  3) Allocate more cash to the portfolio's hedge 
        #       -The portfolio manages what money is allocated to hedge/SPY
        #        and what money is reserved to be allocated to hedge
        #  2) Rollover a hedge 
        #       -The portfolio manages a queue of contracts which have rollover dates
        #       -If the head of the queue is ready to be rolled over then
        #       -sell all contracts ready to be roll over
        #       -Use the money from the sale and any hedge allocated money to buy more hedge
        # We initialize these to 0 because the portfolio needs to 
        # take these actions immediately
        rebalancing_in = 0
        hedge_frag_in = 0

        for current in tqdm(pd.date_range(start=params["start"],end=params["end"])):
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


            # Update the value of the portfolio's assets
            stocks_cost = (today_data.iloc[0]["underlying_bid_1545"] + today_data.iloc[0]["underlying_ask_1545"]) / 2
            portfolio.update_holding("SPY", stocks_cost)

            new_hedge_prices = update_hedge_info(today_data, portfolio)
            if params["verbose"]:
                logs.append("SPY cost update: " + str(stocks_cost))
                logs.append("Hedge cost update: " + str(new_hedge_prices))
                logs.append("Portfolio cash: " + str(portfolio.cash) + " assets: " + str(portfolio.assets))

            # Protect against erroneous data
            if portfolio.cash + portfolio.assets < 40000:
                print(current.date())

            # Record the new value of the portfolio
            y_axis.append(math.floor(portfolio.cash + portfolio.assets))

            # If its time to rebalance
            if rebalancing_in <= 0:
                if params["verbose"]:
                    logs.append("Rebalancing...")

                # Liquidate any assets that we own
                result = portfolio.rebalance(strategy["SPY"], strategy["hedge"])
                val = portfolio.sell_asset("SPY")
                if params["verbose"]:
                    logs.append("SELLing stock for " + str(val))
                val = portfolio.sell_asset("hedge")
                if params["verbose"]:
                    logs.append("SELLing hedge for " + str(new_hedge_price))

                # Rebalance the allocation of SPY in the portfolio
                portfolio.allocated_for_stock = portfolio.cash * strategy["SPY"]

                # Initialize the fragmentation for this period and allocate for hedge
                portfolio.liquid_hedge["segments"] = strategy["hedge fragmentation"]
                portfolio.liquid_hedge["total value"] = portfolio.cash * strategy["hedge"]
                portfolio.slice_liquid_hedge()

                if params["verbose"]:
                    logs.append("SPY allocation: " + str(portfolio.allocated_for_stock))
                    logs.append("Hedge allocation: " + str(portfolio.allocated_for_hedge))

                # Spend the allocated cash for the respective assets
                # SPY
                stocks_quantity = math.floor(portfolio.allocated_for_stock / float(stocks_cost))
                portfolio.buy_asset("SPY", stocks_cost, stocks_quantity, stock=True)
                if params["verbose"]:
                    logs.append("BUYing " + str(stocks_quantity) + " stock's for $" + str(stocks_cost))
                # Hedge
                target_contract = grand_selector(
                    today_data,
                    "P",
                    strategy["target delta"],
                    current + timedelta(days=strategy["expiry"])
                )
                put_cost = bid_ask_mean(target_contract) * 100
                hedge_quantity = math.floor(portfolio.allocated_for_hedge / put_cost)
                portfolio.buy_asset("hedge", put_cost, hedge_quantity, data=target_contract, hedge=True)
                if params["verbose"]:
                    logs.append("BUYing " + str(hedge_quantity) + " contracts of " + str(target_contract["expiration"]) + ", " + str(target_contract["strike"]) + " for $" + str(put_cost))

                # Reset rebalancing timer
                rebalancing_in = strategy["rebalancing period"]
                # Reset the rollover timer
                rolling_over_in = min(strategy["rollover"], strategy["expiry"])
                # Reset fragmentation timer
                frag_timer = math.floor(strategy["rebalancing period"] / strategy["hedge fragmentation"])

            
            # Time to allocate more cash to hedge 
            if frag_timer <= 0:
                portfolio.slice_liquid_hedge()
                frag_timer = math.floor(strategy["rebalancing period"] / strategy["hedge fragmentation"])
                if params["verbose"]:
                    logs.append("Allocating another slice to hedge. Currently: " + str(portfolio.allocated_for_hedge))

            
            
            """
            elif rolling_over_in <= 0:
                if params["verbose"]:
                    logs.append("Rolling over...")

                # Update hedge price
                new_hedge_price = update_hedge_info(today_data, portfolio)

                # Sell hedge
                portfolio.sell_asset("hedge", hedge=True)
                if params["verbose"]:
                    logs.append("SELLing hedge for " + str(new_hedge_price))
                
                # Buy hedge with portfolio's allocated cash
                target_contract = grand_selector(
                    today_data,
                    "P",
                    strategy["target delta"],
                    current + timedelta(days=strategy["expiry"])
                )
                put_cost = bid_ask_mean(target_contract) * 100
                hedge_quantity = math.floor(portfolio.allocated_for_hedge / put_cost)
                portfolio.buy_asset("hedge", put_cost, hedge_quantity, data=target_contract, hedge=True)
                if params["verbose"]:
                    logs.append("BUYing " + str(hedge_quantity) + " contracts of " + str(target_contract["expiration"]) + ", " + str(target_contract["strike"]) + " for $" + str(put_cost))

                # reset rollover timer
                rolling_over_in = min(strategy["rollover"], strategy["expiry"])
            
            """
            else:                
                rebalancing_in -= 1
                rolling_over_in -= 1
                frag_timer -= 1
        result[strategy["name"]]["logs"] = logs
        result[strategy["name"]]["y axis"] = y_axis


    return result


# Todo:
# -When value of hedge increases over rebalancing period, excess money should be put back into hedge
