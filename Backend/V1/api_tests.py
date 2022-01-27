from Portfolio import Portfolio
import unittest
import math

class TestStringMethods(unittest.TestCase):

    def test_contructor(self):
        portfolio = Portfolio(1000, 0.9, 0.1)
        self.assertEqual(portfolio.cash, 1000)
        self.assertEqual(portfolio.assets, 0)
        self.assertEqual(portfolio.allocated_for_stock, 1000 * 0.9)
        self.assertEqual(portfolio.allocated_for_hedge, 1000 * 0.1)


    def test_buy_stock(self):
        portfolio = Portfolio(1000, 0.9, 0.1)
        self.assertEqual(portfolio.allocated_for_stock, 1000 * 0.9)
        portfolio.buy_stock(30, 20)
        self.assertEqual(portfolio.allocated_for_stock, 1000 * 0.9 - 30 * 20)
        self.assertEqual(portfolio.cash, 1000 - 30 * 20)
        self.assertEqual(portfolio.assets, 30 * 20)
        self.assertEqual(len(portfolio.holdings), 1)
        self.assertEqual(len(portfolio.hedge_queue), 0)

    def test_buy_puts(self):
        portfolio = Portfolio(1000, 0.9, 0.1)
        self.assertEqual(portfolio.allocated_for_hedge, 1000 * 0.1)
        portfolio.buy_puts("test put", 3, 20, {}, "then")
        self.assertEqual(portfolio.allocated_for_hedge, 1000 * 0.1 - 3 * 20)
        self.assertEqual(portfolio.cash, 1000 - 3 * 20)
        self.assertEqual(portfolio.assets, 3 * 20)
        self.assertEqual(len(portfolio.holdings), 1)
        self.assertEqual(len(portfolio.hedge_queue), 1)
        self.assertEqual(portfolio.hedge_queue[0], {"name":"test put", "date":"then"})

    def test_sell_asset(self):
        # initialize portfolio
        portfolio = Portfolio(1000, 0.9, 0.1)
        self.assertEqual(portfolio.allocated_for_hedge, 1000 * 0.1)
        self.assertEqual(portfolio.allocated_for_stock, 1000 * 0.9)
        # purchase assets
        portfolio.buy_puts("test put", 3, 20, {}, "then")
        portfolio.buy_stock(30, 20)
        # make sure purchase was succesful
        self.assertEqual(portfolio.allocated_for_hedge, 40)
        self.assertEqual(portfolio.allocated_for_stock, 300)
        self.assertEqual(portfolio.assets, 660)
        # sell SPY and check porfolio state
        cash = portfolio.sell_asset("SPY", 10)
        self.assertEqual(cash, 300)
        self.assertEqual(portfolio.assets, 360)
        self.assertEqual(portfolio.cash, 640)
        self.assertEqual(portfolio.allocated_for_hedge, 40)
        self.assertEqual(portfolio.allocated_for_stock, 300)
        self.assertEqual(portfolio.holdings["SPY"]["quantity"], 10)
        # make sure puts were not touched
        self.assertEqual(portfolio.holdings["test put"]["quantity"], 20)
        # sell puts
        cash = portfolio.sell_asset("test put", 10)
        self.assertEqual(portfolio.assets, 330)
        self.assertEqual(cash, 30)
        self.assertEqual(portfolio.cash, 670)
        self.assertEqual(portfolio.assets, 330)
        self.assertEqual(portfolio.allocated_for_hedge, 40)
        self.assertEqual(portfolio.allocated_for_stock, 300)
        self.assertEqual(portfolio.holdings["test put"]["quantity"], 10)
        # test sell all
        cash = portfolio.sell_asset("SPY", "ALL")
        self.assertEqual(cash, 300)
        self.assertEqual(portfolio.assets, 30)
        self.assertEqual(portfolio.cash, 970)
        self.assertEqual(portfolio.allocated_for_hedge, 40)
        self.assertEqual(portfolio.allocated_for_stock, 300)
        self.assertEqual("SPY" in portfolio.holdings, False)

    def test_slice_hedge(self):
        # initialize portfolio
        portfolio = Portfolio(1000, 0.9, 0.1)
        self.assertEqual(portfolio.allocated_for_hedge, 1000 * 0.1)
        self.assertEqual(portfolio.allocated_for_stock, 1000 * 0.9)

        # $100 allocated to hedge, 4 fragments
        portfolio.hedge_fragments = 4
        portfolio.reserved_for_hedge = portfolio.allocated_for_hedge
        portfolio.allocated_for_hedge = 0
        val = portfolio.slice_liquid_hedge()
        # There should be 25 in alloc, 3 frags, 75 in reserves
        self.assertEqual(portfolio.allocated_for_hedge, 25)
        self.assertEqual(val, 25)
        self.assertEqual(portfolio.hedge_fragments, 3)
        self.assertEqual(portfolio.reserved_for_hedge, 75)
        

    def test_rebalance(self):
        portfolio = Portfolio(1000, 0.9, 0.1)
        self.assertEqual(portfolio.allocated_for_hedge, 1000 * 0.1)
        self.assertEqual(portfolio.allocated_for_stock, 1000 * 0.9)
        portfolio.hedge_fragments = 1
        # Rebalance a balanced portfolio
        portfolio.rebalance(0.9, 0.1)
        self.assertEqual(portfolio.cash, 1000)
        self.assertEqual(portfolio.assets, 0)
        self.assertEqual(portfolio.allocated_for_hedge, 100)
        self.assertEqual(portfolio.allocated_for_stock, 900)

        # Rebalance with no holdings but different ratio
        portfolio.rebalance(0.8, 0.2)
        self.assertEqual(portfolio.cash, 1000)
        self.assertEqual(portfolio.assets, 0)
        self.assertEqual(portfolio.allocated_for_hedge, 200)
        self.assertEqual(portfolio.allocated_for_stock, 800)

        portfolio.rebalance(0.95, 0.05)
        self.assertEqual(portfolio.cash, 1000)
        self.assertEqual(portfolio.assets, 0)
        self.assertEqual(portfolio.allocated_for_hedge, 50)
        self.assertEqual(portfolio.allocated_for_stock, 950)

        # With holdings, no fragments, too much SPY
        stock_price = 90
        hedge_price = 10
        portfolio = Portfolio(1000, 0.9, 0.1)
        portfolio.hedge_fragments = 1
        stock_quant = portfolio.allocated_for_stock / stock_price
        hedge_quant = portfolio.allocated_for_hedge / hedge_price
        portfolio.buy_stock(stock_price, stock_quant)
        portfolio.buy_puts("test put", hedge_price, hedge_quant, {}, "then")
        self.assertEqual((portfolio.cash + portfolio.assets) * 0.9, portfolio.get_holding_val("SPY"))
        self.assertEqual((portfolio.cash + portfolio.assets) * 0.1, portfolio.get_holding_val("test put"))
        stock_price += 10
        hedge_price -= 10
        portfolio.update_holding("SPY", stock_price)
        portfolio.update_holding("test put", hedge_price)
        self.assertEqual(portfolio.cash + portfolio.assets, stock_price * stock_quant + hedge_price * hedge_quant)
        self.assertNotEqual((portfolio.cash + portfolio.assets) * 0.9, portfolio.get_holding_val("SPY"))
        self.assertNotEqual((portfolio.cash + portfolio.assets) * 0.1, portfolio.get_holding_val("test put"))
        portfolio.rebalance(0.9, 0.1)
        self.assertEqual((portfolio.cash + portfolio.assets) * 0.9, portfolio.get_holding_val("SPY") + portfolio.allocated_for_stock)
        self.assertEqual((portfolio.cash + portfolio.assets) * 0.1, portfolio.get_holding_val("test put") + portfolio.allocated_for_hedge)
        self.assertEqual(portfolio.reserved_for_hedge, 0)

        # no fragments, too little SPY
        stock_price = 90
        hedge_price = 10
        portfolio = Portfolio(1000, 0.9, 0.1)
        portfolio.hedge_fragments = 1
        stock_quant = portfolio.allocated_for_stock / stock_price
        hedge_quant = portfolio.allocated_for_hedge / hedge_price
        portfolio.buy_stock(stock_price, stock_quant)
        portfolio.buy_puts("test put", hedge_price, hedge_quant, {}, "then")
        self.assertEqual((portfolio.cash + portfolio.assets) * 0.9, portfolio.get_holding_val("SPY"))
        self.assertEqual((portfolio.cash + portfolio.assets) * 0.1, portfolio.get_holding_val("test put"))
        stock_price -= 10
        hedge_price += 10
        portfolio.update_holding("SPY", stock_price)
        portfolio.update_holding("test put", hedge_price)
        self.assertEqual(portfolio.cash + portfolio.assets, stock_price * stock_quant + hedge_price * hedge_quant)
        self.assertNotEqual((portfolio.cash + portfolio.assets) * 0.9, portfolio.get_holding_val("SPY"))
        self.assertNotEqual((portfolio.cash + portfolio.assets) * 0.1, portfolio.get_holding_val("test put"))
        portfolio.rebalance(0.9, 0.1)
        self.assertEqual((portfolio.cash + portfolio.assets) * 0.9, portfolio.get_holding_val("SPY") + portfolio.allocated_for_stock)
        self.assertEqual((portfolio.cash + portfolio.assets) * 0.1, portfolio.get_holding_val("test put") + portfolio.allocated_for_hedge)
        self.assertEqual(portfolio.reserved_for_hedge, 0)


        # 4 fragments too much SPY
        stock_price = 90
        hedge_price = 10
        portfolio = Portfolio(1000, 0.9, 0.1)
        portfolio.hedge_fragments = 4
        stock_quant = portfolio.allocated_for_stock / stock_price
        hedge_quant = portfolio.allocated_for_hedge / hedge_price
        portfolio.buy_stock(stock_price, stock_quant)
        portfolio.buy_puts("test put", hedge_price, hedge_quant, {}, "then")
        self.assertEqual((portfolio.cash + portfolio.assets) * 0.9, portfolio.get_holding_val("SPY"))
        self.assertEqual((portfolio.cash + portfolio.assets) * 0.1, portfolio.get_holding_val("test put"))
        stock_price += 10
        hedge_price -= 10
        portfolio.update_holding("SPY", stock_price)
        portfolio.update_holding("test put", hedge_price)
        self.assertEqual(portfolio.cash + portfolio.assets, stock_price * stock_quant + hedge_price * hedge_quant)
        self.assertNotEqual((portfolio.cash + portfolio.assets) * 0.9, portfolio.get_holding_val("SPY"))
        self.assertNotEqual((portfolio.cash + portfolio.assets) * 0.1, portfolio.get_holding_val("test put"))
        portfolio.rebalance(0.9, 0.1)
        self.assertEqual((portfolio.cash + portfolio.assets) * 0.9, portfolio.get_holding_val("SPY") + portfolio.allocated_for_stock)
        self.assertEqual((portfolio.cash + portfolio.assets) * (0.1 / 4), portfolio.get_holding_val("test put") + portfolio.allocated_for_hedge)
        self.assertEqual(portfolio.reserved_for_hedge, math.floor((portfolio.cash + portfolio.assets) * (0.1 * 3 / 4)))

        # 4 fragments, too little SPY
        stock_price = 90
        hedge_price = 10
        portfolio = Portfolio(1000, 0.9, 0.1)
        portfolio.hedge_fragments = 4
        stock_quant = portfolio.allocated_for_stock / stock_price
        hedge_quant = portfolio.allocated_for_hedge / hedge_price
        portfolio.buy_stock(stock_price, stock_quant)
        portfolio.buy_puts("test put", hedge_price, hedge_quant, {}, "then")
        self.assertEqual((portfolio.cash + portfolio.assets) * 0.9, portfolio.get_holding_val("SPY"))
        self.assertEqual((portfolio.cash + portfolio.assets) * 0.1, portfolio.get_holding_val("test put"))
        stock_price -= 10
        hedge_price += 10
        portfolio.update_holding("SPY", stock_price)
        portfolio.update_holding("test put", hedge_price)
        self.assertEqual(portfolio.cash + portfolio.assets, stock_price * stock_quant + hedge_price * hedge_quant)
        self.assertNotEqual((portfolio.cash + portfolio.assets) * 0.9, portfolio.get_holding_val("SPY"))
        self.assertNotEqual((portfolio.cash + portfolio.assets) * 0.1, portfolio.get_holding_val("test put"))
        portfolio.rebalance(0.9, 0.1)
        self.assertEqual((portfolio.cash + portfolio.assets) * 0.9, portfolio.get_holding_val("SPY") + portfolio.allocated_for_stock)
        self.assertEqual((portfolio.cash + portfolio.assets) * (0.1 / 4), portfolio.get_holding_val("test put") + portfolio.allocated_for_hedge)
        self.assertEqual(portfolio.reserved_for_hedge, math.floor((portfolio.cash + portfolio.assets) * (0.1 * 3 / 4)))


if __name__ == '__main__':
    unittest.main()






    


