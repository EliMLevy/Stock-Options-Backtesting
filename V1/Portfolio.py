from collections import deque
import json 
import math


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
        self.hedge_fragments = 0
        self.reserved_for_hedge = 0
        self.hedge_queue = deque()
        self.hedge_pl = 0
        self.stock_pl = 0


    def update_holding(self, holding, price, data=dict()):
        if holding in self.holdings:
            diff = price - self.holdings[holding]["price"]
            profit = diff * self.holdings[holding]["quantity"]
            if holding == "SPY":
                self.stock_pl += profit
            else:
                self.hedge_pl += profit
            self.assets += profit
            self.holdings[holding]["price"] = price
            self.holdings[holding]["data"] = data
            
    def buy_stock(self, price, quantity):
        cost = price * quantity
        self.cash -= cost
        self.assets += cost
        if "SPY" in self.holdings:
            self.holdings["SPY"]["quantity"] += quantity
        else:
            self.holdings["SPY"] = {
                "name": "SPY",
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
        self.hedge_fragments -= 1
        self.reserved_for_hedge -= new_slice
        self.allocated_for_hedge += new_slice
        if self.hedge_fragments < 0 or self.reserved_for_hedge < 0:
            raise Exception("Fragmentation fault")

        return new_slice

    def rebalance(self, percent_spy, percent_hedge, verbose=False):
        logs = []
        stats = {
            "# of SPY trades": 0,
            "# of put trades": 0
        }
        # self.check_invariants()
        # Calculate portfolio value (cash + assets)
        portfolio_value = self.cash + self.assets
        # Calculate desired and actual SPY value
        desired_SPY = portfolio_value * percent_spy
        actual_SPY = self.get_holding_val("SPY") + self.allocated_for_stock
        # get rid of any reserves (it will be replaced at the end of rebalancing)
        self.allocated_for_hedge += self.reserved_for_hedge
        self.reserved_for_hedge = 0

        # If val of SPY is too big
        if actual_SPY > desired_SPY:
            if verbose:
                logs.append("Too much SPY")
            descrepency = actual_SPY - desired_SPY
            # 1) If the liquid allocation can rebalance
            if descrepency <= self.allocated_for_stock:
                self.allocated_for_hedge += descrepency
                self.allocated_for_stock -= descrepency
                if verbose:
                    logs.append("Reallocation from liquid SPY")
                # self.check_invariants()
                
            # 2) Start selling SPY shares
            else:
                # Get rid of any cash reserved for spy before we start selling
                self.allocated_for_hedge += self.allocated_for_stock
                self.allocated_for_stock = 0
                # self.check_invariants()

                # Calc descrepency
                actual_SPY = self.get_holding_val("SPY") + self.allocated_for_stock
                descrepency = actual_SPY - desired_SPY
                # shares to sell = math.ceil(descrepency / price) or 0 (if the descrepency became a negative)
                SPY_price = self.holdings["SPY"]["price"]
                shares_to_sell = max(0, math.ceil(descrepency / SPY_price))
                # descrepency goes to alloc_hedge and remainder goes to SPY_alloc
                liquid = self.sell_asset("SPY", shares_to_sell)
                stats["# of SPY trades"] += 1
                self.allocated_for_hedge += descrepency
                self.allocated_for_stock += (liquid - descrepency)
                if verbose:
                    logs.append("Selling " + str(shares_to_sell) + " shares of SPY for " + str(liquid))
                
                # self.check_invariants()

        else:
            if verbose:
                logs.append("Too little SPY")
            descrepency = desired_SPY - actual_SPY
            # 1) If we have enough liquid hedge to reblanace
            if descrepency <= self.allocated_for_hedge:
                self.allocated_for_stock += descrepency
                self.allocated_for_hedge -= descrepency
                if verbose:
                    logs.append("Reallocation from liquid hedge")
            # 2) Start selling hedge
            else:
                # Get rid of any cash allocated for hedge before we start selling
                self.allocated_for_stock += self.allocated_for_hedge
                self.allocated_for_hedge = 0

                actual_SPY = self.get_holding_val("SPY") + self.allocated_for_stock
                val_of_puts = portfolio_value - actual_SPY
                # desired val of puts = % * (portfolio_val) (deal with fragments later)
                desired_val_of_puts = (percent_hedge * portfolio_value)
                # As we sell, we need to remove them from queue buy
                while len(self.hedge_queue) > 0:
                    current_contract = self.hedge_queue.popleft()
                    actual_SPY = self.get_holding_val("SPY") + self.allocated_for_stock
                    val_of_puts = portfolio_value - actual_SPY
                    descrepency = val_of_puts - desired_val_of_puts
                    # Sell the current contract
                    liquid = self.sell_asset(current_contract["name"], "ALL")
                    stats["# of put trades"] += 1
                    if verbose:
                        logs.append("Selling " + str(current_contract["name"]) + " for $" + str(liquid))
                    # If this sale is enough to cover descrepency, then move the amount of the descrepency
                    # to the allocated for stock and the remainder remains with hedge. Otherwise, move it
                    # all to stock
                    if liquid > descrepency:
                        self.allocated_for_stock += descrepency 
                        self.allocated_for_hedge += (liquid - descrepency)
                        if verbose:
                            logs.append("Alocating $" + str(liquid - descrepency) + " to hedge and $" + str(descrepency ) + " to stock")
                        # We have finished
                        break
                    else:
                        self.allocated_for_stock += liquid

        # self.check_invariants()

        
        # Before we conclude we must sell more puts such that we are below the 
        # amount for the first fragement of the rebalancing period
        if verbose:
            logs.append("Final stage, selling puts")
        # 1) find the correct amount of non-liquidity
        actual_SPY = self.get_holding_val("SPY") + self.allocated_for_stock

        desired_nonliquid_puts_val = (percent_hedge * portfolio_value) / self.hedge_fragments
        actual_nonliquid_puts_val = (portfolio_value - actual_SPY) - self.allocated_for_hedge
        if desired_nonliquid_puts_val < actual_nonliquid_puts_val:
            if verbose:
                logs.append("Too much nonliquidity desired=" + str(desired_nonliquid_puts_val) + " actual=" + str(actual_nonliquid_puts_val))
            while len(self.hedge_queue) > 0:
                current_contract = self.hedge_queue.popleft()
                # 2) sell current put and move the cash to put liquidity
                liquid = self.sell_asset(current_contract["name"], "ALL")
                stats["# of put trades"] = 1
                if verbose:
                    logs.append("Selling " + str(current_contract["name"]) + " for $" + str(liquid))
                self.allocated_for_hedge += liquid
                actual_nonliquid_puts_val = (portfolio_value - actual_SPY) - self.allocated_for_hedge
                # 3) compare out non-liquidity to correect non-liquidity
                if desired_nonliquid_puts_val >= actual_nonliquid_puts_val:
                    break
        # self.check_invariants()

        # Lastly, we need to move enough cash to hedge reserves
        # 1) Caluculate how much belongs in reserves
        desired_cash_in_reserves = ((percent_hedge * portfolio_value) / self.hedge_fragments) * (self.hedge_fragments - 1)
        assert abs((portfolio_value * percent_hedge) - (desired_cash_in_reserves + desired_nonliquid_puts_val)) < 1, "pv: " + str(portfolio_value) + "; ph:" + str(percent_hedge) + "; r:" + str(desired_cash_in_reserves) + "; pr:" + str(desired_nonliquid_puts_val)  
        
        assert desired_cash_in_reserves <= self.allocated_for_hedge, "Desired: " + str(desired_cash_in_reserves) + " cash: " + str(self.allocated_for_hedge) + "\n" + str(self)
        
        if verbose:
            logs.append("Moving " + str(desired_cash_in_reserves) + " from allocated to reserved")
        # 2) move that much
        self.reserved_for_hedge += desired_cash_in_reserves
        self.allocated_for_hedge -= desired_cash_in_reserves

        if verbose:
            portfolio_value = self.cash + self.assets
            stocks_val = self.get_holding_val("SPY")
            stocks_liquid = self.allocated_for_stock
            puts_val = self.assets - stocks_val
            puts_liquid = self.allocated_for_hedge
            puts_reserved = self.reserved_for_hedge
            logs.append("Finished with: Portfolio="+str(portfolio_value) + "; SPY stock=" + str(stocks_val) + " liquid=" + str(stocks_liquid) + "; hedge stock=" + str(puts_val) + " liquid=" + str(puts_liquid) + " reserved=" + str(puts_reserved))
            logs.append("Perfectly Balanced!")
       
        # self.check_invariants()
        return ["\n".join(logs), stats]


    def __str__(self):
        output = dict()
        output["cash"] = self.cash
        output["assets"] = self.assets
        output["holdings"] = self.holdings
        output["Allocated Cash"] = {
            "SPY": self.allocated_for_stock,
            "hedge": self.allocated_for_hedge

        }

        return str(output)


    def check_invariants(self):
        # 1) Assets should sum to self.assets
        assets = 0
        for name in self.holdings:
            holding = self.holdings[name]
            assets += (holding["price"] * holding["quantity"])
        assert abs(round(assets, 1) - round(self.assets, 1)) < 1, "Portfolio assets are " + str(self.assets) + " however sum of assets is " + str(assets) + "\n" + str(self) 

        # 2) allocated cash should sum to cash
        allocated = self.allocated_for_hedge + self.allocated_for_stock + self.reserved_for_hedge
        assert round(self.cash, 3) == round(allocated, 3), "Portfolio cash is " + str(self.cash) + " however allocated cash is " + str(allocated) + "\n" + str(self)

        # 3) allocated should never be below zero
        assert self.allocated_for_hedge >= 0, "Allocated to hedge is " + str(self.allocated_for_hedge)
        assert self.allocated_for_stock >= 0, "Allocated to stock is " + str(self.allocated_for_stock)
        assert self.reserved_for_hedge >= 0, "Reserved for hedge is " + str(self.reserved_for_hedge)

        # 4) Every position in queue has a guy in holdings and vis versa
        # TODO make this invariant
        for put in self.hedge_queue:
            assert put["name"] in self.holdings, str(put["name"]) + " is in queue but could not be found in holdings \n" + str(self.holdings) + "\n" + str(self.hedge_queue)
        for holding in self.holdings:
            if self.holdings[holding]["name"] != "SPY":
                found = False
                for put in self.hedge_queue:
                    if put["name"] == self.holdings[holding]["name"]:
                        found = True
                
                assert found == True, str(self.holdings[holding]["name"]) + " is in holdings but could not be found in queue \n" + str(self.holdings) + "\n" + str(self.hedge_queue)