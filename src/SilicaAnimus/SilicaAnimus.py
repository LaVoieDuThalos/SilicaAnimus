import logging
import asyncio

from DiscordClient import DiscordClient
from HelloAssoClient import HelloAssoClient

class SilicaAnimus:
    def __init__(self, discord_token : str):
        """_summary_

        Args:
            discord_token (str): Discord token for OAuth2
        """
        self.logger = logging.getLogger(__name__)
        self.discord_client = DiscordClient(discord_token)
        self.helloasso_client = HelloAssoClient("")

    async def run(self) -> bool:
        """Run the discord client
        """
        self.logger.info("Running...")

        async with asyncio.TaskGroup() as tg:
            discord_task = tg.create_task(self.discord_client.start())
            helloasso_task = tg.create_task(self.helloasso_client.start())

        return True
