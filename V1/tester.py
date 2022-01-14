from Portfolio import Portfolio
import math

portfolio = Portfolio(10000, 0.9, 0.1)

print(portfolio)

# Stock price 1 = 100, Put price = 30
# Stock price 2 = 300, Put price = 3

# Buy as much stock and puts as we can
stock_price = 100

put_prices = [3, 4, 5, 6]

stock_quantity = math.floor(portfolio.allocated_for_stock / stock_price)
portfolio.buy_stock(100, stock_quantity)

for n in range(len(put_prices)):
    snippet = portfolio.allocated_for_hedge / len(put_prices)
    put_quantity = math.floor( snippet / put_prices[n])
    portfolio.buy_puts("TESTPUT" + str(n), put_prices[n], put_quantity, dict(), "then")

last_put = 7
snippet = portfolio.allocated_for_hedge 
put_quantity = math.floor( snippet / last_put)
portfolio.buy_puts("TESTPUT" + str(4), last_put, put_quantity, dict(), "then")



print(portfolio)



stock_price = 300
portfolio.update_holding("SPY", stock_price)
put_prices = [1, 2, 3, 4,5]

for n in range(len(put_prices)):
    portfolio.update_holding("TESTPUT" + str(n), put_prices[n])


print(portfolio)

portfolio.hedge_fragments = 1
logs = portfolio.rebalance(0.9, 0.1)

print(logs)

print(portfolio)
