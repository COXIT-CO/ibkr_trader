# import sys
# sys.path.append("site-packages")
# from loguru import logger

# logger.remove()

# # everyday create new file with name 'taras_trader.log',
# # if previous one exists it will be renamed by appending the date to its basename
# logger.add("taras_trader.log", rotation="15:00")

# from dotenv import dotenv_values
# import os

# CONFIG_DEFAULT = dict(
#     ICLI_IBKR_HOST="127.0.0.1", ICLI_IBKR_PORT=4002, ICLI_REFRESH=3.33
# )

# CONFIG = {**CONFIG_DEFAULT, **dotenv_values(".env.icli"), **os.environ}

# try:
#     ACCOUNT_ID = CONFIG["ICLI_IBKR_ACCOUNT_ID"]
# except:
#     logger.error(
#         "Sorry, please provide your IBKR Account ID [U...] in ICLI_IBKR_ACCOUNT_ID"
#     )
#     sys.exit(0)

# HOST = CONFIG["ICLI_IBKR_HOST"]
# PORT = int(CONFIG["ICLI_IBKR_PORT"])  # type: ignore

# import cli

# app = cli.IBKRCmdlineApp(
#         accountId=ACCOUNT_ID, host=HOST, port=PORT
#     )  