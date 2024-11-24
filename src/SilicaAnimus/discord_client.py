import discord
from discord.ext import commands
import logging
import itertools as itt


from os import getenv
from dotenv import load_dotenv
from typing import Union


import asyncio

logger = logging.getLogger('silica_animus')

load_dotenv()

def get_object_mentionned(mention, ctx):
    if mention.startswith('<') and mention.endswith('>'):
        if mention.startswith('<@!'):
            mention = int(mention[3:-1])
            obj = ctx.guild.get_member(mention)
        elif mention.startswith('<@&'):
            mention = int(mention[3:-1])
            obj = ctx.guild.get_role(mention)
        elif mention.startswith('<@'):
            mention = int(mention[2:-1])
            obj = ctx.guild.get_member(mention)

        return obj
    else:
        raise ValueError('This is not a mention !')

@commands.check
def custom_pinners(ctx):
    return False

class AdminCog(commands.Cog):
    """ Commands used to administrate the Discord"""

    def __init__(self, parent_client):
        super().__init__()

        self.parent_client = parent_client
        self.logger = logging.getLogger(type(self).__name__)

    @commands.command()
    @commands.has_role(int(getenv('ADMIN_ROLE_ID')))
    async def give_role(self, ctx, *args, **kwargs):
        """ This command give one or several roles to a user or to a group
        of users

        Syntax : !give_role [role1] [role2] ... to [user1] [user2] ... [roleA] [roleB]
        ... """
        logger.info(f'user {ctx.author} invoked give_role command')

        # parsing args
        roles_stack = []
        user_stack = []
        try:
            split_rank = args.index('to')
        except ValueError as e:
            await ctx.channel.send('Bad command usage. Type !help give_role')
            raise
        
        roles_stack = args[:split_rank]
        user_stack = args[split_rank + 1:]

        # Running command
        for role, g_user in itt.product(roles_stack, user_stack):
            logger.info(f'{role} à {g_user}')
            men_role = get_object_mentionned(role, ctx)
            men_guser = get_object_mentionned(g_user, ctx)
            if not isinstance(men_role, discord.Role):
                await ctx.channel.send(f'Bad command usage')
                raise ValueError
            if isinstance(men_guser, discord.Role):
                for member in men_guser.members:
                    await member.add_roles(men_role)
            elif isinstance(men_guser, discord.Member):
                await men_guser.add_roles(men_role)
            else:
                await ctx.channel.send(f'Bad command usage')
                raise ValueError                
            
        await ctx.channel.send('Giving role...')

    @commands.command()
    @commands.check_any(commands.has_permissions(manage_messages=True),
                        custom_pinners)
    async def pin(self, ctx, *args, **kwargs):
        """
        Pins the given message, replied or last message in this channel

        Usage : Reply to the message you want to pin with !pin
        OR link messages you want to pin : !pin [link1] [link2] ...
        OR pins the last message : !pin"""
        logger.info('Running pin command')
        if len(args) > 0:
            for arg in args:
                link = arg.split('/')
                server_id = int(link[4])
                channel_id = int(link[5])
                message_id = int(link[6])
                if ctx.guild.id == server_id and ctx.channel.id == channel_id:
                    to_pin = await ctx.channel.fetch_message(message_id)
                    await to_pin.pin()
                    logger.info(f'{to_pin} pinned')
                else:
                    await ctx.channel.send(
                        'Please try to pin in the channel the message'
                        + ' comes from')
                    logger.info(f'bad pin resquest (wrong channel)')
        elif ctx.message.reference is not None:
            to_pin = await ctx.channel.fetch_message(
                ctx.message.reference.message_id)
            await to_pin.pin()
            
        else:
            # If nothing is given, pin the last message of the history
            # (before the command call)
            to_pin = [m async for m in ctx.history()][1]
            await to_pin.pin()


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

        self.client = commands.Bot(command_prefix = '!', intents=self.intents)
        self.logger = logger

        self.token = token
        self.thalos_guild = None
        self.thalos_role = None

        self.start_future = None

        self.run = True

        # Commands
        @self.client.command()
        async def ping(ctx):
            await ctx.channel.send('pong')

        @self.client.command()
        async def echo(ctx, *args):
            await ctx.channel.send(' '.join(args))

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

    async def process_dm(self, message) -> None:           
        if self.thalos_guild is None: 
            self.thalos_guild = self.client.get_guild(int(getenv("THALOS_GUILD_ID")))
            if not self.thalos_guild is None:
                self.thalos_role = self.thalos_guild.get_role(int(getenv("MEMBER_ROLE_ID")))
            else:
                self.logger.warning(f"Could not get the member role")
                return

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
        """Stops the bot
        """

        self.logger.info("Closing...")
        self.run = False
        self.logger.info("Closed...")

        return True

