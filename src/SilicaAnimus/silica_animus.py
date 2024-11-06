import logging
import asyncio
from os import getenv

from discord_client import DiscordClient
from helloasso_client import HelloAssoClient

class SilicaAnimus:
    def __init__(self):
        """_summary_

        Args:
            discord_token (str): Discord token for OAuth2
        """
        self.logger = logging.getLogger(__name__)
        self.discord_client = DiscordClient(getenv("DISCORD_TOKEN"))
        self.helloasso_client = HelloAssoClient(getenv("HELLOASSO_CLIENT_ID"), getenv("HELLOASSO_CLIENT_SECRET"))

    async def run(self) -> bool:
        """Run the discord client
        """
        self.logger.info("Running...")

        async with asyncio.TaskGroup() as tg:
            discord_task = tg.create_task(self.discord_client.start())
            helloasso_task = tg.create_task(self.helloasso_client.start())

        return True
