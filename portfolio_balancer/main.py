#!/usr/bin/env python3
import ccxt
import toml
import os
import csv
import datetime
import argparse
from rich import print
from importlib.metadata import version
from decimal import Decimal, ROUND_HALF_UP

def parametric_round(number, significant_digits):
    number = Decimal(str(number))
    exponent = number.adjusted()
    rounded = number.scaleb(-exponent).quantize(Decimal('1.' + '0' * (significant_digits - 1)), rounding=ROUND_HALF_UP)
    return float(rounded.scaleb(exponent))

def smart_round(number):
    number = Decimal(str(number))
    exponent = number.adjusted()
    if exponent >= 0:
        significant_digits = exponent + 1
    else:
        significant_digits = abs(exponent)
    rounded = number.scaleb(-exponent).quantize(Decimal('1.' + '0' * (significant_digits - 1)), rounding=ROUND_HALF_UP)
    return float(rounded.scaleb(exponent))

__version__ = version('portfolio-balancer')

class PortfolioBalancer(object):
    def __init__(self, args) -> None:
        self.args = args
        self.config = self.load_config()
        self.exchange = None
        
        

    def get_config_path(self):
        home = os.path.expanduser("~")
        config_folder = ".portfolio_balancer"

        if os.name == 'nt':  # Windows
            config_folder = "PortfolioBalancer"

        config_dir = os.path.join(home, config_folder)
        os.makedirs(config_dir, exist_ok=True)

        return config_dir, os.path.join(config_dir, "config.toml")

    def load_config(self):
        config_dir, config_file = self.get_config_path()
        config = toml.load(config_file)
        config['config_dir'] = config_dir
        config['currency1'] = config["portfolio"]["currency1"]
        config['currency2'] = config["portfolio"]["currency2"]
        config['base_currency'] = config["portfolio"]["base_currency"]
        return config


    def show_history(self):
        with open(os.path.join(self.config['config_dir'],"portfolio.csv") , "r") as f:
            print(f.read())


    def initPortfolio(self):
        exchange_class = getattr(ccxt, self.config["portfolio"]['exchange'])
        exchange = exchange_class({
            "apiKey": self.config[self.config["portfolio"]['exchange']]["api_key"],
            "secret": self.config[self.config["portfolio"]['exchange']]["api_secret"],
        })
        return exchange

    def read_portfolio(self):
        self.portfolio_file = self.config["portfolio"]["file"]
        self.currency1 = self.config["portfolio"]["currency1"]
        self.currency2 = self.config["portfolio"]["currency2"]
        self.base_currency = self.config["portfolio"]["base_currency"]

        with open(os.path.join(self.config['config_dir'], self.portfolio_file), "r") as f:
            reader = csv.reader(f)
            next(reader)  # skip header
            date, cur1, cur2, _, _, _ = next(reversed(list(reader)))
            return float(cur1), float(cur2)

    def write_log(self, date, cur1, cur2, base,  detail, fx_rate):
        if self.args.dry_run:
            print("Date, Currency1, Currency2, Base Currency, Details, FX rate")
            print(f"{date}, {self.currency1:0.4f}, {self.currency2:0.4f}, {self.base_currency}, {detail}, {fx_rate}")
        else:
            with open(os.path.join(self.config['config_dir'], "portfolio.csv"), "a") as f:
                writer = csv.writer(f, lineterminator="\n")
                writer.writerow([date, smart_round(cur1, 6), smart_round(cur2, 6), base, detail, fx_rate])

    def update_portfolio(self, cur1_amount, cur2_amount, detail, fx_rate):
        date = datetime.datetime.now().strftime("%Y%m%d%H%M%S")
        self.write_log(date, cur1_amount, cur2_amount, self.base_currency, detail, fx_rate)

    def balance_portfolio(self):
        self.exchange = self.initPortfolio()
        balance_ratio = self.config[self.config['portfolio']['exchange']]["balance_ratio"]
        trigger_ratio = self.config[self.config['portfolio']['exchange']]["trigger_ratio"]

        cur1_amount, cur2_amount = self.read_portfolio()  # Change this line
        cur1_ticker = f"{self.currency1}/{self.config['portfolio']['base_currency']}" if self.currency1 != self.config['portfolio']['base_currency'] else "1"
        cur2_ticker = f"{self.currency2}/{self.config['portfolio']['base_currency']}" if self.currency2  != self.config['portfolio']['base_currency'] else "1"
        cur1_price = 1 if cur1_ticker == "1" else self.exchange.fetch_ticker(cur1_ticker)["close"]
        cur2_price = 1 if cur2_ticker == "1" else self.exchange.fetch_ticker(cur2_ticker)["close"]

        total_value = cur1_amount * cur1_price + cur2_amount * cur2_price

        target_cur1 = total_value * balance_ratio / cur1_price
        target_cur2 = total_value * (1 - balance_ratio)

        cur1_diff = target_cur1 - cur1_amount
        cur1_diff_print = "%0.4f" % cur1_diff

        cur2_diff = target_cur2 - cur2_amount

        current_cur1_value = cur1_amount * cur1_price
        target_cur1_value = target_cur1 * cur1_price
        abs_diff = abs((current_cur1_value - target_cur1_value) * cur1_amount / total_value)
        abs_diff_print = "%0.4f" % abs_diff

        if self.args.verbose:
            order = "precondition"
            self.report_status(order, cur1_amount, cur2_amount, target_cur1, target_cur2, cur1_price, cur2_price, abs_diff_print)

        if abs_diff > trigger_ratio:
            order = "dry-run"
            if cur1_diff > 0:
                if not self.args.dry_run:
                    try:
                        order = self.exchange.create_market_buy_order(cur1_ticker, cur1_diff)
                    except ccxt.InsufficientFunds:
                        print(f"Insufficient funds trying to buy {cur1_diff} at {cur1_ticker}")
                        return
                    
                detail = f"Buy {cur1_diff_print} {self.currency1}"
            else:
                if not self.args.dry_run:
                    try:
                        order = self.exchange.create_market_sell_order(cur1_ticker, -cur1_diff)
                    except ccxt.InsufficientFunds:
                        print(f"Insufficient funds trying to sell -{cur1_diff} at {cur1_ticker}")
                        return
                detail = f"Sell -{cur1_diff_print} {self.currency1}"

            if not self.args.verbose and self.args.report_transaction:
                self.report_status(order, cur1_amount, cur2_amount, target_cur1, target_cur2, cur1_price, cur2_price, abs_diff_print)
            if self.args.report_transaction:
                print(f"Transaction executed: {detail}")

            new_cur1_amount = target_cur1
            new_cur2_amount = target_cur2

            self.update_portfolio(new_cur1_amount, new_cur2_amount, detail, cur1_price)

    def exec(self):
        if self.args.show_history:
            self.show_history()
        elif self.args.check:
            self.check_balance()
        else:
            self.balance_portfolio()

    def check_balance(self):
        self.exchange = self.initPortfolio()    
        cur1_amount, cur2_amount = self.read_portfolio()  # Change this line
        cur1_ticker = f"{self.currency1}/{self.config['portfolio']['base_currency']}" if self.currency1 != self.config['portfolio']['base_currency'] else "1"
        cur2_ticker = f"{self.currency2}/{self.config['portfolio']['base_currency']}" if self.currency2  != self.config['portfolio']['base_currency'] else "1"
        cur1_price = 1 if cur1_ticker == "1" else self.exchange.fetch_ticker(cur1_ticker)["close"]
        cur2_price = 1 if cur2_ticker == "1" else self.exchange.fetch_ticker(cur2_ticker)["close"]

        total_value = cur1_amount * cur1_price + cur2_amount * cur2_price
        print(f"Current balance: {total_value:.2f} {self.config['portfolio']['base_currency']}")
        
    def report_status(self, order, cur1_amount, cur2_amount, target_cur1, target_cur2, cur1_price, cur2_price, abs_diff_print):
        print(f"Order: {order}")
        print(f"{self.currency1} amount: {cur1_amount}, {self.currency2} amount: {cur2_amount}")
        print(f"Target {self.currency1}: {target_cur1}, Target {self.currency2}: {target_cur2}")
        print(f"{self.config['portfolio']['currency1']} price: {cur1_price:0.4f}, {self.currency2} price: {cur2_price}, Absolute difference: {abs_diff_print}")

def parse_args():
        parser = argparse.ArgumentParser(description="Balance a virtual portfolio between ETH and USDT.")
        parser.add_argument("--verbose", action="store_true", help="Show verbose output.")
        parser.add_argument("--show-history", action="store_true", help="Show portfolio history")
        parser.add_argument("--exchange", default="binance", help="Exchange to connect to")
        parser.add_argument("--portfolio", default="portfolio.csv", help="Virtual portfolio to balance")
        parser.add_argument("--report-transaction", action="store_true", help="Show verbose output when we trigger a buy or a sell.")
        parser.add_argument("--dry-run", action="store_true", help="Follow the entire logic, just don't send the order and do not log the transaction.")
        parser.add_argument("--version", action="version", version=__version__)
        parser.add_argument("-c", "--check", action="store_true", help="Check the current balance of the portfolio.")
    
        return parser.parse_args()

def main():
    args = parse_args()
    portfolioBalancer = PortfolioBalancer(args)
    portfolioBalancer.exec()
    
if __name__ == "__main__":
    main()
