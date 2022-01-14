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


def backtest(params):
    final_result = {}
    # Load in the dataset
    data = load_data(params["start"], params["end"])

    # Process one strategy at a time
    for strategy in params["strategies"]:
        logs = []
        y_axis = []
        portfolio = Portfolio(params["starting balance"], strategy["SPY"], strategy["hedge"])
        portfolio.hedge_fragments = strategy["hedge fragmentation"]
        

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
            if (len(portfolio.hedge_queue) != 0 and len(portfolio.holdings) != 0) and len(portfolio.hedge_queue) + 1 != len(portfolio.holdings) :
                print(list(portfolio.hedge_queue))
                print(portfolio.holdings)
                raise Exception("Queue len=" + str(len(portfolio.hedge_queue)) + " holdings len=" + str(len(portfolio.holdings)))
                
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

                # Liquidate assets to rebalance portfolio
                portfolio.hedge_fragments = strategy["hedge fragmentation"]
                result = portfolio.rebalance(strategy["SPY"], strategy["hedge"], verbose=params["verbose"])
                if params["verbose"]:
                    logs.append(result)

                # Spend allocated cash on respective assets
                if params["verbose"]:
                    logs.append("SPY allocation: " + str(portfolio.allocated_for_stock))
                    logs.append("Hedge allocation: " + str(portfolio.allocated_for_hedge))

                stocks_quantity = math.floor(portfolio.allocated_for_stock / float(stocks_cost))
                portfolio.buy_stock(stocks_cost, stocks_quantity)
                if params["verbose"]:
                    logs.append("BUYing " + str(stocks_quantity) + " stock's for $" + str(stocks_cost))

                
                # Reset rebalancing timer
                rebalancing_in = strategy["rebalancing period"]
                # Reset fragmentation timer
                frag_timer = math.floor(strategy["rebalancing period"] / strategy["hedge fragmentation"])

            
            # Time to allocate more cash to hedge 
            if frag_timer <= 0:
                portfolio.slice_liquid_hedge()

                frag_timer = math.floor(strategy["rebalancing period"] / strategy["hedge fragmentation"])
                if params["verbose"]:
                    logs.append("Allocating another slice to hedge. Currently: " + str(portfolio.allocated_for_hedge))

            # Check for any contracts ready to rollover
            if len(portfolio.hedge_queue) > 0 and portfolio.hedge_queue[0]["date"] <= current:
                # 1) sell all holdings that are ready to be rolled over
                cash = 0
                count = 0
                for put in portfolio.hedge_queue:
                    if put["date"] <= current:
                        value = portfolio.sell_asset(put["name"], "ALL")
                        if params["verbose"]:
                            logs.append("Rolling over " + str(put["name"]) + " adding $" + str(value) + " to hedge allocation")
                        cash += value
                        count += 1
                    else:
                        break
                for i in range(count):
                    portfolio.hedge_queue.popleft()

            target_contract = grand_selector(
                today_data,
                "P",
                strategy["target delta"],
                current + timedelta(days=strategy["expiry"])
            )
            put_cost = bid_ask_mean(target_contract) * 100
            hedge_quantity = math.floor( portfolio.allocated_for_hedge / put_cost)
            if hedge_quantity > 0:
                contract_name = target_contract["expiration"] + str(target_contract["strike"]) + str(current.date())
                portfolio.buy_puts(contract_name, put_cost, hedge_quantity, target_contract, current + timedelta(days=strategy["rollover"]))
                if params["verbose"]:
                    logs.append("BUYing " + str(hedge_quantity) + " contracts of " + str(target_contract["expiration"]) + ", " + str(target_contract["strike"]) + " for $" + str(put_cost))




            rebalancing_in -= 1
            frag_timer -= 1
        final_result[strategy["name"]] = {
            "logs": logs,
            "y axis": y_axis
        }



    return final_result
