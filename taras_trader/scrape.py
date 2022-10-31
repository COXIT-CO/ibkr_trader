from typing import OrderedDict
import yaml
import sys
sys.path.append("site-packages")
sys.path.append("..")
import time
import requests
import os
from taras_trader import helpers
# from cli import IBKRCmdlineApp as cmdline
from ib_insync import Stock
import collections
import oyaml as yaml

# os.environ["NO_PROXY"] = "127.0.0.1"

# import ssl

# try:
#     _create_unverified_https_context = ssl._create_unverified_context
# except AttributeError:
#     # Legacy Python that doesn't verify HTTPS certificates by default
#     pass
# else:
#     # Handle target environment that doesn't support HTTPS verification
#     ssl._create_default_https_context = _create_unverified_https_context

extracted_data = None

def extract_data_from_yaml_file(path: str) -> dict:
    """function to extact content to dictionary 
    from yaml file residing on privided path
        Parameters:
            path (str): path to the file to extact data from"""
    stream = open(path, 'r')
    try:
        scraped_data = yaml.safe_load(stream)
        # print(parsed_data.get("fill", True))
        # print(parsed_data["fill"] != "on")
        if "fill" not in scraped_data or scraped_data["fill"] != "on":
            return None
    except yaml.YAMLError as exc:
        print(exc)
        sys.exit()

    return scraped_data
    # for key, value in dictionary.items():
    #     print(key + " : " + str(value))

# extracted_data = extract_data_from_yaml_file("config_buy.yaml")
# print(extracted_data)
# print(extracted_data['order']['stocks'])


# def remove_stocks_being_processed(data: dict) -> dict:
#     """when we extracted data from config file we need to remove it from there and put empty data,
#     so we split task on two parts: delete data from dictionary holding all info about them after what
#     delete data from yaml file, convert this dictionary to yaml format and write it back to file"""

#     data['order']['buy'] = ""
#     data['order']['sell'] = ""

#     print(yaml.dump(data))

# remove_stocks_being_processed(extracted_data)

def replace_stocks_being_processed(
    stocks_data, 
    file_path, 
    stocks_cost=0, 
    balance_cash=0, 
    are_stocks_accepted: bool = False
):
    patterns_dump_to_file = [collections.OrderedDict([
        ('fill', 'off'), 
        ('warning', 
    "previous stocks are being processed, please, don't put other ones until this title dissapears"),
        ('order', {
            'buy': [
                {"stocks": ""}, 
                {"conditions": ""}
            ], 
            'sell': [
                {"stocks": ""}, 
                {"conditions": ""}
            ]
            }
        )
    ]), collections.OrderedDict([
        ('fill', 'off'), 
        ('order', {
            'buy': [
                {"stocks": ""}, 
                {"conditions": ""}
            ], 
            'sell': [
                {"stocks": ""}, 
                {"conditions": ""}
            ]
            }
        )
    ]), collections.OrderedDict([
        ('fill', 'off'), 
        ('warning', 
    f"stocks haven't been processes cause their price exceeds balance cash, \nstocks averall price - {stocks_cost}, balance cash -{balance_cash}, \nif you still want to proceed these stocks, please, consider their quantity"),
    ])]

    if are_stocks_accepted:
        data_to_dump = patterns_dump_to_file[1]
    elif stocks_cost and balance_cash:
        stocks_data_copy = stocks_data.copy()
        del stocks_data_copy['fill']
        patterns_dump_to_file[2].update(OrderedDict(stocks_data_copy))
        data_to_dump = patterns_dump_to_file[2]
    else:
        data_to_dump = patterns_dump_to_file[0]
    # if stocks_data is None or "fill" not in stocks_data or stocks_data["fill"] != "on":
    #     return None

    # data_to_dump['fill'] = "off"
    # data_to_dump['warning'] = "previous stocks are being processed, please, don't put other ones untill this title dissapears"
    # data_to_dump['order']['buy'] = [{"stocks": ""}, {"conditions": ""}]
    # data_to_dump['order']['sell'] = [{"stocks": ""}, {"conditions": ""}]
    with open(file_path, "r") as file:
        lines = file.readlines()

    with open(file_path, "w") as file:
        for line in lines:
            if line.startswith("\n") or line.strip("\n").startswith("#"):
                file.write(line)
        
        file.write(yaml.dump(data_to_dump))


def delete_processed_stocks_from_file(data_to_replace: dict, file_path: str) -> dict:
    if data_to_replace is None or "fill" not in data_to_replace or data_to_replace["fill"] != "on":
        return None
    data_to_replace = collections.OrderedDict([
        ('fill', 'off'), 
        ('warning', 
    "previous stocks are being processed, please, don't put other ones untill this title dissapears"),
        ('order', {
            'buy': [
                {"stocks": ""}, 
                {"conditions": ""}
            ], 
            'sell': [
                {"stocks": ""}, 
                {"conditions": ""}
            ]
            }
        )
    ])
    # data_to_replace['fill'] = "off"
    # data_to_replace['warning'] = "previous stocks are being processed, please, don't put other ones untill this title dissapears"
    # data_to_replace['order']['buy'] = [{"stocks": ""}, {"conditions": ""}]
    # data_to_replace['order']['sell'] = [{"stocks": ""}, {"conditions": ""}]
    with open(file_path, "r") as file:
        lines = file.readlines()

    with open(file_path, "w") as file:
        for line in lines:
            if line.startswith("\n") or line.strip("\n").startswith("#"):
                file.write(line)
        
        file.write(yaml.dump(data_to_replace))

