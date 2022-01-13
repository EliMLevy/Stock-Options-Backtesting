from collections import deque
import json 


class Portfolio:
    """
    holdings = {
        "SPY": {
            "name":___,
            "price":__,
            "quantity":__
        },
        "contract name":{
            "name":__,
            "rollover date":__,
            "price":__,
            "quantity":__,
            "data":__
        },
        ...
    }
    """
    def __init__(self, bal):
        self.cash = bal
        self.assets = 0
        self.holdings = dict()
        self.allocated_for_stock = 0
        self.allocated_for_hedge = 0
        self.hedge_reserved = {
            "total value":0,
            "segments": 1
        }
        self.hedge_queue = deque()


    def update_holding(self, holding, price, data=dict()):
        if holding in self.holdings:
            profit = price - self.holdings[holding]["price"]
            self.assets += profit * self.holdings[holding]["quantity"]
            self.holdings[holding]["price"] = price
            self.holdings[holding]["data"] = data
            
    def buy_stock(self, price, quantity):
        cost = price * quantity
        self.cash -= cost
        self.assets += cost
        self.holdings["SPY"] = {
            "name": name,
            "price": price,
            "quantity": quantity
        }
        self.allocated_for_stock -= cost

    def buy_puts(self, name, price, quantity, data, rollover_date):
        cost = price * quantity
        self.cash -= cost
        self.assets += cost
        self.holdings[name] = {
            "name": name,
            "price": price,
            "quantity": quantity,
            "data":data,
            "rollover date": rollover_date
        }
        self.allocated_for_hedge -= cost
        self.hedge_queue.append({"date":rollover_date, "name":name})

    def sell_asset(self, holding_name, quantity):
        if holding_name in self.holdings:
            if quantity == "ALL":
                quantity = self.holdings[holding_name]["quantity"]
            value = self.holdings[holding_name]["price"] * quantity
            self.cash += value
            self.assets -= value
            self.holdings[holding_name]["quantity"] -= quantity
            if self.holdings[holding_name]["quantity"] == 0:
                self.holdings.pop(holding_name)
            return value
        else:
            return -1



    def get_holding_info(self, name):
        if name in self.holdings:
            return self.holdings[name]
        else:
            return None

    def slice_liquid_hedge(self):
        if self.hedge_reserved["segments"] == 0:
            return 0
        new_slice = self.hedge_reserved["total value"] / self.hedge_reserved["segments"]
        self.hedge_reserved["total value"] -= new_slice
        self.hedge_reserved["segments"] -= 1

        if self.hedge_reserved["total value"] < 0 or self.hedge_reserved["segments"] < 0:
            raise Exception("Fragmentation fault")

        self.allocated_for_hedge += new_slice

        return new_slice

    def __str__(self):
        output = dict()
        output["cash"] = self.cash
        output["assets"] = self.assets
        output["holdings"] = self.holdings

        return json.dumps(output, indent = 4) 