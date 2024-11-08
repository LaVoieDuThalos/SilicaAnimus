import logging
import sys
import typer
import asyncio
from functools import wraps

from dotenv import load_dotenv
from silica_animus import SilicaAnimus


def typer_async(f):
    @wraps(f)
    def wrapper(*args, **kwargs):
        return asyncio.run(f(*args, **kwargs))

    return wrapper


@typer_async
async def main() -> None:
    logging.basicConfig(stream=sys.stdout, level=logging.INFO)

    silica_animus = SilicaAnimus()
    await silica_animus.run()


if __name__ == "__main__":
    load_dotenv()
    typer.run(main)
