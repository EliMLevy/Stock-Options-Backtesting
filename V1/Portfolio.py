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
        # Calculate portfolio value (cash + assets)
        portfolio_value = self.cash + self.assets
        # Calculate desired and actual SPY value
        desired_SPY = portfolio_value * percent_spy
        # actual_SPY = self.holdings["SPY"]["price"] * self.holdings["SPY"]["quantity"] + self.allocated_for_stock
        actual_SPY = self.get_holding_val("SPY") + self.allocated_for_stock

        # If val of SPY is too big
        if actual_SPY > desired_SPY:
            # sell SPY till it is back to 98%, 
            # allocate funds to hedge, 
            # use 1/frag to buy puts

            descrepency = actual_SPY - desired_SPY
            if verbose:
                logs.append("Too much SPY")
            # 1) If the liquid allocation can rebalance
            if descrepency <= self.allocated_for_stock:
                self.allocated_for_hedge += descrepency
                self.allocated_for_stock -= descrepency
                if verbose:
                    logs.append("Reallocation from liquid SPY")
            # 2) Start selling SPY shares
            else:
                self.allocated_for_hedge += self.allocated_for_stock
                self.allocated_for_stock = 0
                # Calc descrepency
                actual_SPY = self.get_holding_val("SPY") + self.allocated_for_stock
                descrepency = actual_SPY - desired_SPY
                # shares to sell = math.ceil(descrepency / price)
                SPY_price = self.holdings["SPY"]["price"]
                shares_to_sell = max(0, math.ceil(descrepency / SPY_price))
                # descrepency goes to alloc_hedge and remainder goes to SPY_alloc
                liquid = self.sell_asset("SPY", shares_to_sell)
                self.allocated_for_hedge += descrepency
                self.allocated_for_stock += (liquid - descrepency)
                if verbose:
                    logs.append("Selling " + str(shares_to_sell) + " shares of SPY for " + str(liquid))
            # At this point the value of SPY holdings+allocated_SPY = correct percentage
            # and same for hedge. 
            # TODO sell puts till we have 1/frags 
        else:
            if verbose:
                logs.append("Too little SPY")
                logs.append("Desired: " + str(desired_SPY) + " actual: " + str(actual_SPY))
            descrepency = desired_SPY - actual_SPY
            #  sell Puts till we have 1/frag of 2% in puts, 
            # allocate funds to SPY till it reaches 98%, 
            # allocate remainder to hedge.

            # go through puts, selling till you reach desired value of puts
            # allocate new liquid to SPY
            self.allocated_for_hedge += self.reserved_for_hedge
            self.reserved_for_hedge = 0
            # 1) If we have enough liquid hedge to reblanace
            if descrepency <= self.allocated_for_hedge:
                self.allocated_for_stock += descrepency
                self.allocated_for_hedge -= descrepency
                if verbose:
                    logs.append("Reallocation from liquid hedge bc descrepency was " + str(descrepency))
            # 2) Start selling hedge
            else:
                self.allocated_for_stock += self.allocated_for_hedge
                self.allocated_for_hedge = 0
                logs.append("Allocated for stock = " + str(self.allocated_for_stock))
                # values of puts = assets - actual_SPY 
                actual_SPY = self.get_holding_val("SPY") + self.allocated_for_stock
                portfolio_val = (self.assets + self.cash)
                val_of_puts = portfolio_val - actual_SPY
                # desired val of puts = % * (portfolio_val) / fragments
                desired_val_of_puts = (percent_hedge * portfolio_value)

                count = 0
                for put_position in self.hedge_queue:
                    # if money is larger than descrepency, divy it up, otherwise allocae to SPY
                    actual_SPY = self.get_holding_val("SPY") + self.allocated_for_stock
                    portfolio_val = (self.assets + self.cash)
                    val_of_puts = portfolio_val - actual_SPY
                    descrepency = val_of_puts - desired_val_of_puts
                    if verbose:
                        logs.append("Portfolio: " + str(portfolio_val))
                        logs.append("Actual SPY: " + str(actual_SPY))
                        logs.append("val_of_puts: " + str(val_of_puts))
                        logs.append("desired_val_of_puts: " + str(desired_val_of_puts))
                        logs.append("descrepency: " + str(descrepency))

                    # Sell next position
                    liquid = self.sell_asset(put_position["name"], "ALL")
                    count += 1
                    if verbose:
                        logs.append("Selling " + str(put_position["name"]) + " for $" + str(liquid))
                    if liquid > descrepency:
                        self.allocated_for_stock += descrepency 
                        self.allocated_for_hedge += (liquid - descrepency)
                        if verbose:
                            logs.append("Alocating $" + str(liquid - descrepency) + " to hedge and $" + str(descrepency ) + " to stock")
                        # We have finished
                        break
                    else:
                        self.allocated_for_stock += liquid
                for i in range(count):
                    self.hedge_queue.popleft()
            
        # Before we conclude we must sell more puts such that we are below the 
        # amount for the first fragement of the rebalancing period
        if verbose:
            logs.append("Final stage, selling puts")
        # 1) find the correct amount of non-liquidity
        actual_SPY = self.get_holding_val("SPY") + self.allocated_for_stock
        portfolio_val = (self.assets + self.cash)
        desired_nonliquid_puts_val = (percent_hedge * (portfolio_val)) / self.hedge_fragments
        actual_nonliquid_puts_val = (portfolio_val - actual_SPY) - self.allocated_for_hedge
        if desired_nonliquid_puts_val < actual_nonliquid_puts_val:
            if verbose:
                logs.append("Too much nonliquidity desired=" + str(desired_nonliquid_puts_val) + " actual=" + str(actual_nonliquid_puts_val))
            count = 0
            for put_position in self.hedge_queue:
                # 2) sell a put and move the cash to put liquidity
                liquid = self.sell_asset(put_position["name"], "ALL")
                count += 1
                if verbose:
                    logs.append("Selling " + str(put_position["name"]) + " for $" + str(liquid))
                self.allocated_for_hedge += liquid
                actual_nonliquid_puts_val = (portfolio_val - actual_SPY) - self.allocated_for_hedge
                # 3) compare out non-liquidity to correect non-liquidity
                if desired_nonliquid_puts_val >= actual_nonliquid_puts_val:
                    break
            for i in range(count):
                self.hedge_queue.popleft()
        # Lastly, we need to move enough cash to hedge reserves
        # 1) Caluculate how much belongs in reserves
        desired_cash_in_reserves = ((percent_hedge * portfolio_val) / self.hedge_fragments) * (self.hedge_fragments - 1)
        if verbose:
            logs.append("Moving " + str(desired_cash_in_reserves) + " from allocated to reserved")
        # 2) move that much
        self.reserved_for_hedge += desired_cash_in_reserves
        self.allocated_for_hedge -= desired_cash_in_reserves

        if verbose:
            portfolio_val = self.cash + self.assets
            stocks_val = self.get_holding_val("SPY")
            stocks_liquid = self.allocated_for_stock
            puts_val = self.assets - stocks_val
            puts_liquid = self.allocated_for_hedge
            puts_reserved = self.reserved_for_hedge
            logs.append("Finished with: Portfolio="+str(portfolio_val) + "; SPY stock=" + str(stocks_val) + " liquid=" + str(stocks_liquid) + "; hedge stock=" + str(puts_val) + " liquid=" + str(puts_liquid) + " reserved=" + str(puts_reserved))
            logs.append("Perfectly Balanced!")
       
        return "\n".join(logs)


    def __str__(self):
        output = dict()
        output["cash"] = self.cash
        output["assets"] = self.assets
        output["holdings"] = self.holdings
        output["Allocated Cash"] = {
            "SPY": self.allocated_for_stock,
            "hedge": self.allocated_for_hedge

        }

        return json.dumps(output, indent = 4) 