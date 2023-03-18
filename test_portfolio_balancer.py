
#!/usr/bin/env python3
import os
import unittest
from portfolio_balancer import PortfolioBalancer
from argparse import Namespace


class TestPortfolioBalancer(unittest.TestCase):

    def setUp(self):
        args = Namespace(show_history=False, verbose=False, exchange='binance', portfolio='portfolio.csv', report_transaction=False)
        self.portfolio_balancer = PortfolioBalancer(args)

    def test_load_config(self):
        config = self.portfolio_balancer.load_config()
        self.assertIsNotNone(config)
        self.assertIn('config_dir', config)
        self.assertIn('portfolio', config)
        self.assertIn('currency1', config)
        self.assertIn('currency2', config)
        self.assertIn('base_currency', config)

    def test_get_config_path(self):
        config_dir, config_file = self.portfolio_balancer.get_config_path()
        self.assertIsNotNone(config_dir)
        self.assertIsNotNone(config_file)
        self.assertTrue(os.path.exists(config_dir))

    def test_read_portfolio(self):
        cur1_amount, cur2_amount = self.portfolio_balancer.read_portfolio()
        self.assertIsNotNone(cur1_amount)
        self.assertIsNotNone(cur2_amount)
        self.assertTrue(isinstance(cur1_amount, float))
        self.assertTrue(isinstance(cur2_amount, float))

if __name__ == '__main__':
    unittest.main()
