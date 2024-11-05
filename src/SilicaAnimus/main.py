import logging
import sys
import typer
import asyncio
from functools import wraps

from SilicaAnimus import SilicaAnimus

def typer_async(f):
    @wraps(f)
    def wrapper(*args, **kwargs):
        return asyncio.run(f(*args, **kwargs))

    return wrapper

@typer_async
async def main(discord_token: str) -> None:
        logging.basicConfig(stream=sys.stdout, level=logging.INFO)

        silica_animus = SilicaAnimus(discord_token=discord_token)
        await silica_animus.run()

if __name__ == "__main__":
    typer.run(main)
