#!/usr/bin/env python3
import ccxt
import toml
import os
import csv
import datetime
import argparse

def parse_args():
    parser = argparse.ArgumentParser(description="Balance a virtual portfolio between ETH and USDT.")
    parser.add_argument("--verbose", action="store_true", help="Show verbose output.")
    parser.add_argument("--show-history", action="store_true", help="Show portfolio history")
    parser.add_argument("--report-transaction", action="store_true", help="Show verbose output when we trigger a buy or a sell.")
    return parser.parse_args()

def show_history():
    with open("portfolio.csv" , "r") as f:
        print(f.read())

def load_config():
    config_file = "config.toml"
    return toml.load(config_file)

def init_binance(config):
    binance = ccxt.binance({
        "apiKey": config["binance"]["api_key"],
        "secret": config["binance"]["api_secret"],
    })
    return binance

def read_portfolio(config):
    portfolio_file = config["portfolio"]["file"]
    with open(portfolio_file, "r") as f:
        reader = csv.reader(f)
        next(reader)  # skip header
        date, usdt, eth, _, _ = next(reversed(list(reader)))
        return float(usdt), float(eth)

def write_log(date, usdt, eth, detail, fx_rate):
    with open("portfolio.csv", "a") as f:
        writer = csv.writer(f, lineterminator="\n")
        writer.writerow([date, usdt, eth, detail, fx_rate])

def update_portfolio(config, eth_amount, usdt_amount, detail, fx_rate):
    date = datetime.datetime.now().strftime("%Y%m%d")
    write_log(date, usdt_amount, eth_amount, detail, fx_rate)

def balance_portfolio(binance, config, verbose, report_transaction):
    balance_ratio = config["binance"]["balance_ratio"]
    trigger_ratio = config["binance"]["trigger_ratio"]

    usdt_amount, eth_amount = read_portfolio(config)
    eth_price = binance.fetch_ticker("ETH/USDT")["close"]

    total_value = eth_amount * eth_price + usdt_amount

    target_eth = total_value * balance_ratio / eth_price
    target_usdt = total_value * (1 - balance_ratio)

    eth_diff = target_eth - eth_amount
    eth_diff_print = "%0.4f"%eth_diff 

    usdt_diff = target_usdt - usdt_amount

    current_eth_value = eth_amount * eth_price
    target_eth_value = target_eth * eth_price
    abs_diff = abs(current_eth_value - target_eth_value) / total_value
    abs_diff_print = "%0.4f"%abs_diff 

    if verbose:
        report_status(eth_amount, usdt_amount, target_eth, target_usdt, eth_price, abs_diff_print)

    if abs_diff > trigger_ratio:
        if eth_diff > 0:
            order = binance.create_market_buy_order("ETH/USDT", eth_diff)
            detail = f"Buy {eth_diff_print} ETH"
        else:
            order = binance.create_market_sell_order("ETH/USDT", -eth_diff)
            detail = f"Sell {-eth_diff_print} ETH"
                  
        if not verbose and report_transaction:
            report_status(eth_amount, usdt_amount, target_eth, target_usdt, eth_price, abs_diff_print)
        if report_transaction:
            print(f"Transaction executed: {detail}")

        new_eth_amount = target_eth
        new_usdt_amount = target_usdt

        update_portfolio(config, new_eth_amount, new_usdt_amount, detail, eth_price)

def report_status(eth_amount, usdt_amount, target_eth, target_usdt, eth_price, abs_diff_print):
    print(f"ETH amount: {eth_amount}, USDT amount: {usdt_amount}")
    print(f"Target ETH: {target_eth}, Target USDT: {target_usdt}")
    print(f"ETH price: {eth_price}, Absolute difference: {abs_diff_print}")


def main():
    args = parse_args()
    config = load_config()
    binance = init_binance(config)
    if args.show_history:
        show_history()
    else:
        balance_portfolio(binance, config, args.verbose, args.report_transaction)

if __name__ == "__main__":
    main()
