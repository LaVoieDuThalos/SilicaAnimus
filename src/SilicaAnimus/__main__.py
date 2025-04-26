import logging
import sys
import typer
import asyncio
from functools import wraps

from dotenv import load_dotenv
from SilicaAnimus import SilicaAnimus


def typer_async(f):
    @wraps(f)
    def wrapper(*args, **kwargs):
        return asyncio.run(f(*args, **kwargs))

    return wrapper


@typer_async
async def async_main() -> None:
    logging.basicConfig(stream=sys.stdout, level=logging.INFO)

    silica_animus = SilicaAnimus(discord_only=False)
    await silica_animus.run()


def main():
    load_dotenv()
    typer.run(async_main)


if __name__ == "__main__":
    main()
