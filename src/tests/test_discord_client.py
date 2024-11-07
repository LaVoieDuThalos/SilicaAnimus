from os import getenv
from dotenv import load_dotenv
import pytest
import asyncio
import logging
import sys

from SilicaAnimus.discord_client import DiscordClient

pytest_plugins = ('pytest_asyncio',)

def setup_function(function):
    load_dotenv()
    logging.basicConfig(stream=sys.stdout, level=logging.DEBUG)

@pytest.mark.asyncio
async def test_discord_client_connection() -> bool:
    client = DiscordClient(getenv("DISCORD_TOKEN"))
    future = asyncio.create_task(client.start())
    await asyncio.sleep(5)
    await client.close()
    await future
    return True

if __name__ == "__main__":
    setup_function(test_discord_client_connection)
    asyncio.run(test_discord_client_connection())
