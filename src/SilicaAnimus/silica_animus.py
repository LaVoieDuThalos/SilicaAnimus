import logging
import asyncio
from os import getenv

from discord_client import DiscordClient
from helloasso_client import HelloAssoClient
from google_sheets_client import GoogleSheetsClient


class SilicaAnimus:
    def __init__(self):
        """_summary_

        Args:
            discord_token (str): Discord token for OAuth2
        """
        self.logger = logging.getLogger(__name__)
        self.helloasso_client = HelloAssoClient(
            getenv("HELLOASSO_CLIENT_ID"), getenv("HELLOASSO_CLIENT_SECRET")
        )

        self.gsheet_client = GoogleSheetsClient(
            getenv("GOOGLE_SERVICE_ACCOUNT_SECRETS_PATH")
        )
        self.discord_client = DiscordClient(
            getenv("DISCORD_TOKEN"),
            helloasso_client=self.helloasso_client,
            gsheet_client=self.gsheet_client,
        )

    async def run(self) -> bool:
        """Run the discord client"""
        self.logger.info("Running...")

        async with asyncio.TaskGroup() as tg:
            tg.create_task(self.discord_client.start())
            tg.create_task(self.helloasso_client.start())

        return True
