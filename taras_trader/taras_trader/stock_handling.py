from . import helpers

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
from typing import List, Literal, Union

from dataclasses import dataclass, field
import datetime

from typing import Union

from dataclasses import dataclass

from . import app

# from helpers import extract_data_from_yaml_file

from ib_insync import (
    IB,
    Stock,
    Ticker,
)
import asyncio
import requests

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
    stocks_being_processed = []
    stock_prices = {}
    stock_tickers = {}
    subscribes_per_stock = {}
    suspended_stocks = {}
    is_file_avaliable = True
    ib: IB = field(default_factory=IB)
    accountStatus: dict[str, float] = field(
        default_factory=lambda: dict(
            zip(LIVE_ACCOUNT_STATUS, [0.00] * len(LIVE_ACCOUNT_STATUS))
        )
    )
    # raw_stocks_data: dict = field(default_factory=dict)
    # stock_prices: dict[str, int] = field(default_factory=dict)


    @classmethod
    def set_is_file_avaliable(cls, data):
        if data is None:
            data = {}
        cls.is_file_avaliable = data

    @classmethod
    def set_stock_prices(cls, data=None):
        if data is None:
            data = []
        cls.stock_prices = data


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


    @classmethod
    def remove_processed_stock(cls, stock_data):
        cls.stocks_being_processed.remove(stock_data)


    @classmethod
    def get_new_stocks(cls, file_to_read):
        stocks = helpers.extract_data_from_yaml_file(file_to_read)
        if stocks:
            helpers.reformat_stocks(stocks)
            return stocks


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
        self.stock_prices[symbol] = None
        while True:
            price = self.stock_tickers[symbol].midpoint()
            self.stock_prices[symbol] = None if (math.isnan(price) or price <= 0) else price
            await asyncio.sleep(3)


    async def are_stocks_affordable(self, new_stocks):
        """given all the stocks not yet processed define
        if their total cost affordable having current balance"""
        total_cost = 0
        while True:
            start_time = datetime.datetime.now()
            for stock_data in new_stocks:
                quantity = stock_data['quantity']
                if isinstance(quantity, str) and quantity.startswith("$"):
                    total_cost += int(quantity[1:])
                else:
                    current_price = await self.get_valid_price(stock_data['stock'])
                    total_cost += current_price * int(quantity)

            elapsed_time = helpers.find_timedelta(start_time, datetime.datetime.now())
            # if it took nore than 10 seconds to calculate total cost 
            # do it again to assure actual stock prices esle return the results
            if elapsed_time and elapsed_time <= 10:
                break
            await asyncio.sleep(elapsed_time)
            total_cost = 0
        
        return total_cost > self.accountStatus['TotalCashValue'], self.accountStatus['TotalCashValue'], total_cost


        
    def define_start_function(self, conditions):
        """depending on the stock conditions define one of 3 functions of main algorithm to start with"""
        if 'drop_percent' in conditions and 'up_percent' in conditions and 'sell_percent' in conditions:
            return self.check_drop
        elif 'drop_percent' not in conditions and 'up_percent' in conditions:
            return self.buy_with_risk_avoidance
        else:
            return self.provide_risk_avoidance



    async def process_suspended_stocks(self, suspended_stocks):
        """
        for every suspended stock set proper conditions order 
        cause all 3 sub-functions of main stock-handling algorithm accept arguments as positional ones in specific order (take a look),
        so it's our task to preserve proper arguments order rather than count on that it's already done (cause yaml i/o operations can mess it),
        then depending on stock conditions determine one of 3 main stock-handling algorithm sub-functions and start stock processing from it
        """
        for stock_data in suspended_stocks:
            stock_name = stock_data['stock']
            # set stock conditions in proper order cause stock-handling functions 
            # are sensitive to arguments order and we aren't allowed to pass arguments as named ones with dictionary
            # cause args parameter https://docs.python.org/3/library/threading.html#threading.Thread supports only
            # list or tuple, so we need to take of care of order by ourself
            start_func = self.define_start_function(stock_data)

            # if stock isn't used yet start following it by making subscription 
            # and infinitely getting its price
            if not helpers.is_stock_used(stock_name, self.stocks_being_processed):
                await self.start_following_stock(stock_name)

            # add stock to general stocks-holding list
            self.stocks_being_processed.append(stock_data)
            
            asyncio.create_task(start_func(**stock_data))


    async def update_restore_file(self, path_to_file):
        """
        update actual stocks info in config file by provided path
        this function is synchronizing which means that if two parts of code try to update info in file
        one of them will wait for other to complete
        """
        while not self.is_file_avaliable:
            await asyncio.sleep(0.5)
        self.set_is_file_avaliable(False)
        yaml_representation = yaml.dump(self.stocks_being_processed)
        with open(path_to_file, "w") as file:
            file.write(yaml_representation)
        self.set_is_file_avaliable(True)


    def extract_suspended_stocks(self, file_path):
        """extract suspended stocks data from config file"""
        try:
            suspended_stocks = helpers.extract_data_from_yaml_file(file_path)
            helpers.reformat_stocks(suspended_stocks)
            return suspended_stocks
        except FileNotFoundError:
            # if restore file is not found it means we launch the program for the first time
            pass


    async def start_following_stock(self, stock_symbol):
        # start requesting market data about stock and infinitely getting its current price
        self.stock_tickers[stock_symbol] = self.subscribe_stock_market_data(stock_symbol)
        # ticker needs some time to populate its fields
        await asyncio.sleep(0.5)
        asyncio.create_task(self.infinitely_get_stock_price(stock_symbol))


    def stop_following_stock(self, stock_symbol):
        # if stock with symbol is no more needed cancel requesting market data about it
        # and delete any data related to it
        self.ib.cancelMktData(Stock(stock_symbol, "SMART", "USD"))
        del self.stock_tickers[stock_symbol]
        del self.stock_prices[stock_symbol]


    async def run(self):
        """
        starting point to program execution
        """
        self.ib.accountSummaryEvent += self.updateSummary
        # request account info such as balance
        await asyncio.gather(
            self.ib.reqAccountSummaryAsync(),  # self.ib.reqPnLAsync()
        )

        # process suspended stocks if are so
        await self.process_suspended_stocks(
            self.extract_suspended_stocks("taras_trader/restore.yaml")
        )

        while True:
            start_time = datetime.datetime.now()
            new_stocks = self.get_new_stocks("taras_trader/config.yaml")

            if new_stocks:
                for stock_data in new_stocks:
                    stock_name = stock_data['stock']
                    if not helpers.is_stock_used(stock_name, self.stocks_being_processed):
                        await self.start_following_stock(stock_name)
                
                are_stocks_affordable, balance_cash, stocks_cost = await self.are_stocks_affordable(new_stocks)
                helpers.send_response(stocks_cost, balance_cash)

                if not are_stocks_affordable:
                    # discard all subscriptions from stocks no more used
                    # and remove them from dictionaries holding their data
                    for stock_data in new_stocks:
                        stock_name = stock_data['stock']
                        if helpers.find_stock_occurencies(stock_name, self.stocks_being_processed) > 1:
                            self.stop_following_stock(stock_name)
                else:                
                    for stock_data in new_stocks:
                        self.stocks_being_processed.append(stock_data)
                        asyncio.create_task(self.check_drop(**stock_data))

                    self.update_restore_file("taras_trader/restore.yaml")
            
            await asyncio.sleep(
                helpers.sleep_some_time(
                    helpers.find_timedelta(start_time, datetime.datetime.now()), 10
                )
            )



    async def get_valid_price(self, symbol):
        current_price = self.stock_prices[symbol]
        
        while self.stock_prices[symbol] is None:
            await asyncio.sleep(2.5)
            current_price = self.stock_prices[symbol]
        
        return current_price



    async def check_drop(
        self,
        stock, 
        quantity,
        drop_percent, 
        up_percent, 
        sell_percent,
        max_price=0,
        **kwargs
    ):
        """
        starting point of main stock-handling algorithm
        Here we continuously get current stock price every (3 seconds - time needed to make one loop iteration),
        so one iteration takes exactly 3 seconds which is ok for stock price to update.
        Then depending on current price do following:
            if it exceeds max price renew it
            if it is less than drop price it means stock dropped and
                and we can move to 2 part of algorithm
        important thing is that we write down all the changes to restore file
        """
        properties_to_find = {
            'stock': stock,
            'quantity': quantity,
            'drop_percent': drop_percent,
            'up_percent': up_percent,
            'sell_percent': sell_percent,
        }
        # find in stocks-holding list index of stock data entry we work with
        for i in range(len(self.stocks_being_processed)):
            if properties_to_find <= self.stocks_being_processed[i]:
                break

        stock_data = self.stocks_being_processed[i]

        # price that stock needs to drop to
        drop_price = max_price * ((100 - drop_percent) / 100)

        while True:
            start_time = datetime.datetime.now()
            # get new price till it becomes valid
            current_price = await self.get_valid_price(stock)

            if current_price > max_price:
                max_price = current_price
                drop_price = max_price * ((100 - drop_percent) / 100)
                stock_data['max_price'] = max_price
                await self.update_restore_file("taras_trader/restore.yaml")

            if current_price <= drop_price:
                del stock_data["max_price"]
                del stock_data["drop_percent"]
                stock_data['drop_price'] = drop_price
                await self.update_restore_file("taras_trader/restore.yaml")

                asyncio.create_task(
                    self.buy_with_risk_avoidance(
                        stock,
                        quantity,
                        up_percent,
                        sell_percent,
                        drop_price,
                    )
                )
                break
            
            await asyncio.sleep(
                helpers.sleep_some_time(
                    helpers.find_timedelta(start_time, datetime.datetime.now()), 3
                )
            )



    async def wait_fill_or_cancel(
        self, trade, order, start_time
    ):
        """wait for order to fill within 5 minutes otherwise cancel it"""
        start_time = datetime.datetime.now()
        while trade.log[-1].status != "Filled":
            time_difference = helpers.find_timedelta(start_time, datetime.datetime.now())
            if time_difference >= 300:
                self.ib.cancelOrder(order)
                return False
            await asyncio.sleep(1.5)
        return True



    async def buy_with_risk_avoidance(
        self, 
        stock, 
        quantity,  
        up_percent, 
        sell_percent, 
        drop_price,
        **kwargs
    ):
        """
        2 part of main stock-handling algorithm
        Here we continuously get current stock price every (3 seconds - time needed to make one loop iteration),
        so one iteration takes exactly 3 seconds which is ok for stock price to update.
        Then depending on current price do following:
        if it exceeds rise price it means stock rose, 
        so we need to place the order to exchange, check if it is accepted for 5 minutes:
            1) in case of failure cancel it and inform user about that
            2) else update info about stock and go to final part of main algorithm
        important thing is that we write down all the changes to config file
        """
        # price reaching which stock will be purchased
        buy_price = drop_price * (1 + (up_percent / 100))

        properties_to_find = {
            'stock': stock,
            'quantity': quantity,
            'up_percent': up_percent,
            'sell_percent': sell_percent,
            'drop_price': drop_price,
        }
        for i in range(len(self.stocks_being_processed)):
            if properties_to_find <= self.stocks_being_processed[i]:
                break

        stock_data = self.stocks_being_processed[i]

        while True:
            start_time = datetime.datetime.now()
            current_price = await self.get_valid_price(stock)

            if current_price >= buy_price:
                # buy stock as a limit with price of 102 percent of current price to fill the order immediately
                # (actually we buy it with 100 percent of current price, 102 percent is just a detour to immediate buy
                # cause ibkr doesn't buy 100 percent price orders promptly (market orders))
                order, trade = await helpers.place_order(
                    stock, "buy", quantity, lmt=current_price * 1.02,
                )
                is_order_executed = await self.wait_fill_or_cancel(
                    stock, quantity, trade, order,
                )
                if not is_order_executed:
                    del self.stocks_being_processed[i]
                    if helpers.find_stock_occurencies(stock_data['stock'], self.stocks_being_processed) > 1:
                        self.stop_following_stock(stock_data['stock'])
                    return

                self.update_restore_file("taras_trader/restore.yaml")

                asyncio.create_task(
                    self.provide_risk_avoidance(
                        stock, quantity, sell_percent, current_price,
                    )
                )
                break
            
            await asyncio.sleep(
                helpers.sleep_some_time(
                    helpers.find_timedelta(start_time, datetime.datetime.now()), 3
                )
            )
            start_time = datetime.datetime.now()



    async def provide_risk_avoidance(
        self, 
        stock, 
        quantity, 
        sell_percent, 
        buy_price=0,
        **kwargs
    ):
        """
        final part of main stock-handling algorithm
        Here we continuously get current stock price every (3 seconds - time needed to make one loop iteration),
        so one iteration takes exactly 3 seconds which is ok for stock price to update.
        Then depending on current price do following:
            if it exceeds last max price renew it
            if it dropped 'sell_percent' we need to immediately sell it
        important thing is that we write down all the changes to config file
        """
        max_price = buy_price
        properties_to_find = {
            'stock': stock,
            'quantity': quantity,
            'sell_percent': sell_percent,
            'buy_price': buy_price,
        }
        for i in range(len(self.stocks_being_processed)):
            if properties_to_find <= self.stocks_being_processed[i]:
                break

        stock_data = list(self.stocks_being_processed[i].values())[0]
        
        # price reaching which stock must be sold as fast as possible
        alert_price = max_price * ((100 - sell_percent) / 100)

        while True:
            start_time = datetime.datetime.now()
            current_price = self.get_valid_price(stock)

            if current_price > max_price:
                # update info about stock and write it down to config file
                max_price = current_price
                stock_data['max_price'] = max_price
                self.update_restore_file("taras_trader/out.yaml")
                alert_price = max_price * ((100 - sell_percent) / 100)

            if current_price <= alert_price:
                # sell stock as a limit with price of 98 percent of current price to fill the order immediately
                # (actually we sell it with 100 percent of current price, 98 percent is just a detour to immediate sell
                # cause ibkr doesn't sell 100 percent price orders promptly (market orders))
                del self.stocks_being_processed[i]
                self.update_restore_file("taras_trader/out.yaml")
                order, trade = await helpers.place_order(
                    stock, "sell", quantity, "LMT", current_price * 0.98
                )
                if helpers.find_stock_occurencies(stock_data['stock'], self.stocks_being_processed) > 1:
                    self.stop_following_stock(stock_data['stock'])

                break
            
            await asyncio.sleep(
                helpers.sleep_some_time(
                    helpers.find_timedelta(start_time, datetime.datetime.now()), 3
                )
            )
