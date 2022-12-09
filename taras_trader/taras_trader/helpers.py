import sys
import collections
import oyaml as yaml
from ib_insync import Stock
import datetime
from typing import Literal
from . import app
import asyncio


def contractForName(sym, exchange="SMART", currency="USD"):
    """Convert a single text symbol into an ib_insync contract."""
    return Stock(sym, exchange, currency)



def tickFieldsForContract(contract) -> str:
    """return set of tick fields according to which the stock actual data will be received"""
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



def extract_data_from_yaml_file(path_to_file):
    with open(path_to_file, "r") as file:
        try:
            return yaml.safe_load(file)
        except yaml.YAMLError as exc:
            logger.info(exc)
            sys.exit()


def write_orders_to_file(stocks_data: dict, file_path: str) -> None:
    yaml_representation = yaml.dump(stocks_data)
    with open(file_path, "w") as file:
        file.write(yaml_representation)


def process_scraped_stock_data(data_to_process):
    """given data of stocks to be processed return it in convenient way"""
    processed_data = []

    for item in data_to_process['order']['buy']:
        for stock in item['stocks']:
            stock_symbol = list(stock.keys())[0]
            stock_info = {stock_symbol: {}}
            try:
                stock_info[stock_symbol]["quantity"] = float(list(stock.values())[0])
            except ValueError:
                stock_info[stock_symbol]["quantity"] = str(list(stock.values())[0])
            stock_info[stock_symbol]["drop_percent"] = float(item['conditions'][1]['trailing-drop-percent'])
            stock_info[stock_symbol]["rise_percent"] = float(item['conditions'][2]['trailing-up-percent'])
            stock_info[stock_symbol]["risk_avoidance_percent"] = float(data_to_process['order']['sell'][1]['trailing-drop-percent'])
            processed_data.append(stock_info)

    return processed_data



def reformat_stocks(data):
    """given the stocks data return it in convenient format"""
    for i, stock_data in enumerate(data):
        data[i]['drop_percent'] = stock_data['drop-percent']
        del data[i]['drop-percent']
        data[i]['up_percent'] = stock_data['up-percent']
        del data[i]['up-percent']
        data[i]['sell_percent'] = stock_data['sell-percent']
        del data[i]['sell-percent']



def get_time_in_seconds():
    time_now = datetime.datetime.now()
    # we include not just nake seconds,
    # but also miliseconds to get more precise representation
    time_now_seconds = time_now.second + time_now.microsecond / 1_000_000
    return time_now_seconds



async def place_order(
    symbol,
    action: Literal["buy", "sell"],
    quantity,
    order_type,
    lmt=0,
):
    """
    place order to the exchange
    Parameters
    ----------
    symbol: str
        Stock name
    action: bool
        True - buy, False - sell
    quantity: int | str
        quantity, can be integer or string of form '$X' where X - price in dollars
    order_type: str
        in our case only LMT literal is used as argument
    lmt:
        desired price
    """
    contract = Stock(symbol, "SMART", "USD")
    trade = await app.app.placeOrderForContract(
        symbol, 
        True if action == "buy" else False, 
        contract, 
        quantity,
        lmt,
        order_type,
    )
    return trade


def is_stock_used(stock_name, stocks):
    return any(
        [stock_data['stock'] == stock_name for stock_data in stocks]
    )


def find_timedelta(start_time, actual_time):
    """return timedelta between current time and previous one"""
    time_delta = actual_time - start_time
    return time_delta.seconds + time_delta.microseconds / 1_000_000


def sleep_some_time(time_delta, total_seconds):
    """given total seconds and timedelta return their difference
    which will correspond time needed to sleep to new loop iteration
    where this function is used"""
    time_difference = total_seconds - time_delta
    return time_difference if time_difference > 0 else 0


def find_stock_occurencies(stock_name, stocks):
    """find how much times stock with provided name
    is encountered in stocks-holding list"""
    occurencies = 0
    for stock_data in stocks:
        if stock_data['name'] == stock_name:
            occurencies += 1
        if occurencies > 1:
            return occurencies
