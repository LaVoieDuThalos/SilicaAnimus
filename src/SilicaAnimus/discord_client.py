import discord
import logging
from os import getenv
import asyncio
from event import Event


class DiscordClient:
    """The Discord client class"""

    def __init__(self, token: str):
        """_summary_"""
        self.intents = discord.Intents.default()
        self.intents.message_content = True
        self.intents.members = True
        self.intents.guilds = True
        self.intents.dm_messages = True

        self.client = discord.Client(intents=self.intents)
        self.logger = logging.getLogger(__name__)

        self.token = token
        self.thalos_guild = None
        self.thalos_role = None

        self.start_future = None
        self.run = True

        # Events
        @self.client.event
        async def on_ready() -> None:
            self.logger.info(f"Logged as {self.client.user}")

        @self.client.event
        async def on_message(message) -> None:
            self.logger.debug(
                f"message {message.content} received from {message.author}"
            )

            if message.author == self.client.user:
                return

            if message.channel.type == discord.ChannelType.private:
                await self.process_dm(message)

        self.membership_request = Event()

    async def process_dm(self, message: discord.Message) -> None:
        """Process the DMs received by the bot and takes associated actions

        Args:
            message (discord.Messag): _description_
        """
        self.populate_roles()

        member = self.thalos_guild.get_member(message.author.id)
        if member is None:
            self.logger.info(
                f"{message.author.name} dm'd the bot but is not in the server"
            )
            await message.channel.send(
                "Ce bot n'a d'interêt que si vous êtes membre du serveur du thalos !"
            )
            return

        if self.thalos_role in member.roles:
            self.logger.info(
                f"{message.author.name} dm'd the bot but already has the role"
            )
            await message.channel.send(
                f"Bonjour {message.author.name}. Vous êtes déjà membre !"
            )
            return

        if message.content.startswith("thalosien"):
            self.logger.info(f"{message.author.name} tried to get the role")
            content = message.content.split(" ")
            await self.membership_request(
                first_name=content[1], last_name=content[2], user_id=message.author.id
            )
            return

        self.logger.info(f"{message.author.name} dm'd the bot with a random message")
        await message.channel.send(
            f'Bonjour {message.author.name}. Pour avoir le rôle membre, tapez "thalosien Prénom Nom ". Le bot va vérifier votre adhésion.'
        )
        return

    async def start(self) -> bool:
        """Starts the client

        Args:
            token (str): Discord API authentification token
        """
        self.logger.info("Starting...")
        self.start_future = asyncio.create_task(self.client.start(self.token))
        self.logger.info("Running...")

        while self.run:
            await asyncio.sleep(1)

        await self.client.close()
        await self.start_future
        self.logger.info("Closed")

        return True

    async def close(self) -> bool:
        """Stops the bot"""

        self.logger.info("Closing...")
        self.run = False
        self.logger.info("Closed...")

        return True

    def populate_roles(self) -> None:
        if self.thalos_guild is None:
            self.thalos_guild = self.client.get_guild(int(getenv("THALOS_GUILD_ID")))
            if self.thalos_guild is not None:
                self.thalos_role = self.thalos_guild.get_role(
                    int(getenv("MEMBER_ROLE_ID"))
                )
            else:
                self.logger.warning("Could not get the member role")
                return

                self.logger.warning("Could not get the member role")

    async def set_membership(
        self, first_name: str, last_name: str, user_id: int
    ) -> None:
        self.populate_roles()
        member = self.thalos_guild.get_member(user_id)
        if member is None:
            self.logger.warning(
                f"{first_name} {last_name} with id {user_id} could not be found"
            )
            return

        await member.add_roles(self.thalos_role)
        await member.send("Tu es maintenant membre sur le serveur !")
        self.logger.warning(f"{first_name} {last_name} now has the thalos member role")
