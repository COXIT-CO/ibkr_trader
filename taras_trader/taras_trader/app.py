from dotenv import dotenv_values
import os

from taras_trader import cli

from loguru import logger

def asink(x):
    # don't use print_formatted_text() (aliased to print()) because it doesn't
    # respect the patch_stdout() context manager we've wrapped this entire
    # runtime around. If we don't have patch_stdout() guarantees, the interface
    # rips apart with prompt and bottom_toolbar problems during async logging.
    print(x, end="")


logger.remove()
logger.add(asink, colorize=True)

CONFIG_DEFAULT = dict(
    ICLI_IBKR_HOST="127.0.0.1", ICLI_IBKR_PORT=4002, ICLI_REFRESH=3.33
)

CONFIG = {**CONFIG_DEFAULT, **dotenv_values(".env.icli"), **os.environ}

try:
    ACCOUNT_ID = CONFIG["ICLI_IBKR_ACCOUNT_ID"]
except:
    logger.error(
        "Sorry, please provide your IBKR Account ID [U...] in ICLI_IBKR_ACCOUNT_ID"
    )
    sys.exit(0)

HOST = CONFIG["ICLI_IBKR_HOST"]
PORT = int(CONFIG["ICLI_IBKR_PORT"])  # type: ignore
# REFRESH = float(CONFIG["ICLI_REFRESH"])  # type: ignore

app = cli.IBKRCmdlineApp(
    accountId=ACCOUNT_ID, host=HOST, port=PORT
)  

# async def a():
#     await app.setup()
#     await app.dorepl()
#     app.stop()

# asyncio.run(a())