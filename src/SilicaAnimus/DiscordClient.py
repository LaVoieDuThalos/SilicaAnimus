import discord
import logging

class DiscordClient:
    """The Discord client class
    """
    def __init__(self, token: str):
        """_summary_
        """
        self.intents = discord.Intents.default()
        self.intents.message_content = True

        self.client = discord.Client(intents=self.intents)
        self.logger = logging.getLogger(__name__)

        self.token = token

        # Events 
        @self.client.event
        async def on_ready() -> None:
            self.logger.info(f"Logged as {self.client.user}")

        @self.client.event
        async def on_message(message) -> None:

            self.logger.debug(f"message {message.content} received from {message.author}")

            if message.author == self.client.user:
                return

            if message.content.startswith('$bonjour'):
                await message.channel.send('Bonjour!')

    async def start(self) -> bool:
        """Starts the bot

        Args:
            token (str): Discord API authentification token
        """

        self.logger.info("Running...")
        await self.client.start(self.token)

        return True

