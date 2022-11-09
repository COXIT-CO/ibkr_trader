from re import I
from taras_trader import helpers

# add lookup pattern to import anything from __init__.py module

from dataclasses import (
    dataclass,
    field,
)

# from taras_trader.app import logger
import oyaml as yaml
import math
import time
import datetime
import threading
from typing import List, Union

from dataclasses import dataclass, field
import datetime

from typing import Union

from dataclasses import dataclass

from taras_trader import helpers
from taras_trader import app

# from helpers import extract_data_from_yaml_file

from ib_insync import (
    IB,
    Stock,
    Ticker,
)
import asyncio

# Configure logger where the ib_insync live service logs get written.
# Note: if you have weird problems you don't think are being exposed
# in the CLI, check this log file for what ib_insync is actually doing.

LIVE_ACCOUNT_STATUS = [
    "TotalCashValue",
]

STATUS_FIELDS = set(LIVE_ACCOUNT_STATUS)


@dataclass
class Stocks:
    # pending_stocks: dict[str, Any] = field(default_factory=dict)
    extracted_data = []
    stocks_being_processed = []
    new_stocks = []
    raw_stocks_data = {}
    current_stock_prices = {}
    stocks_quantity = {}
    stock_tickers = {}
    subscribes_per_stock = {}
    suspended_stocks = {}
    summary = {}
    stop_trigger = False
    stop_write_flag = False
    is_suspended_stocks_processed = False
    ib: IB = field(default_factory=IB)
    loop = None
    accountStatus: dict[str, float] = field(
        default_factory=lambda: dict(
            zip(LIVE_ACCOUNT_STATUS, [0.00] * len(LIVE_ACCOUNT_STATUS))
        )
    )
    # raw_stocks_data: dict = field(default_factory=dict)
    # current_stock_prices: dict[str, int] = field(default_factory=dict)


    @classmethod
    def set_stop_write_flag(cls, data):
        if data is None:
            data = {}
        cls.stop_write_flag = data

    @classmethod
    def set_stocks_quantity(cls, data=None):
        if data is None:
            data = {}
        cls.stocks_quantity = data


    @classmethod
    def set_new_stocks(cls, data=None):
        if data is None:
            data = []
        cls.new_stocks = data

    @classmethod
    def set_current_stock_prices(cls, data=None):
        if data is None:
            data = []
        cls.current_stock_prices = data

    @classmethod
    def set_stop_trigger(cls, value: bool = False):
        cls.stop_trigger = value


    @classmethod
    def set_is_suspended_stocks_processed(cls, value: bool = False):
        cls.is_suspended_stocks_processed = value


    def updateSummary(self, v):
        """Each row is populated after connection then continually
        updated via subscription while the connection remains active."""
        # logger.info("Updating sumary... {}", v)
        # self.summary[v.tag] = v.value

        # regular accounts are U...; sanbox accounts are DU... (apparently)
        # Some fields are for "All" accounts under this login, which don't help us here.
        # TODO: find a place to set this once instead of checking every update?
        # if self.isSandbox is None and v.account != "All":
        #     self.isSandbox = v.account.startswith("D")

        if v.tag in STATUS_FIELDS:
            try:
                self.accountStatus[v.tag] = float(v.value)
            except:
                # don't care, just keep going
                pass


    def set_loop(self, loop):
        self.loop = loop


    @classmethod
    def remove_processed_stock(cls, stock_data):
        cls.stocks_being_processed.remove(stock_data)


    @classmethod
    def process_new_orders(cls, file_to_read):
        # while True:
        # if cls.stop_trigger:
        #     await asyncio.sleep(5)
        #     cls.stop_trigger = False
        cls.raw_stocks_data = helpers.extract_data_from_yaml_file(file_to_read)
        # for stock_data in stocks_to_process:
        #     if stock_data not in cls.stocks_being_processed:

        # await asyncio.sleep(30)
        # continue

        if 'fill' in cls.raw_stocks_data and cls.raw_stocks_data['fill'] == 'on':
            cls.new_stocks = helpers.process_scraped_stock_data(cls.raw_stocks_data)
            # cls.stocks_being_processed = helpers.process_scraped_stock_data(cls.raw_stocks_data)
            # print(cls.raw_stocks_data)
            # print(cls.raw_stocks_data)
            helpers.replace_stocks_being_processed(cls.raw_stocks_data, file_to_read)
            # helpers.write_orders_to_file(cls.new_stocks, file_to_write)
            # cls.write_orders_to_file(cls.stocks_being_processed, file_to_write)
            # helpers.write_orders_to_file(raw_stocks_data, path_to_file)
        # await asyncio.sleep(3)


    @classmethod
    def write_orders_to_file(cls, data_to_write, path_to_file):
        while True:
            cls.stop_trigger = True
            helpers.write_orders_to_file(data_to_write, path_to_file)
            cls.stop_trigger = False


    @staticmethod
    def delete_processed_stocks_from_file(file_path: str) -> dict:
        with open(file_path, "w") as file:
            pass

    def set_ib(self, ib):
        self.ib = ib


    def subscribe_market_data(self):
        """set requesting market data of type 2 (real-time data) 
        https://interactivebrokers.github.io/tws-api/market_data_type.html"""
        self.ib.reqMarketDataType(2)


    def subscribe_stock_market_data(self, stock_symbol):
        """subscribe stock to request market data"""
        contract = Stock(stock_symbol, "SMART", "USD")
        return self.ib.reqMktData(contract, helpers.tickFieldsForContract(contract))


    async def infinitely_get_stock_price(self, symbol):
        """continually get current stock price """
        self.current_stock_prices[symbol] = None
        while True:
            if symbol not in self.stock_tickers:
                break
            self.current_stock_prices[symbol] = self.stock_tickers[symbol].midpoint()
            if math.isnan(self.current_stock_prices[symbol]) or self.current_stock_prices[symbol] <= 0:
                self.current_stock_prices[symbol] = None
            await asyncio.sleep(3)



    @staticmethod
    def get_time_in_seconds():
        time_now = datetime.datetime.now()
        # we include not just nake seconds,
        # but also miliseconds to get more precise representation
        time_now_seconds = time_now.second + time_now.microsecond / 1_000_000
        return time_now_seconds


    async def is_stocks_cost_affordable(self):
        """given all the stocks not yet processed define
        if their total cost affordable having current balance"""
        total_cost = 0
        while True:
            time_1 = self.get_time_in_seconds()
            for stock_symbol, quantities in self.stocks_quantity.items():
                for quantity in quantities:
                    if isinstance(quantity, str) and quantity.startswith("$"):
                        total_cost += int(quantity[1:])
                    else:
                        current_price = await self.get_valid_current_price(stock_symbol)
                        total_cost += current_price * int(quantity)
            time_2 = self.get_time_in_seconds()
            # if it took nore than 10 seconds to calculate total cost 
            # do it again to assure actual stock prices esle return the results
            if time_2 - time_1 <= 10:
                break
            time.sleep(time_2 - time_1)
            time_1 = self.get_time_in_seconds()
            total_cost = 0
        
        return total_cost > self.accountStatus['TotalCashValue'], self.accountStatus['TotalCashValue'], total_cost


        
    def define_start_function_suspended_stocks(self, conditions):
        """depending on the stock conditions define one of 3 function of main algorithm to start from"""
        if 'drop_percent' in conditions and 'rise_percent' in conditions and 'risk_avoidance_percent' in conditions:
            return self.process_stock
        elif 'drop_percent' not in conditions and 'rise_percent' in conditions:
            return self.buy_with_risk_avoidance
        else:
            return self.provide_risk_avoidance



    def set_proper_conditions_order(self, stock_symbol, stock_conditions):
        """set proper stock conditions order cause stock-handling functions
        preserve order"""
        possible_ordered_conditions = (
            'quantity', 'drop_percent', 'trailing-drop-percent', 
            'trailing-up-percent', 'rise_percent', 'percentage-risk-avoidance',
            'risk_avoidance_percent', 'drop_price', 'max_price',
        )

        ordered_stock_conditions = (stock_symbol,)
        for condition in possible_ordered_conditions:
            if condition in stock_conditions:
                ordered_stock_conditions += (stock_conditions[condition],)

        return ordered_stock_conditions



    def process_suspended_stocks(self):
        """
        for every suspended stock set proper conditions order 
        cause all 3 sub-functions of main stock-handling algorithm accept arguments as positional ones in specific order (take a look),
        so it's our task to preserve proper arguments order rather than count on that it's already done (cause yaml i/o operations can mess him),
        then depending on stock conditions determine one of 3 main stock-handling algorithm sub-functions and start stock processing from it
        """
        for stock_data in self.suspended_stocks:
            stock_symbol = list(stock_data.keys())[0]
            conditions = list(stock_data.values())[0]
            # set stock conditions in proper order cause stock-handling functions 
            # are sensitive to arguments order and we aren't allowed to pass arguments as named ones with dictionary
            # cause args parameter https://docs.python.org/3/library/threading.html#threading.Thread supports only
            # list or tuple, so we need to take of care of order by ourself
            ordered_stock_conditions = self.set_proper_conditions_order(stock_symbol, conditions)
            function_to_start_from = self.define_start_function_suspended_stocks(conditions)

            if stock_symbol not in self.subscribes_per_stock or not self.subscribes_per_stock[stock_symbol]:
                self.start_following_stock(stock_symbol)
            self.subscribes_per_stock[stock_symbol] = self.subscribes_per_stock.get(stock_symbol, 0) + 1

            # add stock to general stock info keeping list
            self.stocks_being_processed.append(
                {stock_symbol: conditions}
            )
            
            # process stock in separate thread
            asyncio.create_task(function_to_start_from(*ordered_stock_conditions))
            # threading.Thread(
            #     target=function_to_start_from, 
            #     name="stock_handler", 
            #     args=ordered_stock_conditions
            # ).start()



    def update_stocks_file_info(self, path_to_file):
        """
        update actual stocks info in config file by provided path
        this function is synchronizing which means that if two parts of code try to update info in file
        one of them will wait for other to complete
        """
        while self.stop_write_flag:
            time.sleep(1.5)
        self.set_stop_write_flag(True)
        data_to_dump = []
        for stock_data in self.stocks_being_processed:
            stock_symbol = list(stock_data.keys())[0]
            conditions = list(stock_data.values())[0]
            data_to_dump.append({stock_symbol: [conditions]})
        yaml_representation = yaml.dump(data_to_dump)
        with open(path_to_file, "w") as file:
            file.write(yaml_representation)
        self.set_stop_write_flag(False)


    def extract_suspended_stocks(self, file_path):
        """extract suspended stocks data from config file"""
        self.suspended_stocks = helpers.process_suspended_stocks(
            helpers.extract_data_from_yaml_file(file_path)
        )


    def start_following_stock(self, stock_symbol):
        # start requesting market data about stock and infinitely getting its current price
        self.stock_tickers[stock_symbol] = self.subscribe_stock_market_data(stock_symbol)
        asyncio.create_task(self.infinitely_get_stock_price(stock_symbol))


    def stop_following_stock(self, stock_symbol):
        # if stock with symbol is no more needed cancel requesting market data about it
        # and delete any data related to it
        self.ib.cancelMktData(Stock(stock_symbol, "SMART", "USD"))
        del self.stock_tickers[stock_symbol]
        del self.current_stock_prices[stock_symbol]


    async def run(self):
        """
        starting point to program execution
        """
        self.ib.accountSummaryEvent += self.updateSummary
        # request account info such as balance
        await asyncio.gather(
            self.ib.reqAccountSummaryAsync(),  # self.ib.reqPnLAsync()
        )

        while True:
            if True: #not self.is_suspended_stocks_processed:
                self.extract_suspended_stocks("taras_trader/restore.yaml")
                self.process_suspended_stocks()
                self.set_is_suspended_stocks_processed(True)

            # self.process_new_orders("taras_trader/config_buy.yaml")

            if self.new_stocks:
                for i in range(len(self.new_stocks)):
                    symbol = list(self.new_stocks[i].keys())[0]
                    if symbol not in self.subscribes_per_stock or not self.subscribes_per_stock[symbol]:
                        self.start_following_stock(symbol)
                    self.subscribes_per_stock[symbol] = self.subscribes_per_stock.get(symbol, 0) + 1
                    quantity = list(self.new_stocks[i].values())[0]['quantity']
                    self.stocks_quantity[symbol] = self.stocks_quantity.get(symbol, []) + [quantity]
                
                await asyncio.sleep(0.5)

                does_stocks_cost_exceed_balance, balance_cash, total_stocks_cost = await self.is_stocks_cost_affordable()
                self.set_stocks_quantity()

                if does_stocks_cost_exceed_balance:
                    helpers.replace_stocks_being_processed(
                        self.raw_stocks_data,
                        "taras_trader/config_buy.yaml",
                        total_stocks_cost,
                        balance_cash,
                    )

                    # discard all subscriptions from stocks no more used
                    # and remove them from dictionaries holding their data
                    for stock_symbol in self.subscribes_per_stock.copy():
                        self.subscribes_per_stock[stock_symbol] -= 1
                        if not self.subscribes_per_stock[stock_symbol]:
                            self.stop_following_stock(stock_symbol)
                    
                    self.set_stop_trigger(True)
                else:
                    helpers.replace_stocks_being_processed(
                        self.raw_stocks_data,
                        "taras_trader/config_buy.yaml",
                        are_stocks_accepted=True,
                    )
                
                if not self.stop_trigger:
                    for i in range(len(self.new_stocks)):
                        symbol = list(self.new_stocks[i].keys())[0]
                        stock_conditions = list(self.new_stocks[i].values())[0]
                        args = self.set_proper_conditions_order(symbol, stock_conditions)

                        # threading.Thread(
                        #     target=self.process_stock, 
                        #     name="stock_handler", 
                        #     args=args
                        # ).start()

                        self.stocks_being_processed.append(self.new_stocks[i].copy())

                    self.update_stocks_file_info("taras_trader/restore.yaml")
                    self.set_stop_trigger(False)

                self.set_new_stocks()

            await asyncio.sleep(100000)


    @staticmethod
    def inform_about_unfilled_stock(path_to_file, stock_data, message_to_write):
        """
        if order is not executed within 5 minutes we need to cancel it and 
        notify user about it in config file residing in 'path_to_file'
        """
        # read lines from file to 'lines' and determine the line holding 'fill' word
        lines = []
        line_index_to_insert_comment = 0
        with open(path_to_file, "r") as file:
            counter = 0
            for line in file:
                if 'fill' in line:
                    line_index_to_insert_comment = counter
                lines.append(line)
                counter += 1
        stock_data_to_write = ''
        
        # convert 'stock_data' to yaml and make commented
        for symbol, conditions in stock_data.copy().items():
            del conditions['drop_price']
            stock_data_to_write += f'# - {symbol}\n'
            for condition, value in conditions.items():
                stock_data_to_write += f'#    - {condition}: {value}\n'

        # proper order of new lines to write to file: 
        # actually we insert commented 'stock_data' with warning between previously extracted lines
        lines_to_write = [
            *lines[:line_index_to_insert_comment],
            f"# {message_to_write}",
            stock_data_to_write,
            *lines[line_index_to_insert_comment:],
        ]
        with open(path_to_file, "w") as file:
            file.writelines(lines_to_write)



    async def get_valid_current_price(self, symbol):
        current_stock_price = self.current_stock_prices[symbol]
        
        while self.current_stock_prices[symbol] is None:
            await asyncio.sleep(2.5)
            current_stock_price = self.current_stock_prices[symbol]
        
        return current_stock_price



    @staticmethod
    def find_time_shift(start_time, actual_time):
        """return 3 seconds minus time needed to make one loop iteration ('actual_time' - 'start_time')"""
        time_delta = actual_time - start_time
        time_shift = 3 - (time_delta.seconds + time_delta.microseconds / 1_000_000)
        return time_shift if time_shift > 0 else 0



    async def process_stock(
        self,
        symbol, 
        quantity,
        drop_percent, 
        rise_percent, 
        risk_avoidance_percent,
        previous_max_price=0,
    ):
        """
        starting point of main stock-handling algorithm
        1. continuously get current stock price (every 3 seconds - time needed to make one loop itaration)
        2. if it exceeds last max price than renew it
        3. if it is less than drop price it means that stock dropped 'drop_percent' 
            and we can move to 2 part of all stock-handling algorithm
        important thing is that we write down all the changes to config file
        """
        await asyncio.sleep(0.5)

        # stock properties to compare with
        conditions_to_find = {
            'quantity': quantity,
            'drop_percent': drop_percent,
            'rise_percent': rise_percent,
            'risk_avoidance_percent': risk_avoidance_percent,
        }
        # iterate through stocks holding dictionary and stop when stock data will match above one
        for i in range(len(self.stocks_being_processed)):
            if list(self.stocks_being_processed[i].keys())[0] == symbol:
                if conditions_to_find.items() <= list(self.stocks_being_processed[i].values())[0].items():
                    break

        dict_to_update_info = list(self.stocks_being_processed[i].values())[0]

        max_price = previous_max_price
        drop_price = max_price * ((100 - drop_percent) / 100)

        start_time = datetime.datetime.now()
        while True:
            # get new stock price till it becomes valid
            current_stock_price = await self.get_valid_current_price(symbol)

            if current_stock_price > max_price:
                # update info about stock and write it down to config file
                max_price = current_stock_price
                drop_price = max_price * ((100 - drop_percent) / 100)
                dict_to_update_info['max_price'] = max_price
                self.update_stocks_file_info("taras_trader/restore.yaml")

            if current_stock_price <= drop_price:
                # update info about stock, write it down to config file and move to 2 part of main alforithm
                del dict_to_update_info["max_price"]
                del dict_to_update_info["drop_percent"]
                dict_to_update_info['drop_price'] = drop_price
                self.update_stocks_file_info("taras_trader/restore.yaml")

                asyncio.create_task(
                    self.buy_with_risk_avoidance(
                        symbol,
                        quantity,
                        rise_percent,
                        risk_avoidance_percent,
                        drop_price,
                    )
                )
                break
            
            await asyncio.sleep(self.find_time_shift(start_time, datetime.datetime.now()))
            start_time = datetime.datetime.now()



    async def check_for_order_to_fill(
        self, trade, order, start_time
    ):
        """check for order to fill within 5 minutes otherwise cancel it"""
        while trade.log[-1].status != "Filled":
            time_difference = self.find_time_shift(start_time, datetime.datetime.now())
            if time_difference >= 300:
                self.ib.cancelOrder(order)
                return False
            await asyncio.sleep(1.5)
        return True



    async def buy_with_risk_avoidance(
        self, 
        symbol, 
        quantity,  
        rise_percent, 
        risk_avoidance_percent, 
        drop_price,
    ):
        """
        2 part of main stock-handling algorithm
        1. continuously get current stock price (every 3 seconds - time needed to make one loop itaration)
        2. if it exceeds rise price it means stock rose, 
            so we need to place the order to exchange, check if is accepted for 5 minutes:
            1) in case of failure cancel it and inform user about that in config file
            2) else update info about stock and got to final part of main stock-handling algorithm
        important thing is that we write down all the changes to config file
        """
        await asyncio.sleep(0.5)
        rise_price = drop_price * (1 + (rise_percent / 100))

        conditions_to_find = {
            'quantity': quantity,
            'rise_percent': rise_percent,
            'risk_avoidance_percent': risk_avoidance_percent,
            'drop_price': drop_price,
        }
        for i in range(len(self.stocks_being_processed)):
            if list(self.stocks_being_processed[i].keys())[0] == symbol:
                if conditions_to_find.items() <= list(self.stocks_being_processed[i].values())[0].items():
                    break

        dict_to_update_info = list(self.stocks_being_processed[i].values())[0]
        
        start_time = datetime.datetime.now()
        while True:
            current_stock_price = await self.get_valid_current_price(symbol)

            if current_stock_price >= rise_price:
                # buy stock as a limit with price of 102 percent of current price to fill the order immediately
                # (actually we buy it with 100 percent of current price, 102 percent is just a detour to immediate buy
                # cause ibkr doesn't buy 100 percent price orders promptly (market orders))
                order, trade = await place_order(
                        symbol, True, quantity, lmt=current_stock_price * 1.02,
                    )
                is_order_executed = await self.check_for_order_to_fill(
                    symbol, quantity, trade, order, datetime.datetime.now(),
                )
                if not is_order_executed:
                    self.inform_about_unfilled_stock(
                        "taras_trader/config_buy.yaml",
                        self.stocks_being_processed[i],
                        "ATTERNTION!!! order was pending fill for more than 5 minutes, so isn't executed\n"
                    )
                    del self.stocks_being_processed[i]
                    return

                del dict_to_update_info["drop_price"]
                del dict_to_update_info["rise_percent"]
                max_price = current_stock_price
                dict_to_update_info['max_price'] = max_price
                self.update_stocks_file_info("taras_trader/restore.yaml")

                asyncio.create_task(
                    self.provide_risk_avoidance(
                        symbol, quantity, risk_avoidance_percent, max_price,
                    )
                )
                break
            
            await asyncio.sleep(self.find_time_shift(start_time, datetime.datetime.now()))
            start_time = datetime.datetime.now()



    async def provide_risk_avoidance(
        self, symbol, quantity, risk_avoidance_percent, max_price=0, 
    ):
        """
        final part of main stock-handling algorithm
        1. continuously get current stock price (every 3 seconds - time needed to make one loop itaration)
        2. if it exceeds last max price than renew it
        3. if it dropped 'risk_avoidance_percent' it means we need to immediately sell it
        important thing is that we write down all the changes to config file
        """
        await asyncio.sleep(0.5)
        conditions_to_find = {
            'quantity': quantity,
            'risk_avoidance_percent': risk_avoidance_percent,
            'max_price': max_price,
        }
        for i in range(len(self.stocks_being_processed)):
            if list(self.stocks_being_processed[i].keys())[0] == symbol:
                if conditions_to_find.items() <= list(self.stocks_being_processed[i].values())[0].items():
                    break

        dict_to_update_info = list(self.stocks_being_processed[i].values())[0]
        
        alert_price = max_price * ((100 - risk_avoidance_percent) / 100)

        start_time = datetime.datetime.now()
        while True:
            current_price = self.get_valid_current_price(symbol)

            if current_price > max_price:
                # update info about stock and write it down to config file
                max_price = current_price
                dict_to_update_info['max_price'] = max_price
                self.update_stocks_file_info("taras_trader/out.yaml")
                alert_price = max_price * ((100 - risk_avoidance_percent) / 100)

            if current_price <= alert_price:
                # sell stock as a limit with price of 98 percent of current price to fill the order immediately
                # (actually we sell it with 100 percent of current price, 98 percent is just a detour to immediate sell
                # cause ibkr doesn't sell 100 percent price orders promptly (market orders))
                order, trade = await place_order(
                    symbol, False, quantity, "LMT", current_price * 0.98
                )
                del self.stocks_being_processed[i]
                self.update_stocks_file_info("taras_trader/out.yaml")

                break
            
            await asyncio.sleep(self.find_time_shift(start_time, datetime.datetime.now()))
            start_time = datetime.datetime.now()
        


async def place_order(
    symbol,
    action: bool,
    quantity,
    order_type,
    lmt=0,
):
    """
    place order to the exhange
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
        action, 
        contract, 
        quantity,
        lmt,
        order_type,
    )
    return trade
