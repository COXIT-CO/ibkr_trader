from prompt_toolkit.patch_stdout import patch_stdout
from loguru import logger
from mutil import safeLoop  # type: ignore
import asyncio
from . import app

logger.add("file.log", rotation="1 week")


async def initcli():
    with patch_stdout(raw=True):
        try:
            await app.app.dorepl()
        except SystemExit:
            # known good exit condition
            ...

    app.app.stop()


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