# delete_processed_stocks_from_file(extracted_data, "../config_buy.yaml")


# import app
import asyncio
import time

# tickFields = tickFieldsForContract()

async def a():
    contract = Stock("AAPL", "SMART", "USD")
    app.app.ib.qualifyContracts(contract)
    data = app.app.ib.reqMktData(contract)
    print(data.marketPrice())
    # app.app.ib.reqMarketDataType(2)
    # q = app.app.ib.reqMktData(Stock("SPY", "SMART", "USD"), tickFields)
    # time.sleep(10)
    # show = [
    #         f"{q.contract.symbol}: bid {q.bid} x {q.bidSize}",
    #         f"ask {q.ask} x {q.askSize}",
    #         f"mid {q.bid}",
    #         f"last {q.last} x {q.lastSize}",
    #     ]

    # print(show)

# asyncio.run(a())


def setup_yaml():
    """ https://stackoverflow.com/a/8661021 """
    represent_dict_order = lambda self, data:  self.represent_mapping('tag:yaml.org,2002:map', data.items())
    yaml.add_representer(collections.OrderedDict, represent_dict_order)  

# setup_yaml()

def get_current_stock_price(symbol: str) -> int:
    """return contract identifier for stock by provided symbol"""

    tickFields = helpers.tickFieldsForContract()
    # print(app.app.ib.reqMktData(Stock(symbol, "SMART", "USD"), tickFields))
    
    url = "https://localhost:5000/v1/api/iserver/secdef/search"
    # print(requests.post(url=url, json={"symbol": symbol}, verify=False).json()[0]['conid'])

    conid = int(requests.post(url=url, json={"symbol": symbol}, verify=False).json()[0]['conid'])

    stock_price = float(requests.post(url="https://localhost:5000/v1/api/iserver/contract/rules", json={"conid": str(conid), "isBuy": True}, verify=False).json()['limitPrice'])

    return stock_price

# get_current_stock_price('tsla')

# a = get_current_stock_price("msft")
# print(a, type(a))

def ping_server():
    url = "https://localhost:5000/v1/api/tickle"

    requests.post(url=url, verify=False)


def reauthenticate():
    url = "https://localhost:5000/v1/api/iserver/reauthenticate"

    requests.post(url=url, verify=False)


def write_orders_to_file(stocks_data: dict, file_path: str) -> None:
    yaml_representation = yaml.dump(stocks_data)
    with open(file_path, "w") as file:
        file.write(yaml_representation)


def write_orders_back(stocks_data: dict, file_path: str):
    yaml_representation = yaml.dump(stocks_data)
    with open(file_path, "w") as file:
        file.write(yaml_representation)


def process_scraped_stock_data(data_to_process):
    # del data_to_process['fill']
    processed_data = []

    for item in data_to_process['order']['buy']:
        # print(item['stocks'])
        for stock in item['stocks']:
            stock_symbol = list(stock.keys())[0]
            stock_info = {stock_symbol: {}}
            try:
                stock_info[stock_symbol]["quantity"] = int(list(stock.values())[0])
            except:
                stock_info[stock_symbol]["quantity"] = str(list(stock.values())[0])
            stock_info[stock_symbol]["drop_percent"] = float(item['conditions'][1]['trailing-drop-percent'])
            stock_info[stock_symbol]["rise_percent"] = float(item['conditions'][2]['trailing-up-percent'])
            stock_info[stock_symbol]["risk_avoidance_percent"] = float(data_to_process['order']['sell'][1]['trailing-drop-percent'])
            processed_data.append(stock_info)

    return processed_data


def process_suspended_stocks(data):
    processed_data = []

    for item in data:
        symbol = list(item.keys())[0]
        conditions = list(item.values())[0][0]
        processed_data.append(
            {symbol: conditions},
        )

    return processed_data

# print(write_orders_to_file(extracted_data, "../out.yaml"))

# place_orders(extracted_data)

# delete_processed_stocks_from_file(extracted_data, "../config.yaml")

    # final_data = yaml.dump(data_to_replace)
    # file = open(file_path, "w")

# def are_dictionaries_equal(dict1: dict, dict2: dict):
#     return dict1 == dict2

# print(get_current_stock_price("MSFT"))

# while True:
#     extracted_data = extract_data_yaml_file("../config.yaml")
#     print(extracted_data)
#     delete_processed_stocks_from_file(extracted_data, "../config.yaml")
#     time.sleep(3)
# exctracted_data_2 = extract_data_yaml_file("../config-test.yaml")
# print(extracted_data)
# print(exctracted_data_2)
# print(yaml.dump(extracted_data))