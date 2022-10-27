import yaml
import sys
# from cli import logger

sys.path.append("site-packages")

from ib_insync import (
    Stock,
    Ticker,
)

def contractForName(sym, exchange="SMART", currency="USD"):
    """Convert a single text symbol into an ib_insync contract."""
    
    return Stock(sym, exchange, currency)


def tickFieldsForContract(contract) -> str:
    extraFields = []
    if isinstance(contract, Stock):
        # 104:
        # "The 30-day historical volatility (currently for stocks)."
        # 106:
        # "The IB 30-day volatility is the at-market volatility estimated
        #  for a maturity thirty calendar days forward of the current trading
        #  day, and is based on option prices from two consecutive expiration
        #  months."
        # 236:
        # "Number of shares available to short"
        # "Shortable: < 1.5, not availabe
        #             > 1.5, if shares can be located
        #             > 2.5, enough shares are available (>= 1k)"
        extraFields += [104, 106, 236]

    # yeah, the API wants a CSV for the tick list. sigh.
    tickFields = ",".join([str(x) for x in extraFields])

    # logger.info("[{}] Sending fields: {}", contract, tickFields)
    return tickFields


def get_stock_price(stock_data: Ticker):
    return stock_data.midpoint()


def extract_data_from_yaml_file(path_to_file):
    with open(path_to_file, "r") as file:
        try:
            return yaml.safe_load(file)
        except yaml.YAMLError as exc:
            logger.info(exc)
            sys.exit()
