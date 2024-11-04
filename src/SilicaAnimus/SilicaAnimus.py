import logging
from DiscordClient import DiscordClient

class SilicaAnimus:
    def __init__(self, discord_token : str):
        """_summary_

        Args:
            discord_token (str): Discord token for OAuth2
        """
        self.logger = logging.getLogger(__name__)
        self.discord_client = DiscordClient(discord_token)

    def run(self) -> bool:
        """Run the discord client
        """
        self.logger.info("Running...")
        self.discord_client.run()

        return True
