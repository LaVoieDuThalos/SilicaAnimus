from os import getenv
from dotenv import load_dotenv
import pytest

from SilicaAnimus.discord_client import DiscordClient

pytest_plugins = ('pytest_asyncio',)
@pytest.mark.asyncio
async def test_discord_client_connection() -> bool:
    load_dotenv()
    client = DiscordClient(getenv("DISCORD_TOKEN"))
    await client.start()
    await client.close()

    return True
