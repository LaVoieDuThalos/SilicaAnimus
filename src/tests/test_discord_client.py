import pytest
import asyncio
from os import getenv
from dotenv import load_dotenv

from SilicaAnimus.discord_client import DiscordClient

pytest_plugins = ("pytest_asyncio",)

load_dotenv()


@pytest.mark.asyncio
async def test_discord_client_connection():
    """Test that Discord client can connect and disconnect properly"""
    client = DiscordClient(
        getenv("DISCORD_TOKEN"), helloasso_client=None, gsheet_client=None
    )
    future = asyncio.create_task(client.start())
    await asyncio.sleep(5)
    await client.close()
    await future
