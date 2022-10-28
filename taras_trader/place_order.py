import sys

from taras_trader import scrape
sys.path.append("site-packages")

# add lookup pattern to import anything from __init__.py module
sys.path.append("..")

# from taras_trader import logger

from dataclasses import (
    dataclass,
    field,
)

# from taras_trader.app import logger
import sys
import oyaml as yaml
import math
import time
import threading
import multiprocessing
from typing import List, Union

from collections import Counter, defaultdict
from dataclasses import dataclass, field
import datetime
import os

import fnmatch  # for glob string matching!
from typing import Literal, Union, Optional, Sequence, Any, Mapping

import numpy as np

import pendulum

import pandas as pd
from dataclasses import dataclass

from taras_trader import helpers

# from helpers import extract_data_from_yaml_file

import ib_insync
from ib_insync import (
    IB,
    Stock,
    Ticker,
)
import asyncio

import logging

import seaborn
import collections

import psycopg2
# try:
#     conn = psycopg2.connect(
#         host="localhost",
#         dbname="taras_trader",
#         user="postgres",
#         password="pcl340"
#     )
#     cur = conn.cursor()
# except psycopg2.DatabaseError as exc:
#     logger.error(exc)

# import icli.lang as lang
# from icli.helpers import *  # FUT_EXP is appearing from here
from mutil.numeric import fmtPrice, fmtPricePad
from mutil.timer import Timer
import tradeapis.buylang as buylang

# from app import app
# from taras_trader.cli import logger


# Configure logger where the ib_insync live service logs get written.
# Note: if you have weird problems you don't think are being exposed
# in the CLI, check this log file for what ib_insync is actually doing.
logging.basicConfig(
    level=logging.INFO,
    filename=f"icli-{pendulum.now('US/Eastern')}.log",
    format="%(asctime)s %(message)s",
)



def set_db_max_stock_price(symbol, max_price):
    try:
        postgres_query =  """
            UPDATE stocks
            SET max_price = %s
            WHERE symbol = %s
        """        
        cur.execute(postgres_query, (max_price, symbol))

        conn.commit()
    except (Exception, psycopg2.DatabaseError) as error:
        logger.error(error)


def set_db_min_stock_price(symbol, min_price):
    try:
        postgres_query =  """
            UPDATE stocks
            SET min_price = %s
            WHERE symbol = %s
        """
        cur.execute(postgres_query, (min_price, symbol))

        conn.commit()
    except (Exception, psycopg2.DatabaseError) as error:
        logger.error(error)

# set_db_max_stock_stock('TSLA', 1)

def set_db_second_max_stock_price(symbol, second_max_price):
    try:
        postgres_query =  """
            UPDATE stocks
            SET second_max_price = %s
            WHERE symbol = %s
        """
        cur.execute(postgres_query, (second_max_price, symbol))

        conn.commit()
    except (Exception, psycopg2.DatabaseError) as error:
        logger.error(error)


def set_value_for_column_in_db(symbol, column, value):
    try:
        postgres_query =  """
            UPDATE stocks
            SET %s = %s
            WHERE symbol = %s
        """
        cur.execute(postgres_query, (column, value, symbol))

        conn.commit()
    except (Exception, psycopg2.DatabaseError) as error:
        logger.error(error)



stock_being_processed = []

# asyncio.run(get_stocks_orders_data("out.yaml")) 


LIVE_ACCOUNT_STATUS = [
    "TotalCashValue",
]

STATUS_FIELDS = set(LIVE_ACCOUNT_STATUS)

class Account:
    accountStatus: dict[str, float] = field(
        default_factory=lambda: dict(
            zip(LIVE_ACCOUNT_STATUS, [0.00] * len(LIVE_ACCOUNT_STATUS))
        )
    )


    def updateSummary(self, v):
        """Each row is populated after connection then continually
        updated via subscription while the connection remains active."""
        # logger.info("Updating sumary... {}", v)
        self.summary[v.tag] = v.value

        # regular accounts are U...; sanbox accounts are DU... (apparently)
        # Some fields are for "All" accounts under this login, which don't help us here.
        # TODO: find a place to set this once instead of checking every update?
        if self.isSandbox is None and v.account != "All":
            self.isSandbox = v.account.startswith("D")

        if v.tag in STATUS_FIELDS:
            try:
                self.accountStatus[v.tag] = float(v.value)
            except:
                # don't care, just keep going
                pass



