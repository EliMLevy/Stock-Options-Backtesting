import pandas as pd
from datetime import (timedelta, datetime)
from functions import (grand_selector, bid_ask_mean, select_contract, update_hedge_info)
import math
from Portfolio import Portfolio
import json




def backtestNoHedge(params, data):
    final_result = {}
    y_axis = []

    portfolio = Portfolio(params["starting balance"], 1, 0)
    

    print("Beginging processing for no hedge")


    for current in (pd.date_range(start=params["start"],end=params["end"])):
        # Grab todays data
        if str(current.date()) in data:
            today_data = data[str(current.date())]
        else:
            # The dataset is missing this day (weekend, holiday, or deliquency)
            # Push the timers down by one to signal the passage of a day and 
            # record the portfolio's value
            y_axis.append(math.floor(portfolio.cash + portfolio.assets))
            continue

        # Update the value of the portfolio's assets
        stocks_cost = (today_data.iloc[0]["underlying_bid_1545"] + today_data.iloc[0]["underlying_ask_1545"]) / 2
        if portfolio.allocated_for_stock > stocks_cost:
            quantity = math.floor(portfolio.allocated_for_stock / stocks_cost)
            portfolio.buy_stock(stocks_cost, quantity)
        # print(stocks_cost)
        portfolio.update_holding("SPY", stocks_cost)

        # Record the new value of the portfolio
        y_axis.append(math.floor(portfolio.cash + portfolio.assets))

    final_result = {
        "y axis": y_axis,
    }

    return final_result
