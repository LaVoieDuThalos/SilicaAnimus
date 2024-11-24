import itertools as itt
import logging
from os import getenv
import asyncio

import discord
from discord.ext import commands

from SilicaAnimus.helloasso_client import HelloAssoClient
from SilicaAnimus.google_sheets_client import GoogleSheetsClient, MemberInfo


def get_object_mentionned(mention, ctx):
    if mention.startswith("<") and mention.endswith(">"):
        if mention.startswith("<@!"):
            mention = int(mention[3:-1])
            obj = ctx.guild.get_member(mention)
        elif mention.startswith("<@&"):
            mention = int(mention[3:-1])
            obj = ctx.guild.get_role(mention)
        elif mention.startswith("<@"):
            mention = int(mention[2:-1])
            obj = ctx.guild.get_member(mention)

        return obj
    else:
        raise ValueError("This is not a mention !")


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
    async def give_role(self, ctx, *args, **kwargs):
        """This command give one or several roles to a user or to a group
        of users

        Syntax : !give_role [role1] [role2] ... to [user1] [user2] ... [roleA] [roleB]
        ..."""
        self.logger.info(f"user {ctx.author} invoked give_role command")

        # parsing args
        roles_stack = []
        user_stack = []
        try:
            split_rank = args.index("to")
        except ValueError:
            await ctx.channel.send("Bad command usage. Type !help give_role")
            raise

        roles_stack = args[:split_rank]
        user_stack = args[split_rank + 1:]

        # Running command
        for role, g_user in itt.product(roles_stack, user_stack):
            self.logger.info(f"{role} à {g_user}")
            men_role = get_object_mentionned(role, ctx)
            men_guser = get_object_mentionned(g_user, ctx)
            if not isinstance(men_role, discord.Role):
                await ctx.channel.send("Bad command usage")
                raise ValueError
            if isinstance(men_guser, discord.Role):
                for member in men_guser.members:
                    await member.add_roles(men_role)
            elif isinstance(men_guser, discord.Member):
                await men_guser.add_roles(men_role)
            else:
                await ctx.channel.send("Bad command usage")
                raise ValueError

        await ctx.channel.send("Giving role...")

    @commands.command()
    @commands.check_any(commands.has_permissions(manage_messages=True), custom_pinners)
    async def pin(self, ctx, *args, **kwargs):
        """
        Pins the given message, replied or last message in this channel

        Usage : Reply to the message you want to pin with !pin
        OR link messages you want to pin : !pin [link1] [link2] ...
        OR pins the last message : !pin"""
        self.logger.info("Running pin command")
        if len(args) > 0:
            for arg in args:
                link = arg.split("/")
                server_id = int(link[4])
                channel_id = int(link[5])
                message_id = int(link[6])
                if ctx.guild.id == server_id and ctx.channel.id == channel_id:
                    to_pin = await ctx.channel.fetch_message(message_id)
                    await to_pin.pin()
                    self.logger.info(f"{to_pin} pinned")
                else:
                    await ctx.channel.send(
                        "Please try to pin in the channel the message" + " comes from"
                    )
                    self.logger.info("bad pin resquest (wrong channel)")
        elif ctx.message.reference is not None:
            to_pin = await ctx.channel.fetch_message(ctx.message.reference.message_id)
            await to_pin.pin()

        else:
            # If nothing is given, pin the last message of the history
            # (before the command call)
            to_pin = [m async for m in ctx.history()][1]
            await to_pin.pin()

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
