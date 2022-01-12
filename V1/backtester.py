from tqdm import tqdm
import pandas as pd
from datetime import (timedelta, datetime)
from functions import (grand_selector, bid_ask_mean, select_contract, update_hedge_info)
import math





class Portfolio:
    def __init__(self, bal):
        self.bal = bal
        self.assets = 0
        self.holdings = dict()
        self.liquid_hedge = {
            "segments":0,
            "total value":0,
        }

    def update_holding(self, holding, price, data=None):
        if holding in self.holdings:
            profit = price - self.holdings[holding]["price"]
            self.assets += profit * self.holdings[holding]["quantity"]
            self.holdings[holding]["price"] = price
            self.holdings[holding]["data"] = data
            

    def buy_asset(self, name, price, quantity, data=dict()):
        self.bal -= price * quantity
        self.assets += price * quantity
        self.holdings[name] = {
            "name": name,
            "price": price,
            "quantity": quantity
        }
        self.holdings[name]["data"] = data

    def sell_asset(self, name):
        if name in self.holdings:
            value = self.holdings[name]["price"] * \
                self.holdings[name]["quantity"]
            self.bal += value
            self.assets -= value
            self.holdings.pop(name)
            return value
        else:
            return -1

    def get_holding_info(self, name):
        if name in self.holdings:
            return self.holdings[name]
        else:
            return None

    def slice_liquid_hedge(self):
        return_slice = self.liquid_hedge["total value"] / self.liquid_hedge["segments"]
        self.liquid_hedge["total value"] -= return_slice
        self.liquid_hedge["segments"] -= 1

        if self.liquid_hedge["total value"] < 0 or self.liquid_hedge["segments"] < 0:
            raise Exception("Fragmentation fault")

        return return_slice

    def __str__(self):
        output = "Portfolio:\n"
        for holding in self.holdings:
            output += ">>" + str(self.holdings[holding]["name"]) + "<<\n"
            output += "  price: " + str(self.holdings[holding]["price"]) + "\n"
            output += "  quantity: " + \
                str(self.holdings[holding]["quantity"]) + "\n"
            output += "  value: " + \
                str(self.holdings[holding]["quantity"] * self.holdings[holding]["price"]) + "\n"
        output += "Cash: " + str(self.bal) + "\n"
        output += "Assets: " + str(self.assets)

        return output


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
        result[strategy["name"]] = dict();
        logs = []
        portfolio = Portfolio(params["starting balance"])
        y_axis = []

        print("Beginging processing for strategy: " + strategy["name"])

        # set a timer to renew the contracts (min(rollover, expiry))
        # set a timer to rebalance the % of stock and % of option
        rebalancing_in = 0
        rolling_over_in = 0
        frag_timer = 0

        # hedge_annual_budget = params["starting balance"] * strategy["hedge"]

        for current in tqdm(pd.date_range(start=params["start"],end=params["end"])):
            # print(str(current.date()))
            # Grab todays data
            if str(current.date()) in data:
                today_data = data[str(current.date())]
            else:
                # print("skipping " + str(current.date()))
                # logs.append("skipping " + str(current.date()))
                rebalancing_in -= 1
                rolling_over_in -= 1
                frag_timer -= 1
                y_axis.append(math.floor(portfolio.bal + portfolio.assets))
                continue

            # Output day header
            logs.append("*************\n" + str(current.date()))

            stocks_cost = (today_data.iloc[0]["underlying_bid_1545"] + today_data.iloc[0]["underlying_ask_1545"]) / 2

            portfolio.update_holding("SPY", stocks_cost)

            new_hedge_price = update_hedge_info(today_data, portfolio)

            logs.append("SPY cost update: " + str(stocks_cost))
            logs.append("Hedge cost update: " + str(new_hedge_price))
            logs.append("Portfolio cash: " + str(portfolio.bal) + " assets: " + str(portfolio.assets))

            if portfolio.bal + portfolio.assets < 40000:
                print(current.date())

            y_axis.append(math.floor(portfolio.bal + portfolio.assets))

            if rebalancing_in <= 0:
                logs.append("Rebalancing...")

                # update stock and put cost
                # stocks_cost = data["SPYStock"][data["SPYStock"]["Date"] == current.strftime("%m/%d/%Y")].iloc[0]["Close/Last"]
                portfolio.update_holding("SPY", stocks_cost)

                new_hedge_price = update_hedge_info(today_data, portfolio)

                # Sell any SPY and Hedge that we own
                val = portfolio.sell_asset("SPY")
                logs.append("SELLing stock for " + str(val))
                val = portfolio.sell_asset("hedge")
                logs.append("SELLing hedge for " + str(new_hedge_price))

                # Update the money dedicated to hedge for the rebalancing period
                portfolio.liquid_hedge["segments"] = strategy["hedge fragmentation"]
                portfolio.liquid_hedge["total value"] = portfolio.bal * strategy["hedge"]

                # buy SPY% of balanace stocks
                stocks_budget = portfolio.bal * strategy["SPY"]
                stocks_quantity = math.floor(stocks_budget / float(stocks_cost))
                portfolio.buy_asset("SPY", stocks_cost, stocks_quantity)
                logs.append("BUYing " + str(stocks_quantity) + " stock's for $" + str(stocks_cost))
                # buy hedge% of balance puts
                target_contract = grand_selector(
                    today_data,
                    "P",
                    strategy["target delta"],
                    current + timedelta(days=strategy["expiry"])
                )
                put_cost = bid_ask_mean(target_contract) * 100
                # hedge_budget = hedge_annual_budget / strategy["hedge fragmentation"]
                hedge_budget = portfolio.slice_liquid_hedge()

                hedge_quantity = math.floor(hedge_budget / put_cost)
                portfolio.buy_asset("hedge", put_cost, hedge_quantity, data=target_contract)
                logs.append("BUYing " + str(hedge_quantity) + " contracts of " + str(target_contract["expiration"]) + ", " + str(target_contract["strike"]) + " for $" + str(put_cost))

                # Reset rebalancing timer
                rebalancing_in = strategy["rebalancing period"]
                # Reset the rollover timer
                rolling_over_in = strategy["rollover"]
                # Reset fragmentation timer
                frag_timer = math.floor(strategy["rebalancing period"] / strategy["hedge fragmentation"])

            elif rolling_over_in <= 0:
                logs.append("Rolling over...")
                # Update hedge price
                new_hedge_price = update_hedge_info(today_data, portfolio)

                # Sell hedge
                hedge_budget = portfolio.sell_asset("hedge")
                logs.append("SELLing hedge for " + str(new_hedge_price))
                if frag_timer <= 0: # if its time to add money to hedge budget
                    logs.append("Frag timer is " + str(frag_timer))
                    new_slice = 0
                    new_slice += portfolio.slice_liquid_hedge()
                    # We may have missed some framents so add up all the missed ones
                    while frag_timer <= 0:
                        new_slice += portfolio.slice_liquid_hedge()
                        frag_timer += math.floor(strategy["rebalancing period"] / strategy["hedge fragmentation"])
                        logs.append(">>" + str(frag_timer) + ": " + str(new_slice))

                    hedge_budget += new_slice
                    logs.append("adding " + str(new_slice) + " to hedge budget")
                # Buy hedge again with money made from sale
                target_contract = grand_selector(
                    today_data,
                    "P",
                    strategy["target delta"],
                    current +timedelta(days=strategy["expiry"])
                )
                put_cost = bid_ask_mean(target_contract) * 100
                hedge_quantity = math.floor(hedge_budget / put_cost)
                portfolio.buy_asset("hedge", put_cost, hedge_quantity, data=target_contract)
                logs.append("BUYing " + str(hedge_quantity) + " contracts of " + str(target_contract["expiration"]) + ", " + str(target_contract["strike"]) + " for $" + str(put_cost))

                # reset rollover timer
                rolling_over_in = strategy["rollover"]
            else:                
                rebalancing_in -= 1
                rolling_over_in -= 1
                frag_timer -= 1
        result[strategy["name"]]["logs"] = logs
        result[strategy["name"]]["y axis"] = y_axis


    return result


# Todo:
# -When value of hedge increases over rebalancing period, excess money should be put back into hedge