@dataclass
class Stocks:
    # pending_stocks: dict[str, Any] = field(default_factory=dict)
    extracted_data = []
    stocks_being_processed = []
    stocks_to_check_general_cost = []
    stop_trigger = False
    stop_write_flag = False
    ib: IB = field(default_factory=IB)
    loop = None
    summary: dict[str, float] = field(default_factory=dict)
    accountStatus: dict[str, float] = field(
        default_factory=lambda: dict(
            zip(LIVE_ACCOUNT_STATUS, [0.00] * len(LIVE_ACCOUNT_STATUS))
        )
    )
    raw_stocks_data: dict = field(default_factory=dict)
    stock_tickers: dict[str, Ticker] = field(default_factory=dict)
    subscribes_per_stock: dict[str, int] = field(default_factory=dict)
    current_stock_prices: dict[str, int] = field(default_factory=dict)
    stocks_quantity: dict[str, List[Union[int, str]]] = field(default_factory=dict)
    stock_info_to_write: dict = field(default_factory=dict)


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
    def set_raw_stocks_data(cls, data=None):
        if data is None:
            data = {}
        cls.raw_stocks_data = data

    @classmethod
    def set_stocks_to_check_general_cost(cls, data=None):
        if data is None:
            data = []
        cls.stocks_to_check_general_cost = data

    @classmethod
    def set_current_stock_prices(cls, data=None):
        if data is None:
            data = []
        cls.current_stock_prices = data

    @classmethod
    def set_stop_trigger(cls, value: bool = False):
        cls.stop_trigger = value


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

    # async def populate_pending_stocks(self, path_to_file):
    #     self.pending_stocks = helpers.extract_data_from_yaml_file(path_to_file)


    # @classmethod
    # def append_stock_to_be_processed(cls, stock_data):
    #     cls.stocks_being_processed.append(stock_data)


    def set_loop(self, loop):
        self.loop = loop


    @classmethod
    def remove_processed_stock(cls, stock_data):
        cls.stocks_being_processed.remove(stock_data)


    @classmethod
    def process_file_orders(cls, file_to_read):
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
            cls.stocks_to_check_general_cost = scrape.process_scraped_stock_data(cls.raw_stocks_data)
            # cls.stocks_being_processed = scrape.process_scraped_stock_data(cls.raw_stocks_data)
            # print(cls.raw_stocks_data)
            # print(cls.raw_stocks_data)
            scrape.replace_stocks_being_processed(cls.raw_stocks_data, file_to_read)
            # scrape.write_orders_to_file(cls.stocks_to_check_general_cost, file_to_write)
            # cls.write_orders_to_file(cls.stocks_being_processed, file_to_write)
            # scrape.write_orders_to_file(raw_stocks_data, path_to_file)
        # await asyncio.sleep(3)


    @classmethod
    def write_orders_to_file(cls, data_to_write, path_to_file):
        while True:
            cls.stop_trigger = True
            scrape.write_orders_to_file(data_to_write, path_to_file)
            cls.stop_trigger = False


    # @staticmethod
    # def write_orders_without_risk_avoidance(
    #     path_to_file, 
    #     symbol, 
    #     quantity, 
    #     alert_price,
    # ):
    #     stock_risk_avoidance_data = {
    #         "symbol": symbol,
    #         "quantity": quantity,
    #         "alert_price": alert_price,
    #     }
    #     yaml_representation = yaml.dump(stock_risk_avoidance_data)
    #     with open(path_to_file, "a") as file:
    #         file.write(yaml_representation)


    @staticmethod
    def delete_processed_stocks_from_file(file_path: str) -> dict:
        with open(file_path, "w") as file:
            pass

    def set_ib(self, ib):
        self.ib = ib


    def subscribe_market_data(self):
        self.ib.reqMarketDataType(2)


    def subscribe_stock_market_data(self, stock_symbol):
        contract = Stock(stock_symbol, "SMART", "USD")
        return self.ib.reqMktData(contract, helpers.tickFieldsForContract(contract))


    async def infinitely_get_stock_price(self, symbol):
        # self.current_stock_prices[symbol] = self.stock_tickers[symbol].midpoint()
        while True:
            if symbol not in self.stock_tickers:
                break
            self.current_stock_prices[symbol] = self.stock_tickers[symbol].midpoint()
            if math.isnan(self.current_stock_prices[symbol]) or self.current_stock_prices[symbol] <= 0:
                self.current_stock_prices[symbol] = None
            await asyncio.sleep(3)


    def is_total_stocks_cost_affordable(self):
        total_cost = 0
        while True:
            current_time = time.time()
            for stock_symbol, quantities in self.stocks_quantity:
                for quantity in quantities:
                    if quantity.startswith("$"):
                        total_cost += int(quantity[1:])
                    else:
                        current_price = self.current_stock_prices[stock_symbol]
                        while math.isnan(current_stock_price) or current_stock_price <= 0:
                            time.sleep(2.5)
                            current_stock_price = self.current_stock_prices[stock_symbol]
                        total_cost += current_price * int(quantity)
            if time.time() - current_time <= 10:
                break
            time.sleep(time.time() - current_time)
            current_time = time.time()
            total_cost = 0
        print("yes")
        
        return total_cost > self.accountStatus['TotalCashValue'], self.accountStatus['TotalCashValue'], total_cost

    
    # def process_stock_conditions(
    #     self,
    #     stock_conditions,
    # ):
    #     drop_percent = stock_conditions['trailing-drop-percent']
    #     drop_price = current_stock_price - current_stock_price * (drop_percent / 100)
    #     rise_percent = stock_conditions['trailing-up-percent']
    #     rise_price = drop_price * ((100 + rise_percent) / 100)
    #     risk_avoidance_percent = stock_conditions['percentage-risk-avoidance']
    #     trigger_sell_price = rise_price - rise_price * (risk_avoidance_percent / 100)
    #     return drop_price, \
    #             rise_price, \
    #             trigger_sell_price


        
    def define_start_function_suspended_stocks(self, conditions):
        """depending on the stock conditions define one of 3 function of main algorithm to start from"""
        if 'drop_percent' in conditions and 'rise_percent' in conditions and 'risk_avoidance_percent' in conditions:
            return self.process_stock
        elif 'drop_percent' not in conditions and 'rise_percent' in conditions:
            return self.buy_with_risk_avoidance
        else:
            return self.provide_risk_avoidance


    # def extract_suspended_stock_conditions(self, stock_symbol, conditions):
    #     """stocks can have different conditions depending on their stage from last program failure"""
    #     quantity = conditions['quantity']
    #     risk_avoidance_percent = conditions['risk_avoidance_percent']
    #     possible_condition_fields = (
    #         'stock_symbol', 'quantity', 'drop_percent', 'rise_percent',
    #         'risk_avoidance_percent', 'drop_price', 'max_price',
    #     )
    #     stock_conditions = {}
    #     for condition in possible_condition_fields:
    #         try:
    #             stock_conditions[condition] = conditions[condition]

    #     args = {
    #         'stock_symbol': stock_symbol, 
    #         'quantity': quantity, 
    #         'risk_avoidance_percent': risk_avoidance_percent,
    #     }
    #     if 'drop_percent' in conditions and 'rise_percent' in conditions and 'risk_avoidance_percent' in conditions:
    #         drop_percent = conditions['drop_percent']
    #         rise_percent = conditions['rise_percent']
    #         previous_max_price = conditions['max_price']
    #         args += {
    #             'drop_percent': drop_percent, 
    #             'rise_percent': rise_percent, 
    #             'previous_max_price': previous_max_price,
    #         }
    #     elif 'drop_percent' not in conditions and 'rise_percent' in conditions:
    #         rise_percent = conditions['rise_percent']
    #         drop_price = conditions['drop_price']
    #         args = {
    #             'drop_price': drop_price, 'rise_percent': rise_percent,
    #         }
    #     else:
    #         previous_max_price = conditions['max_price']
    #         args = {
    #             'previous_max_price': previous_max_price,
    #         }

    #     return args


    def set_proper_conditions_order(self, stock_symbol, stock_conditions):
        """set stock conditions on proper order cause stock-handling functions
        preserve order"""
        possible_ordered_conditions = (
            'quantity', 'drop_percent', 'rise_percent', 
            'risk_avoidance_percent', 'drop_price', 'max_price',
        )

        ordered_stock_conditions = (stock_symbol,)
        for condition in possible_ordered_conditions:
            if condition in stock_conditions:
                ordered_stock_conditions += (stock_conditions[condition],)

        return ordered_stock_conditions


    def process_suspended_stocks(self):
        for stock_symbol, conditions in self.stock_info_to_write.items():
            # set stock conditions in proper order cause stock-handling functions 
            # are sensitive to arguments order and we aren't allowed to pass arguments as named ones with dictionary
            # cause args parameter https://docs.python.org/3/library/threading.html#threading.Thread supports only
            # list or tuple, so we need to take of care of order by ourself
            ordered_stock_conditions = self.set_proper_conditions_order(stock_symbol, conditions)
            function_to_start_from = self.define_start_function_suspended_stocks(conditions)

            if stock_symbol not in self.subscribes_per_stock or not self.subscribes_per_stock[stock_symbol]:
                self.stock_tickers[stock_symbol] = self.subscribe_stock_market_data(stock_symbol)
                self.subscribes_per_stock[stock_symbol] = self.subscribes_per_stock.get(stock_symbol, 0) + 1
            self.loop.create_task(self.infinitely_get_stock_price(stock_symbol))

            # add stock to general stock info keeping list
            self.stocks_being_processed.append(
                {stock_symbol: conditions}
            )

            # handle stock in separate thread
            threading.Thread(
                target=function_to_start_from, 
                name="stock_handler", 
                args=ordered_stock_conditions
            ).start()


    def update_stocks_info_file(self, file_to_write):
        yaml_representation = yaml.dump(self.stocks_being_processed)
        with open(file_to_write, "w") as file:
            file.write(yaml_representation)


    def write_stocks_info_to_file(self, path_to_file):
        while self.stop_write_flag:
            time.sleep(2)
        self.set_stop_write_flag(True)
        yaml_representation = yaml.dump(self.stocks_being_processed)
        with open(path_to_file, "w") as file:
            file.write(yaml_representation)
        self.set_stop_write_flag(False)


    async def run(self):
        self.ib.accountSummaryEvent += self.updateSummary

        await asyncio.gather(
            self.ib.reqAccountSummaryAsync(),  # self.ib.reqPnLAsync()
        )

        self.stock_info_to_write = helpers.extract_data_from_yaml_file("restore.yaml")[0]

        self.process_suspended_stocks()
        await asyncio.sleep(30)

        self.process_file_orders("config_buy.yaml")

        # if self.stocks_to_check_general_cost:
        #     for i in range(len(self.stocks_to_check_general_cost)):
        #         symbol = list(self.stocks_to_check_general_cost[i].keys())[0]
                # if symbol not in self.subscribes_per_stock or not self.subscribes_per_stock[symbol]:
                #     self.stock_tickers[symbol] = self.subscribe_stock_market_data(symbol)
                #     self.subscribes_per_stock[symbol] = self.subscribes_per_stock.get(symbol, 0) + 1
                # self.loop.create_task(self.infinitely_get_stock_price(symbol))
        #         quantity = list(self.stocks_to_check_general_cost[i].values())[0]['quantity']
        #         self.stocks_quantity[symbol] = self.stocks_quantity.get(symbol, []).append(quantity)

        #     does_stocks_cost_exceed_balance, balance_cash, total_stocks_cost = self.is_total_stocks_cost_affordable()

        #     if does_stocks_cost_exceed_balance:
        #         scrape.replace_stocks_being_processed(
        #             self.raw_stocks_data,
        #             "config_buy.yaml",
        #             total_stocks_cost,
        #             balance_cash,
        #         )

        #         # discard all subscriptions from stocks no more used
        #         # and remove them from dictionaries holding their data
        #         for stock_symbol, subscriptions in self.subscribes_per_stock.copy().items():
        #             self.subscribes_per_stock[stock_symbol] -= 1
        #             if not subscriptions:
        #                 self.ib.cancelMktData(Stock(stock_symbol, "SMART", "USD"))
        #                 del self.subscribes_per_stock[stock_symbol]
        #                 del self.stock_tickers[stock_symbol]
        #                 del self.current_stock_prices[stock_symbol]
                
        #         self.set_stop_trigger(True)
        #         # make all collections holding data about stocks not able to execute clear
        #     else:
        #         scrape.replace_stocks_being_processed(
        #             self.raw_stocks_data,
        #             "config_buy.yaml",
        #             are_stocks_accepted=True,
        #         )
        #         self.stocks_being_processed += self.stocks_to_check_general_cost.copy()

        #     self.set_raw_stocks_data()
        #     self.set_stocks_quantity()
            # self.set_stocks_to_check_general_cost()

            # if not self.stop_trigger:
            #     if self.stocks_to_check_general_cost:
            #         for i in range(len(self.stocks_to_check_general_cost)):
            #             symbol = list(self.stocks_to_check_general_cost[i].keys())[0]
            #             stock_conditions = list(self.stocks_to_check_general_cost[i].values())[0]
            #             quantity = stock_conditions['quantity']
            #             drop_percent = stock_conditions['trailing-drop-percent']
            #             rise_percent = stock_conditions['trailing-up-percent']
            #             risk_avoidance_percent = stock_conditions['percentage-risk-avoidance']
            #             args = (
            #                 symbol,
            #                 quantity,
            #                 drop_percent,
            #                 rise_percent,
            #                 risk_avoidance_percent,
            #                 self.stocks_to_check_general_cost[i],
            #             )
            #             # asyncio.create_task(self.buy_stocks_with_risk_avoidance(*args))
            #             threading.Thread(
            #                 target=self.process_stock, 
            #                 name="stock_handler", 
            #                 args=args
            #             ).start()
            #             self.stocks_being_processed.append(self.stocks_to_check_general_cost[i].copy()) 
            #             self.stocks_to_check_general_cost[i] = None
            #         while None in self.stocks_to_check_general_cost:
            #             self.stocks_to_check_general_cost.remove(None)
            #             # asyncio.create_task(self.buy_stocks_with_risk_avoidance(
            #             #     stock_ticker,
            #             #     symbol,
            #             #     quantity,
            #             #     drop_percent,
            #             #     rise_percent,
            #             #     risk_avoidance_percent,
            #             #     self.stocks_being_processed[i],
            #             # ))
            #         # self.delete_processed_stocks_from_file("out.yaml")

        await asyncio.sleep(5)


    @staticmethod
    def inform_about_unfilled_stock(path_to_file, pattern, message_to_write):
        lines = []
        with open(path_to_file, "r") as file:
            for line in file:
                lines.append(line)
        with open(path_to_file, "w") as file:
            for line in lines:
                if pattern in line and not line.startswith("#"):
                    line = line.replace("\n", "") + f"  <-- {message_to_write}\n"
                file.write(line)


    def get_valid_current_price(self, symbol):
        # return self.current_stock_prices[symbol] is not None
        current_stock_price = self.current_stock_prices[symbol]
        
        while self.current_stock_prices[symbol] is None:
            time.sleep(2.5)
            current_stock_price = self.current_stock_prices[symbol]

        return current_stock_price



    @staticmethod
    def sleep_for_some_time(previous_time):
        """sleep 3 seconds minus time needed to make one loop iteration"""

        time_to_sleep = 3 - (time.time() - previous_time)
        time.sleep(time_to_sleep if time_to_sleep else 0)



    def process_stock(
        self,
        symbol, 
        quantity,
        drop_percent, 
        rise_percent, 
        risk_avoidance_percent,
        previous_max_price=0,
        # previous_drop_price=0,
    ):
        """
        1. get current stock price, compare it to max price in database
        if it exceeds than renew max price in database
        2. if stock price drops x percentages start checking if it grows up y percentages
        otherwise wait untill it drops
        3. if stock price raised y percentages, buy it
        4. after purchase sell it as a trailing limit with z percentages
        (if stock raises from current price we will sell it when (max price - z percentages) 
        price is reached otherwise we sell stock when it drops z percentages from price in moment we bought it)
        """
        current_time = time.time()
        # current_stock_price = self.get_valid_current_price(symbol)
        # max_stock_price = previous_max_stock_price

        # if stock is processed calculate drop price otherwise restore previous max price and drop price
        conditions_to_find = {
            'quantity': quantity,
            'drop_percent': drop_percent,
            'rise_percent': rise_percent,
            'risk_avoidance_percent': risk_avoidance_percent,
        }
        for i in range(len(self.stocks_being_processed)):
            if list(self.stocks_being_processed[i].keys())[0] == symbol:
                if conditions_to_find.items() <= list(self.stocks_being_processed[i].values())[0].items():
                    break

        dict_to_update_info = list(self.stocks_being_processed[i].values())[0]

        max_price = previous_max_price
        drop_price = max_price * ((100 - drop_percent) / 100)

        # main algorithm
        while True:
            self.sleep_for_some_time(current_time)

            # get new stock price till it becomes valid
            current_stock_price = 100 # self.get_valid_current_price(symbol)

            if current_stock_price > max_price:
                # if current price exceeds max price set new max and drop ones 
                # cause the shift in percentages between max price and drop prices is saved
                max_price = current_stock_price
                drop_price = max_price * ((100 - drop_percent) / 100)
                dict_to_update_info['max_price'] = max_price
                self.write_stocks_info_to_file("out.yaml")

            if current_stock_price <= drop_price:
                # if stock dropped calculate price it needs to rise and start tracking when this happen make to buy
                del dict_to_update_info["max_price"]
                del dict_to_update_info["drop_percent"]
                dict_to_update_info['drop_price'] = drop_price
                self.write_stocks_info_to_file("out.yaml")

                self.buy_with_risk_avoidance(
                    symbol,
                    quantity,
                    rise_percent,
                    risk_avoidance_percent,
                    drop_price,
                )
                break
            current_time = time.time()


    def check_for_order_to_fill(
        self, trade, order, current_time
    ):
        """check for order to fill within 15 minutes otherwise cancel it"""
        while trade.log[-1].status != "Filled":
            if time.time() - current_time >= 900:
                # if order hasn't been bought for more that 15 minutes cancel it
                self.ib.cancelOrder(order)
                return
            time.sleep(1)
        return True



    def buy_with_risk_avoidance(
        self, 
        symbol, 
        quantity,  
        rise_percent, 
        risk_avoidance_percent, 
        drop_price,
    ):
        # if stock is processed first time restore previous max price and drop price otherwise calculate drop price
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
        
        current_time = time.time()
        while True:
            self.sleep_for_some_time(current_time)

            current_stock_price = self.get_valid_current_price(symbol)

            # if price raised buy it and make an order sell it when it drops to provide risk-avoidance
            if current_stock_price >= rise_price:
                # buy stock as a limit with 102 percentages price to fill the order immediately
                order, trade = self.loop.run_until_complete(
                    place_order(
                        symbol, True, quantity, lmt=current_stock_price * 1.02,
                    )
                )
                if not self.check_for_order_to_fill(
                    symbol, quantity, trade, order, current_time,
                ):
                    self.inform_about_unfilled_stock(
                        "config_buy.yaml", 
                        f"{symbol}: {quantity}", 
                        "order was pending fill for 15 minutes, so isn't executed"
                    )
                    return

                del dict_to_update_info["drop_price"]
                del dict_to_update_info["rise_percent"]
                max_price = current_stock_price
                dict_to_update_info['max_price'] = max_price
                self.write_stocks_info_to_file("config_buy.yaml")

                self.provide_risk_avoidance(
                    symbol, quantity, risk_avoidance_percent, max_price,
                )
                break
            current_time = time.time()



    def provide_risk_avoidance(
        self, symbol, quantity, risk_avoidance_percent, max_price=0, 
    ):
        current_time = time.time()

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
        
        # if stock is processed first time restore previous max price and drop price otherwise calculate drop price
        alert_price = max_price * ((100 - risk_avoidance_percent) / 100)

        while True:
            self.sleep_for_some_time(current_time)

            current_price = self.get_valid_current_price(symbol)

            if current_price > max_price:
                max_price = current_price
                dict_to_update_info['max_price'] = max_price
                self.write_stocks_info_to_file("config_buy.yaml")
                alert_price = max_price * ((100 - risk_avoidance_percent) / 100)

            if current_price <= alert_price:
                order, trade = self.loop.run_until_complete(
                    place_order(
                        symbol, False, quantity, "LMT", current_price * 0.98
                        )
                    )
                del self.stocks_being_processed[i]
                self.write_stocks_info_to_file("config_buy.yaml")
                # self.write_orders_without_risk_avoidance(
                #     "risk_avoidance.yaml", symbol, quantity, current_price
                # )
                # while True:
                #     if trade.log[-1].status != "Filled":
                #         time.sleep(1)
                #     else:
                #         break
                # logger.info(f"stock {symbol} is bough")
                break
            current_time = time.time()


    async def buy_stocks_with_risk_avoidance(
        self,
        stock_ticker,
        symbol, 
        quantity,   
        drop_percent, 
        rise_percent, 
        risk_avoidance_percent,
        stock_data,
    ):
        """
        1. get current stock price, compare it to max price in database
        if it exceeds than renew max price in database
        2. if stock price drops x percentages start checking if it grows up y percentages
        otherwise wait untill it drops
        3. if stock price raised y percentages, buy it
        4. after purchase sell it as a trailing limit with z percentages
        (if stock raises from current price we will sell it when (max price - z percentages) 
        price is reached otherwise we sell stock when it drops z percentages from price in moment we bought it)
        """
        # time = stock_conditions['time']

        print("yes")
        current_stock_price = 0
        async def get_current_stock_price(symbol):
            global current_stock_price
            while True:
                current_stock_price = stock_ticker.midpoint()  # get stock price
                print(current_stock_price)
                await asyncio.sleep(3)
        print("no")

        # asyncio.create_task(get_current_stock_price(symbol))

        # populate_stocks_table("../out.yaml")

        # receive current stock price and set it as max_price in db if didn't yet
        current_stock_price = stock_data.midpoint()
        print(current_stock_price)
        current_time = time.time()
        while math.isnan(current_stock_price) or current_stock_price <= 0:
            await asyncio.sleep(2.5)
            current_stock_price = stock_data.midpoint()
            print(current_stock_price)
        print(current_stock_price)
        max_stock_price = get_db_max_stock_price(symbol)
        if current_stock_price > max_stock_price or -0.1 < max_stock_price < 0.1:
            set_value_for_column_in_db(symbol, "max_price", current_stock_price)
            max_stock_price = current_stock_price

        # main algorithm
        stop_trigger = False
        while True:
            if stop_trigger:
                break
            
            # get new stock price till it becomes valid
            await asyncio.sleep((time.time() - current_time) or 0)
            current_stock_price = stock_data.midpoint()
            while math.isnan(current_stock_price) or current_stock_price <= 0:
                await asyncio.sleep(2.5)
                current_stock_price = stock_data.midpoint()
            current_time = time.time()
            
            # renew max_price column value in db if current stock price exceeds it
            if current_stock_price > max_stock_price:
                set_value_for_column_in_db(symbol, "max_price", current_stock_price)
                max_stock_price = current_stock_price

            # new minimal price that stock drop needs to reach
            drop_stock_price = max_stock_price * ((100 - drop_percent) / 100)

            # if stock dropped in price we need to set it's drop price in db and
            # price stock must to raise
            if current_stock_price <= drop_stock_price:
                set_value_for_column_in_db(symbol, "drop_price", current_stock_price)
                price_to_raise = drop_stock_price * (1 + (rise_percent / 100))

                while True:
                    if stop_trigger:
                        break

                    await asyncio.sleep(time.time() - current_time)
                    current_stock_price = stock_data.midpoint() 
                    current_time = time.time()

                    # if price raised buy it and sell it to provide risk-avoidance
                    if current_stock_price >= price_to_raise:
                        # buy stock as a limit to fill the order immediately
                        _, trade = place_order(symbol, True, quantity, lmt=current_stock_price * 1.02)
                        while trade.log[-1].status != "Filled":
                            await asyncio.sleep(1)
                        max_stock_price = current_stock_price

                        while True:
                            await asyncio.sleep(time.time() - current_time)
                            current_stock_price = stock_data.midpoint() 
                            current_time = time.time()

                            if current_stock_price > max_stock_price:
                                max_stock_price = current_stock_price
                            else:
                                stop_order_price = max_stock_price * ((100 - risk_avoidance_percent) / 100)
                                if current_stock_price <= stop_order_price:
                                    place_order(symbol, False, quantity, "LMT", current_stock_price * 0.98)
                                    # logger.info(f"stock {symbol} is bough")
                                    self.remove_processed_stock(stock_data)
                                stop_trigger = True
                                break


    async def sell_stocks(
        symbol, 
        quantity,   
        drop_percent, 
        rise_percent, 
        risk_avoidance_percent,
        stock_data,
    ):
        """
        1. get current stock price, compare it to max price in database
        if it exceeds than renew max price in database
        2. if stock price drops x percentages start checking if it grows up y percentages
        otherwise wait untill it drops
        3. if stock price raised y percentages, buy it
        4. after purchase sell it as a trailing limit with z percentages
        (if stock raises from current price we will sell it when (max price - z percentages) 
        price is reached otherwise we sell stock when it drops z percentages from price in moment we bought it)
        """

        current_stock_price = 0
        async def get_current_stock_price(symbol):
            global current_stock_price
            while True:
                current_stock_price = stock_data.midpoint()  # get stock price
                await asyncio.sleep(2.5)

        asyncio.create_task(get_current_stock_price(symbol))

        populate_stocks_table("../out.yaml")

        # receive current stock price and set it as max_price in db if didn't yet
        # current_stock_price = stock_data.midpoint()
        current_time = time.time()
        while math.isnan(current_stock_price) or current_stock_price <= 0:
            await asyncio.sleep(2.5)
            # current_stock_price = stock_data.midpoint()
        max_stock_price = get_db_max_stock_price(symbol)
        if current_stock_price > max_stock_price or -0.1 < max_stock_price < 0.1:
            set_value_for_column_in_db(symbol, "max_price", current_stock_price)
            max_stock_price = current_stock_price
        drop_stock_price = max_stock_price * ((100 - drop_percent) / 100)

        # main algorithm
        stop_trigger = False
        while True:
            if stop_trigger:
                break
            
            # get new stock price till it becomes valid
            await asyncio.sleep((time.time() - current_time) or 0)
            # current_stock_price = stock_data.midpoint()
            while math.isnan(current_stock_price) or current_stock_price <= 0:
                await asyncio.sleep(2.5)
                # current_stock_price = stock_data.midpoint()
            current_time = time.time()
            
            # renew max_price column value in db if current stock price exceeds it
            if current_stock_price > max_stock_price:
                set_value_for_column_in_db(symbol, "max_price", current_stock_price)
                max_stock_price = current_stock_price

            # new minimal price that stock drop needs to reach
            drop_stock_price = max_stock_price * ((100 - drop_percent) / 100)

            # if stock dropped in price we need to set it's drop price in db and
            # price stock must to raise
            if current_stock_price <= drop_stock_price:
                set_value_for_column_in_db(symbol, "drop_price", current_stock_price)
                price_to_raise = drop_stock_price * (1 + (rise_percent / 100))

                while True:
                    if stop_trigger:
                        break

                    await asyncio.sleep(time.time() - current_time)
                    # current_stock_price = stock_data.midpoint() 
                    current_time = time.time()

                    # if price raised buy it and sell it to provide risk-avoidance
                    if current_stock_price >= price_to_raise:
                        # buy stock as a limit to fill the order immidiately
                        _, trade = place_order(symbol, True, quantity, lmt=current_stock_price * 1.02)
                        while trade.log[-1].status != "Filled":
                            await asyncio.sleep(1)
                        max_stock_price = current_stock_price

                        while True:
                            await asyncio.sleep(time.time() - current_time)
                            # current_stock_price = stock_data.midpoint() 
                            current_time = time.time()

                            if current_stock_price > max_stock_price:
                                max_stock_price = current_stock_price
                            else:
                                sell_order_price = max_stock_price * ((100 - risk_avoidance_percent) / 100)
                                if current_stock_price <= sell_order_price:
                                    place_order(symbol, "SELL", quantity, "LMT", current_stock_price * 1.02)
                                stop_trigger = True
                                break
        

