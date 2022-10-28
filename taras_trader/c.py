import sys
sys.path.append("site-packages")
# import time
# from helpers import *
# from ib_insync import *
# import asyncio


# async def run():
#     ib = IB()
#     await ib.connectAsync(
#         '127.0.0.1',
#         4002,
#         clientId=0,
#         readonly=False,
#         account="DU1820017",
#     )
#     ib.reqMarketDataType(2)
#     contract = Stock('AAPL', 'SMART', 'USD')
#     # ib.qualifyContracts(nflx_contract)
#     tickFields = tickFieldsForContract(contract)
#     data = None
#     for _ in range(5):
#         data = ib.reqMktData(contract, tickFields)
#         print(data)
#         time.sleep(1)

#     for _ in range(5):
#         print(data.midpoint())
#         time.sleep(1)

# # asyncio.run(run())
# # # ib.connect(host='127.0.0.1', port=4002, clientId=2147483647)
# # ib.reqNewsBulletins(True)


# # print(data)
# # for i in range(100):
# #     print(data.bid, data.ask)
# #     time.sleep(0.075)


# async def a():
#     print(1)
#     await asyncio.sleep(3)

# while True:
#     a()

import os
print(os.getcwd())
import sys
sys.path.append("..")
print(sys.path)
from app import app
# from place_order import place_order
import asyncio
import helpers
import orders
from ib_insync import IB, Stock
ib = IB()


async def place_order(
    symbol,
    action: bool,
    quantity,
    order_type,
    price=0,
):
    """action: True if BUY, False if SELL"""
    contract = Stock(symbol, "SMART", "USD")
    # return await app.placeOrderForContract(
    #     "msft", True, 
    # )

    # order = orders.IOrder(
    #         action, 
    #         quantity, 
    #         # price, 
    #         tif="GTC", 
    #         lmt=lmt,
    #         # trailstop=trailstop, 
    #         # trailpct=trailpct,
    #         # lmtPriceOffset=lmtPriceOffset, 
    #         # aux=aux,
    #     ).order(order_type)

    # trade = ib.placeOrder(contract, order)
    trade = await app.placeOrderForContract(
        symbol, 
        action, 
        contract, 
        quantity,
        price,
        order_type,
    )
    return trade

import time

async def run():
    await app.ib.connectAsync(
        "127.0.0.1",
        4002,
        clientId=2,
        readonly=False,
        account="DU1820017",
    )
    order, trade = await place_order("AMZN", True, 1, "LMT", price=115)
    # while 
    # # trade_1 = await place_order("AMZN", True, 1, "LMT", lmt=110)
    # # print(app.ib.positions()[0].position)
    # print("yes")
    print("abc")
    print(Stock("AMZN", "SMART", "USD").conId)
    print("def")
    # for _ in range(15):
    #     print(trade)
    #     print("\n")
    #     await asyncio.sleep(2)
    # print(trade[0].contract.conId)
    # for i in range(5):
    #     print(trade)
    #     print(trade[1].log[-1].status)
    #     print(trade_1)
    #     print(trade_1[1].log[-1].status)
    #     print("\n")
    #     await asyncio.sleep(1)

    # app.ib.cancelOrder(trade_1[0])
    # while True:
    #     print(trade[1].log[-1].status)
    #     print(trade_1[1].log[-1].status)
    #     print("\n")
    #     await asyncio.sleep(1)
    # while True:
    #     print(trade)
    #     print(trade[0])
    #     # print(trade.order)
    #     print(trade[1].log[-1].status)
    #     # for item in trade:
    #     #     print(item)
    #     # print(trade, type(trade))
    #     await asyncio.sleep(2)
# import scrape

# a = helpers.extract_data_from_yaml_file("restore.yaml")
# print(a)
# a = scrape.process_scraped_stock_data(a)
# print(a)
# print(a[1]['TSLA'].items() >= {'quantity': 4}.items())
# print(a[1]['TSLA']['quantity'])
# # print(list(a[1].values())[0].items())
# print({'quantity': 4}.items())
# print(a[1]['TSLA'].items())
# print({'quantity': 4}.items() <= a[1]['TSLA'].items())



# test_dict1 = {'gfg' : 1, 'is' : 2, 'best' : 3, 'for' : 4, 'CS' : 5}
# test_dict2 = {'gfg' : 1, 'is' : 2, 'best' : 3}
  
# # printing original dictionaries
# print("The original dictionary 1 : " +  str(test_dict1))
# print("The original dictionary 2 : " +  str(test_dict2))
  
# # Using items() + <= operator
# # Check if one dictionary is subset of other
# res = test_dict2.items() <= test_dict1.items()
# print(res)
# print(a)
# for stock in a:
#     for _, values in stock.items():
#         for i in values:
#             for key, value in i.items():
#                 print(key, value, type(key), type(value))


asyncio.run(run())

            