import discord
import logging

MEMBER_ROLE_ID = 678922012109963294
THALOS_GUILD_ID = 677657875736166410

class DiscordClient:
    """The Discord client class
    """
    def __init__(self, token: str):
        """_summary_
        """
        self.intents = discord.Intents.default()
        self.intents.message_content = True
        self.intents.members = True
        self.intents.guilds = True

        self.client = discord.Client(intents=self.intents)
        self.logger = logging.getLogger(__name__)

        self.token = token
        self.thalos_guild = None
        self.thalos_role = None

        # Events 
        @self.client.event
        async def on_ready() -> None:
            self.logger.info(f"Logged as {self.client.user}")

        @self.client.event
        async def on_message(message) -> None:
            self.logger.debug(f"message {message.content} received from {message.author}")

            if message.author == self.client.user:
                return

            if message.channel.type == discord.ChannelType.private:
                await self.process_dm(message)

    async def process_dm(self, message) -> None:           
        if self.thalos_guild is None: 
            self.thalos_guild = self.client.get_guild(THALOS_GUILD_ID)
            self.thalos_role = self.thalos_guild.get_role(MEMBER_ROLE_ID)
        
        members = self.thalos_guild.members
        member = self.thalos_guild.get_member(message.author.id)
        if member is None:
            self.logger.info(f"{message.author.name} dm'd the bot but is not in the server")
            await message.channel.send(f"Ce bot n'a d'interêt que si vous êtes membre du serveur du thalos !")
            return

        if self.thalos_role in member.roles:
            self.logger.info(f"{message.author.name} dm'd the bot but already has the role")
            await message.channel.send(f"Bonjour {message.author.name}. Vous êtes déjà membre !")
            return
            
        if message.content.startswith('thalosien'):
            self.logger.info(f"{message.author.name} tried to get the role")
            await message.channel.send(f"Bientôt implémenté !")
            return

        self.logger.info(f"{message.author.name} dm'd the bot with a random message")
        await message.channel.send(f"Bonjour {message.author.name}. Pour avoir le rôle membre, tapez \"thalosien Prénom Nom \". Le bot va vérifier votre adhésion.")
        return

    async def start(self) -> bool:
        """Starts the bot

        Args:
            token (str): Discord API authentification token
        """

        self.logger.info("Running...")
        await self.client.start(self.token)

        return True