def get_db_max_stock_price(symbol):
    """
    get max stock price from db and return it
    """
    try:
        postgres_query =  """
            SELECT max_price 
            FROM stocks 
            WHERE symbol = %s;
        """
        # "select max_price from stocks where symbol = 'TSLA'"
        
        # execute a statement
        cur.execute(postgres_query, ('TSLA',))

        # display the PostgreSQL database server version
        max_stock_price = cur.fetchone()[0]
        logger.info(max_stock_price)
       
        # close the communication with the PostgreSQL
        # cur.close()

        return max_stock_price
    except (Exception, psycopg2.DatabaseError) as error:
        logger.error(error)

    # return max_stock_price


async def place_order(
    symbol,
    action: bool,
    quantity,
    order_type,
    price=0,
    lmt=0,
    trailpct=0,
    trailstop=0,
    lmtPriceOffset=0,
    aux=0
):
    """action: True if BUY, False if SELL"""
    contract = Stock(symbol, "SMART", "USD")
    # return await app.placeOrderForContract(
    #     "msft", True, 
    # )
    trade = await app.placeOrderForContract(
        symbol, 
        action, 
        contract, 
        quantity,
        price,
        order_type,
        lmt=lmt,
        trailpct=0,
        trailstop=trailstop,
        lmtPriceOffset=lmtPriceOffset,
        aux=aux
    )
    return trade

    
