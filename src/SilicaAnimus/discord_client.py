from __future__ import annotations

import discord
from discord.ext import commands
import logging
from os import getenv
import asyncio

from SilicaAnimus.helloasso_client import HelloAssoClient
from SilicaAnimus.google_sheets_client import GoogleSheetsClient, MemberInfo


@commands.check
def custom_pinners(ctx):
    return False


class AdminCog(commands.Cog):
    """Commands used to administrate the Discord"""

    def __init__(self, parent_client):
        super().__init__()

        self.parent_client = parent_client
        self.logger = logging.getLogger(type(self).__name__)

    @commands.command()
    @commands.has_role(int(getenv("ADMIN_ROLE_ID")))
    async def give_role(self, ctx, *arg, **kwargs):
        """This command give role to a user or to a group of users"""
        self.logger.info("Running give_role command")
        await ctx.channel.send("Giving role...")

    @commands.command()
    @commands.check_any(commands.has_permissions(manage_messages=True), custom_pinners)
    async def pin(self, ctx, *args, **kwargs):
        """This command pin the last message in the channel or the answered
        message
        """
        self.logger.info("Running pin command")
        await ctx.channel.send("I'm pinning the message")

    @commands.command()
    @commands.has_role(int(getenv("ADMIN_ROLE_ID")))
    async def check_member(self, ctx, *arg, **kwargs):
        """This command checks if the person is a member on HelloAsso"""
        self.logger.info("Running check_member command")
        tokens = ctx.message.content.split(" ")
        if len(tokens) != 3:
            self.logger.warning("Wrong check member command")
            await ctx.channel.send(
                "Invoke the command with !check_member *first_name* *last_name*"
            )
            return

        first_name, last_name = tokens[1], tokens[2]
        is_member = await self.parent_client.helloasso_client.get_membership(
            first_name=first_name, last_name=last_name
        )
        if is_member:
            await ctx.channel.send(f"{first_name} {last_name} is a member")
        else:
            await ctx.channel.send(f"{first_name} {last_name} is not a member")


class DiscordClient:
    """The Discord client class"""

    def __init__(
        self,
        token: str,
        helloasso_client: HelloAssoClient,
        gsheet_client: GoogleSheetsClient,
    ):
        """_summary_"""
        self.intents = discord.Intents.default()
        self.intents.message_content = True
        self.intents.members = True
        self.intents.guilds = True
        self.intents.dm_messages = True

        self.helloasso_client = helloasso_client
        self.gsheet_client = gsheet_client

        self.client = commands.Bot(command_prefix="!", intents=self.intents)
        self.logger = logging.getLogger(__name__)

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
            await self.client.add_cog(AdminCog(self))
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

    async def process_dm(self, message: discord.Message) -> None:
        """Process the DMs received by the bot and takes associated actions

        Args:
            message (discord.Message): _description_
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
            content = message.content.split(" ")
            if len(content) < 3:
                await message.channel.send(
                    f'Bonjour {message.author.name}. Pour avoir le rôle membre, tapez "thalosien Prénom Nom ". Le bot va vérifier votre adhésion.'
                )
                return

            first_name, last_name = content[1], content[2]
            self.logger.info(f"{message.author.name} tried to get the role")
            await self.process_membership(
                member=member, first_name=first_name, last_name=last_name
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
        """Fills the class attributes with the necessary guild and membership role"""
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
        """Get the discord member with user_id

        Args:
            user_id (int): The user id

        Returns:
            discord.Member: the discord member
        """
        await self.populate_guild_data()
        member = self.thalos_guild.get_member(user_id)
        if member is None:
            self.logger.warning(f"User {user_id} could not be found")

        return member

    async def process_membership(
        self, member: discord.Member, first_name: str, last_name: str
    ) -> None:
        async with asyncio.TaskGroup() as tg:
            ha_task = tg.create_task(
                self.helloasso_client.get_membership(
                    first_name=first_name,
                    last_name=last_name,
                )
            )

            real_name_gsheet_task = tg.create_task(
                self.gsheet_client.get_member_by_name(
                    first_name=first_name, last_name=last_name
                )
            )

            discord_name_gsheet_task = tg.create_task(
                self.gsheet_client.get_member_by_discord_name(discord_name=member.name)
            )

        is_member = ha_task.result()
        real_name_member_info: MemberInfo = real_name_gsheet_task.result()
        discord_name_member_info: MemberInfo = discord_name_gsheet_task.result()

        if not is_member:
            self.logger.info(
                f"{first_name} {last_name} got denied the role, not a HelloAsso member"
            )
            await member.send(
                "Tu n'es apparemment pas membre. Vérifie que tu as envoyé les mêmes noms et prénoms que lors de ton inscription sur HelloAsso !"
            )
            return

        if discord_name_member_info.in_spreadsheet and (
            discord_name_member_info.first_name.lower() != first_name.lower()
            or discord_name_member_info.last_name.lower() != last_name.lower()
        ):
            self.logger.info(
                f"{member.name} got denied the role with {first_name} {last_name}, "
                "this discord name is already associated with {discord_name_member_info.first_name}, {discord_name_member_info.last_name}"
            )
            await member.send(
                "Ce compte est associé à un autre nom. Contactez un admin."
            )
            return

        if (
            real_name_member_info.in_spreadsheet
            and real_name_member_info.discord_nickname.lower() != member.name
        ):
            self.logger.info(
                f"{member.name} got denied the role with {first_name} {last_name}, "
                "this discord name is already associated with {discord_name_member_info.discord_nickname}"
            )
            await member.send(
                "Ce nom est associé à un autre pseudo discord. Contactez un admin."
            )
            return

        await self.set_membership(member, first_name, last_name)

    async def set_membership(
        self, member: discord.Member, first_name: str, last_name: str
    ) -> None:
        """Set the membership on discord and updates the spreadsheet

        Args:
            member (discord.Member): Discord guild member information
            first_name (str): First name of the member
            last_name (str): Last name of the member
        """
        await member.add_roles(self.thalos_role)
        await member.send("Tu es maintenant membre sur le serveur !")
        self.logger.info(f"{member.name} now has the thalos member role")

        member_info = MemberInfo(
            first_name=first_name,
            last_name=last_name,
            discord_nickname=member.name,
            server_nickname=member.display_name,
        )

        ret = await self.gsheet_client.add_member(member_info)
        if not ret:
            self.logger.error(f"Could not add {member_info} to spreadsheet")

        self.logger.info(f"{member_info} added to spreadsheet")
