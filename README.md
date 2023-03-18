# Crypto Portfolio Balancer

Crypto Portfolio Balancer is a Python script that helps you balance your cryptocurrency portfolio between two specified currencies using the Binance API. It reads the target balance ratio and other settings from a configuration file and can handle three currencies with a specified base currency. It can also handle the case where the base currency is equal to one of the other currencies.

## Features

- Balances your virtual portfolio between two cryptocurrencies
- Reads configuration from a TOML file
- Supports three currencies with a specified base currency
- Can handle the case where the base currency is equal to one of the other currencies
- Shows the history of your portfolio
- Reports transaction details when executed

## Installation

1. Clone this repository or download the source code.
2. Install Python 3 if you haven't already.
3. Install the required packages using the following command:

```bash
pip install -r requirements.txt
poetry build
pip install -U dist/portfolio_balancer-0.1.0-py3-none-any.whl
```

## License
This project is licensed under the MIT License. See the LICENSE file for more information.