def sell_stock(symbol, quantity, price, order_type):
    contract = Stock(symbol, "SMART", "USD")
    return app.placeOrderForContract(
        symbol, 
        False, 
        contract, 
        quantity,
        price,
        order_type,
    )

def populate_stocks_table(path_to_file):
    scraped_data = extract_data_from_yaml_file(path_to_file)
    try:
        # create a cursor
        # cur = conn.cursor()
        postgres_insert_query = """ 
            INSERT INTO stocks (symbol, max_price, min_price) 
            VALUES (%s,%s,%s)
        """
        for stock in scraped_data:
            symbol = list(stock.keys())[0]
            cur.execute(postgres_insert_query, (symbol, 0, 0))
        conn.commit()
        # cur.execute("""
        #     select * from stocks;
        # """)
        # result = cur.fetchall()
        # for row in result:
        #     logger.info(result)

    except (Exception, psycopg2.DatabaseError) as error:
        logger.error(error)


# from app import app

async def run():
    await app.ib.connectAsync(
        "127.0.0.1",
        4002,
        clientId=2,
        readonly=False,
        account="DU1820017",
    )
    _, trade = await place_order("AMZN", True, 1, "LMT", lmt=114)
    while True:
        print(trade.log[-1].status)
        # for item in trade:
        #     print(item)
        # print(trade, type(trade))
        await asyncio.sleep(2)


# asyncio.run(run())
# print(helpers.extract_data_from_yaml_file("config_buy.yaml"))

# populate_stocks_table("../out.yaml")
