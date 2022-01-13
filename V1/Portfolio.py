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
    def __init__(self, bal, percent_spy, percent_hedge):
        self.cash = bal
        self.assets = 0
        self.holdings = dict()
        self.allocated_for_stock = self.cash * percent_spy
        self.allocated_for_hedge = self.cash * percent_hedge
        self.hedge_fragments = 1
        self.reserved_for_hedge = self.allocated_for_hedge
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


    def get_holding_val(self, name):
        if name in self.holdings:
            return self.holdings[name]["price"] * self.holdings[name]["quantity"]
        else:
            return 0

    def slice_liquid_hedge(self):
        new_slice = self.reserved_for_hedge / (self.hedge_fragments)
        new_slice += self.allocated_for_hedge % new_slice

        if self.hedge_fragments < 0 or self.allocated_for_hedge < 0:
            raise Exception("Fragmentation fault")

        return new_slice

    def rebalance(percent_spy, percent_hedge, rollover_date, verbose=False):
        logs = []
        # Calculate portfolio value (cash + assets)
        portfolio_value = self.cash + self.assets
        # Calculate desired and actual SPY value
        desired_SPY = portfolio_value * percent_spy
        actual_SPY = get_holding_val("SPY") + self.allocated_for_SPY
        # If val of SPY + allocated to SPY is LESS than desired
        if actual_SPY < desired_SPY:
            if verbose:
                logs.append("Too little SPY")
            descrepency = desired_SPY - actual_SPY
            # 1) check if we have enough liquidity allocated to hedge to rebalance
            if descrepency <= self.allocated_for_hedge:
                self.allocated_for_SPY += descrepency
                self.allocated_for_hedge -= descrepency
                if verbose:
                    logs.append("Reallocation from liquid hedge")
            # 2) start selling hedge
            else:
                self.allocated_for_SPY += self.allocated_for_hedge
                self.allocated_for_hedge = 0
                # Start selling assets to rebalance
                while len(self.hedge_queue) > 0:
                    # Reevaluate the descrepency
                    actual_SPY = get_holding_val("SPY") + self.allocated_for_SPY
                    descrepency = desired_SPY - actual_SPY
                    # Find the next contract
                    next_contract = self.hedge_queue[0]["name"]
                    # if its value is less then the descrepency
                    next_contract_val = get_holding_val(next_contract)
                    if next_contract_val < descrepency:
                        if verbose:
                            logs.append("Liquidating position: " + str(next_contract) + " for $" + str(next_contract_val))
                        # sell it all and repeat
                        self.hedge_queue.popLeft()
                        self.allocated_for_SPY += sell_asset(next_contract, "ALL")
                    else:
                        shares_to_sell = max(0, math.floor(descrepency / self.holdings[next_contract]["price"]))
                        self.allocated_for_SPY += sell_asset(next_contract, shares_to_sell)
                        if verbose:
                            logs.append("Liquidating " + str(shares_to_sell) + " shares of " + str(next_contract))
                        break
        elif actual_SPY > desired_SPY:
            if verbose:
                logs.append("Too much SPY")
            descrepency = actual_SPY - desired_SPY
            # 1) If the liquid allocation can rebalance
            if descrepency <= self.allocated_for_SPY:
                self.allocated_for_hedge += descrepency
                self.allocated_for_SPY -= descrepency
                if verbose:
                    logs.append("Reallocation from liquid SPY")
            # 2) start selling SPY
            else:
                self.allocated_for_SPY += self.allocated_for_hedge
                self.allocated_for_hedge = 0
                # Calc descrepency
                # shares to sell = math.ceil(descrepency / price)
                # descrepency goes to alloc_hedge and remainder goes to SPY_alloc
                actual_SPY = get_holding_val("SPY") + self.allocated_for_SPY
                descrepency = actual_SPY - desired_SPY
                SPY_price = self.holdings["SPY"]["price"]
                shares_to_sell = max(0, math.ceil(descrepency / SPY_price))
                liquid = sell_asset("SPY", shares_to_sell)
                self.allocated_for_hedge += descrepency
                self.allocated_for_SPY += (liquid - descrepency)
                if verbose:
                    logs.append("Selling " + str(shares_to_sell) + " shares of SPY for " + str(liquid))
        else:
            if verbose:
                logs.append("Perfectly Balanced!")
        return "\n".join(logs)


    def __str__(self):
        output = dict()
        output["cash"] = self.cash
        output["assets"] = self.assets
        output["holdings"] = self.holdings

        return json.dumps(output, indent = 4) 