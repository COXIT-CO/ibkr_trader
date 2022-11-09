from prompt_toolkit.patch_stdout import patch_stdout
from loguru import logger
from mutil import safeLoop  # type: ignore
import asyncio
from taras_trader import cli
import sys

from dotenv import dotenv_values
import os

logger.add("file.log", rotation="1 week")

CONFIG_DEFAULT = dict(
    ICLI_IBKR_HOST="127.0.0.1", ICLI_IBKR_PORT=4002
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


async def initcli():
    app = cli.IBKRCmdlineApp(
        accountId=ACCOUNT_ID, host=HOST, port=PORT
    )
    # await app.setup()
    if sys.stdin.isatty():
        # patch entire application with prompt-toolkit-compatible stdout
        with patch_stdout(raw=True):
            try:
                await app.dorepl()
            except SystemExit:
                # known good exit condition
                ...
    else:
        # NOT IMPLEMENTED HERE, HOLDOVER FROM TCLI
        await app.consumeStdin()

    app.stop()


def runit():
    """Entry point for icli script and __main__ for entire package."""
    try:
        asyncio.run(initcli())
    except KeyboardInterrupt:
        # known good exit condition
        ...
    except:
        logger.exception("unknown reasons, very very bad ...")


if __name__ == "__main__":
    runit()
