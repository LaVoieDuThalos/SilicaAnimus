import discord
import logging

class DiscordClient:
    def __init__(self):
        self.intents = discord.Intents.default()
        self.intents.message_content = True

        self.client = discord.Client(intents=intents)

        self.logger = logging.getLogger(__name__)

    @self.client.event
    async def on_ready():
        self.logger.log