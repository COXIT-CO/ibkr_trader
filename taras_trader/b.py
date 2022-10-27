# from loguru import logger

# logger.remove()
# logger.add("file.log", rotation="15:41", colorize=True)
# logger.info("fjivf")

# logger.level("FRAME", no=25)
# logger.level("ARGS", no=40, color="<white>")

# while True:
#     continue
import asyncio
from audioop import mul
import time
# import place_order

# a = 1
# b = 0

# async def print_1():
#     global a
#     global b
#     while True:
#         a = b + 1
#         print("print_1")
#         b += 1
#         await asyncio.sleep(1)


# async def print_2():
#     global a
#     global b
#     while True:
#         a = b + 1
#         print("print_2")
#         b += 1
#         await asyncio.sleep(1)

# async def async_sleep():
#     asyncio.create_task(print_1())
#     asyncio.create_task(print_2())
#     global a
#     for i in range(5):
#         print(a)
#         await asyncio.sleep(1)


# asyncio.run(async_sleep())


import threading
import multiprocessing
# import time

# def a(c):
#     while True:
#         print(c)
#         time.sleep(4)

loop = asyncio.get_event_loop()

async def a():
    await asyncio.sleep(1)

asyncio.run(a())

async def b():
    while True:
        print("yes")
        print(1)
        await asyncio.sleep(2)

# for i in range(4):
#     p = multiprocessing.Process(target=a, args=("abc",))
#     p2 = multiprocessing.Process(target=b, args=("def",))
#     p.start()
#     p2.start()

#     c = threading.Thread(target=a, name="Downloader")
#     c.start()
for i in range(1):
    print("no")
    print(asyncio.create_task(b()))
    print("out")
print("abc")
# c.start()
# d.start()
# e = input("How do you do: ")
# print(e)




# with open("config_buy.yaml", "r") as file:
#     for line in file:
#         print("- AAPL: 2" in line)
#         if "- AAPL: 2" in line:
#             line = line.replace("- AAPL: 2", "abc")
#         print(line)


# def unfilled_stock_write_to_file(path_to_file, pattern, message_to_write):
#     lines = []
#     with open(path_to_file, "r") as file:
#         for line in file:
#             lines.append(line)
#     with open(path_to_file, "w") as file:
#         for line in lines:
#             if pattern in line and not line.startswith("#"):
#                 line = line.replace("\n", "") + f"  <-- {message_to_write}\n"
#             file.write(line)


# unfilled_stock_write_to_file("config_buy.yaml", "AAPL", "not filled")


