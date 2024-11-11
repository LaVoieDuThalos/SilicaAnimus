import discord
from discord.ext import commands
import logging
from os import getenv
import asyncio
from event import Event

logger = logging.getLogger("silica_animus")


@commands.check
def custom_pinners(ctx):
    return False


class AdminCog(commands.Cog):
    """Commands used to administrate the Discord"""

    @commands.command()
    @commands.has_role(int(getenv("ADMIN_ROLE_ID")))
    async def give_role(self, ctx, *arg, **kwargs):
        """This command give role to a user or to a group of users"""
        logger.info("Running give_role command")
        await ctx.channel.send("Giving role...")

    @commands.command()
    @commands.check_any(commands.has_permissions(manage_messages=True), custom_pinners)
    async def pin(self, ctx, *args, **kwargs):
        """This command pin the last message in the channel or the answered
        message
        """
        logger.info("Running pin command")
        await ctx.channel.send("I'm pinning the message")


class DiscordClient:
    """The Discord client class"""

    def __init__(self, token: str):
        """_summary_"""
        self.intents = discord.Intents.default()
        self.intents.message_content = True
        self.intents.members = True
        self.intents.guilds = True
        self.intents.dm_messages = True

        self.client = commands.Bot(command_prefix="!", intents=self.intents)
        self.logger = logger

        self.token = token
        self.thalos_guild = None
        self.thalos_role = None

        self.start_future = None
        self.run = True

        # Commands
        @self.client.command()
        async def ping(ctx):
            await ctx.channel.send("pong")

        @self.client.command()
        async def echo(ctx, *args):
            await ctx.channel.send(" ".join(args))

        @self.client.command()
        async def my_roles(ctx):
            await ctx.channel.send(str(ctx.author.roles))

        # Events
        @self.client.event
        async def on_ready() -> None:
            self.logger.info(f"Logged as {self.client.user}")
            await self.client.add_cog(AdminCog())
            self.logger.info("Admin commands added")

        @self.client.event
        async def on_message(message) -> None:
            await self.client.process_commands(message)
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
        await self.populate_guild_data()

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
                first_name=content[1],
                last_name=content[2],
                user_id=message.author.id,
                message_back=True,
                add_role=True,
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

    async def populate_guild_data(self) -> None:
        if self.thalos_guild is None:
            self.thalos_guild = self.client.get_guild(int(getenv("THALOS_GUILD_ID")))
            if self.thalos_guild is not None:
                self.thalos_role = self.thalos_guild.get_role(
                    int(getenv("MEMBER_ROLE_ID"))
                )
            else:
                self.logger.warning("Could not get the member role")
                return

    async def get_member(self, user_id: int) -> discord.Member:
        await self.populate_guild_data()
        member = self.thalos_guild.get_member(user_id)
        if member is None:
            self.logger.warning(f"User {user_id} could not be found")

        return member

    async def set_membership(
        self, first_name: str, last_name: str, user_id: int, *args, **kwargs
    ) -> None:
        await self.populate_guild_data()
        member = await self.get_member(user_id=user_id)
        if member is None:
            member = self.client.get_user(user_id)
            if kwargs["message_back"]:
                member.send("Quelquechose a cassé... Contact les admins du serveur")
            self.logger.error(
                f"{first_name} {last_name} got checked for membership but is not in the server anymore ?!"
            )
            return

        if kwargs["add_role"]:
            await member.add_roles(self.thalos_role)
        if kwargs["message_back"]:
            await member.send("Tu es maintenant membre sur le serveur !")
        self.logger.info(f"{first_name} {last_name} now has the thalos member role")

    async def deny_membership(
        self, first_name: str, last_name: str, user_id: int, *args, **kwargs
    ) -> None:
        await self.populate_guild_data()

        member = await self.get_member(user_id)
        if member is None:
            member = self.client.get_user(user_id)
            if kwargs["message_back"]:
                member.send("Quelquechose a cassé... Contact les admins du serveur")
            self.logger.error(
                f"{first_name} {last_name} got checked for membership but is not in the server anymore ?!"
            )
            return

        if kwargs["messageBack"]:
            await member.send(
                "Tu n'es apparemment pas membre. Vérifie que tu as envoyé les mêmes noms et prénoms que lors de ton inscription sur HelloAsso !"
            )
