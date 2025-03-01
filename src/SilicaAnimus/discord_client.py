import itertools as itt
import functools
import logging
from os import getenv
import asyncio
from typing import Union, Text
from dotenv import load_dotenv
from time import sleep

import discord
from discord import app_commands
from discord.ext import commands

from helloasso_client import HelloAssoClient
from google_sheets_client import GoogleSheetsClient, MemberInfo

load_dotenv()


class MessageTemplate(discord.Embed):
    """
    Template for embed messages posted by the bot into discord
    channels
    """
    def __init__(self, *args, **kwargs):

        super().__init__(*args, **kwargs)
        self.colour = discord.Colour.dark_red()
        self.set_footer(
            icon_url = 'https://voie-du-thalos.org/img/logo.png',
            text = 'Application Discord pour La Voie du Thalos')

class MemberProcessView(discord.ui.View):
    """
    View to get the membership status on discord
    """

    def __init__(self, client, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.client = client

    @discord.ui.button(label = 'Demander le rôle de membre',
                       style = discord.ButtonStyle.primary)
    async def button_get(self, interaction: discord.Interaction,
                         button: discord.ui.Button):

        member_role = interaction.guild.get_role(678922012109963294)
        embed = MessageTemplate()
        ephemeral = True

        member_info = (
            await self.client.gsheet_client.get_member_by_discord_name(
            interaction.user.name)
        )

        # if the member has the role already
        if member_role in interaction.user.roles:
            await interaction.response.defer()            
            embed.description = (
                f"Vous possédez déjà le rôle {member_role.mention}.")
            await interaction.followup.send(embed = embed,
                                            ephemeral = ephemeral)

        # if the member is in the sheet
        elif member_info.in_spreadsheet:
            await interaction.response.defer()

            # get information about this member, update member_info
            if await self.client.helloasso_client.get_membership(
                    first_name = member_info.first_name,
                    last_name = member_info.last_name):
                member_info.member_current_year = True
                await self.client.gsheet_client.add_member(member_info)


            if member_info.member_current_year:
                await interaction.user.add_roles(member_role)    

                embed.description = (
                    f"Rôle {member_role.mention} ajouté avec succès")

                await interaction.followup.send(embed = embed,
                                                ephemeral = ephemeral)
                
            # if the user is not member of the association this year
            else:
                embed.description = (
                    f"Votre compte discord est associé au nom "
                    + f"{member_info.last_name}, prénom "
                    + f"{member_info.first_name} qui n'est actuellement pas "
                    + "adhérent de l'association. S'il s'agit d'une erreur, "
                    + "merci de contacter un administrateur")
                await interaction.followup.send(embed = embed,
                                                ephemeral = ephemeral)
        # if the member is not in the sheet
        else:
            #send form
            membership = MemberProcessModal()
            await interaction.response.send_modal(membership)
            await membership.wait()
            
            member_info.first_name = membership.first_name.value
            member_info.last_name = membership.last_name.value

            # if the user is member of association
            if await self.client.helloasso_client.get_membership(
                    first_name = member_info.first_name,
                    last_name = member_info.last_name):
                member_info.member_current_year = True
                identity_info = await self.client.gsheet_client.get_member_by_name(
                    first_name = member_info.first_name,
                    last_name = member_info.last_name)
                # if there is already a discord name recorded
                if len(identity_info.discord_nickname) > 0:
                    embed.description = (f"Ces nom / prénom sont déjà associés "
                    + "à un compte discord. Veuillez contacter un "
                    + "administrateur pour résoudre ce problème")
                # if there is no discord name recorded
                else:
                    member_info.member_last_year = identity_info.member_last_year
                    await self.client.gsheet_client.add_member(member_info)
                    await interaction.user.add_roles(member_role)
                    embed.description = (f"Rôle {member_role.mention} ajouté "
                    + "avec succès")
                
            # if the user is not member of association
            else:
                embed.description = (
                    "Vous n'êtes actuellement pas référencé comme membre de "
                    + "l'association. S'il s'agit d'une erreur veuillez "
                    + "contacter un administrateur")

            await membership.interaction.followup.send(
                embed = embed, ephemeral = ephemeral)

    @discord.ui.button(label = 'Signaler un problème',
                       style = discord.ButtonStyle.danger)
    async def button_report(self, interaction: discord.Interaction,
                            button: discord.ui.Button):
        await interaction.response.send_message('Contactez un administrateur',
                                                ephemeral = True)
        
class MemberProcessModal(discord.ui.Modal,
                         title = 'Devenir membre sur le discord'):
    """
    Modal getting first and last names of the user using a form
    """
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.member_role = 'Membres Thalos'
        
        self.first_name = discord.ui.TextInput(label = 'Prénom')
        self.last_name = discord.ui.TextInput(label = 'Nom') 
        self.add_item(self.first_name)
        self.add_item(self.last_name)



    async def on_submit(self, interaction: discord.Interaction):
        embed = MessageTemplate(description = """Données envoyées""")
        self.interaction = interaction
        await interaction.response.defer()
        
        



class CheckModal(discord.ui.Modal, title = 'Informations'):
    """
    Check if the given name / surname is member of the association
    """
    prenom = discord.ui.TextInput(label = 'Prénom',
                                  placeholder = 'Paul')
    nom = discord.ui.TextInput(label = 'Nom',
                               placeholder = 'Bismuth')



    async def on_submit(self, interaction: discord.Interaction):
        nom = self.nom
        prenom = self.prenom
        ha_client = interaction.client.parent_client.helloasso_client
        is_member = await ha_client.get_membership(
            first_name = prenom.value,
            last_name = nom.value
        )

        if is_member:
            return_message = f"{prenom.value} {nom.value} est adhérent"
        else:
            return_message = f"{prenom.value} {nom.value} n'est pas adhérent"
        embed = MessageTemplate(
            title = 'Vérification du membre :',
            description = return_message)
        await interaction.response.send_message(embed = embed, 
                                                ephemeral = True)        

# class MyView(discord.ui.View):
#     """
#     WIP
#     """
#     @discord.ui.button(label = 'Je cherche un adversaire',
#                        style = discord.ButtonStyle.primary)
#     async def button_search(self, interaction, button):
        
#         embed = interaction.message.embeds[0]

#         for i, field in enumerate(embed.fields):
#             if field.name == 'Joueurs en attente':
#                 my_field = field
#                 field_ID = i

#         new_user = interaction.user.mention
#         content = my_field.value
#         if new_user not in my_field.value:
#             content += f'\n{new_user}'

#         embed.set_field_at(field_ID, name = 'Joueurs en attente',
#                            value = content,
#                            inline = False)
#         await interaction.response.edit_message(embed = embed)
                
#     # @discord.ui.button(label = 'Rejoindre une partie',
#     #                    style = discord.ButtonStyle.success)
#     # async def button_join(self, interaction, button):
#     #     content = interaction.message.content
#     #     print(interaction.message.embeds[0])
#     #     edit = content + f'\n{interaction.user.mention} a rejoint une partie'
#     #     await interaction.message.edit(content = edit)

                
#     @discord.ui.button(label = 'Se retirer',
#                        style = discord.ButtonStyle.danger)
#     async def button_exit(self, interaction, button):
#         embed = interaction.message.embeds[0]
#         for i, field in enumerate(embed.fields):
#             if field.name == "Joueurs en attente":
#                 my_field = field
#                 field_ID = i

#         user = interaction.user.mention
#         content = my_field.value
#         list_val = my_field.value.split('\n')
#         for val in list_val:
#             if user in val:
#                 list_val.remove(val)

#         embed.set_field_at(field_ID, name = 'Joueurs en attente',
#                            value = '\n'.join(list_val),
#                            inline = False)

#         await interaction.response.edit_message(embed = embed)


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

        self.helloasso_client: HelloAssoClient = helloasso_client
        self.gsheet_client: GoogleSheetsClient = gsheet_client

        self.client = commands.Bot(command_prefix = '!', intents = self.intents)
        self.client.parent_client = self
        self.tree = self.client.tree

        
        self.logger = logging.getLogger(__name__)

        self.token = token
        self.thalos_guild = None
        self.thalos_role = None

        self.start_future = None
        self.run = True

        # Commands
        @self.tree.command(guild = self.thalos_guild,
                           description = """
                           Envoie un signal à l'application et affiche le
                           temps de latence
                           """)
        async def ping(interaction: discord.Interaction):
            embed = MessageTemplate(
                title = 'Pong !',
                description = (
                    f'Bot ping is {round(1000*self.client.latency)} ms'),
            )
            
            await interaction.response.send_message(embed = embed,
                                                    ephemeral = True)
            
            
        @self.tree.command(
            guild = self.thalos_guild,
            description = "L'application répète le message envoyé")
        @app_commands.describe(text = 'Texte à répéter')
        @app_commands.rename(text = 'texte')
        async def echo(interaction: discord.Interaction, text: str):
            embed = MessageTemplate(
                description = text,
                )
            await interaction.response.send_message(embed = embed,
                                                    ephemeral = True)


        @self.tree.command(guild = self.thalos_guild)
        async def my_roles(interaction: discord.Interaction,
                           show: bool = False):
            embed = MessageTemplate(
                title = 'Tu possèdes les rôles suivants : ', 
                description = ''.join(
                    [role.mention + '\n' for role in interaction.user.roles[::-1]]
                ),
                )
            await interaction.response.send_message(
                    embed = embed, ephemeral = not show)
            

            
        @self.tree.command(guild = self.thalos_guild,
                           description = """
                           Affiche les utilisateurs ayant le rôle fourni en
                           paramètre
                           """)
        @app_commands.rename(role = 'rôle')
        @app_commands.describe(role =  'Role dont il faut lister les membres')
        async def whois(interaction: discord.Interaction,
                        role: discord.Role,
                        show: bool = False):

            embed = MessageTemplate(
                description = (f'Les membres ayant le role {role.mention}'
                               + 'sont :'), 
                )
            max_fields = 25
            number_by_field = len(role.members) // max_fields + 1

            for i in range(min(max_fields, len(role.members))):
                embed.add_field(name = '', value = ''.join(
                    [member.mention + '\n'
                     for member in role.members[i::max_fields]]))
            await interaction.response.send_message(embed = embed,
                                                    ephemeral = not show)
        

            
        @self.tree.context_menu(name = 'Epingler',
                                guild = self.thalos_guild)
        @app_commands.checks.has_role('Administrateurs')
        async def pin(interaction: discord.Interaction,
                      message: discord.Message):
            try:
                await message.pin()
                embed = MessageTemplate(description = 'Message épinglé !')
                await interaction.response.send_message(embed = embed,
                                                        ephemeral = True)
            except discord.errors.HTTPException as e:
                await interaction.response.send_message(e, ephemeral = True)


                
        @app_commands.checks.has_role('Administrateurs')
        @self.tree.command(guild = self.thalos_guild,
                           description = """
                           Donne un rôle à tous les membres ayant le rôle
                           fourni en paramètre
                           """)
        @app_commands.describe(role_given = 'Rôle à donner',
                               user_group = """Groupe d'utilisateurs recevant
                               le nouveau rôle""")
        async def give_role(interaction: discord.Interaction,
                            role_given: discord.Role,
                            user_group: discord.Role):

            message = ''
            await interaction.response.defer()
            for member in user_group.members:
                try:
                    await member.add_roles(role_given)
                    message = (
                        message
                        + f'Le role {role_given.mention} '
                        + f'est accordé à {member.mention}\n'
                        )
                    self.logger.info(message)
                    
                except Exception as e:
                    message += str(e)
                    embed = MessageTemplate(
                        title = 'Une erreur est survenue...',
                        description = message
                        )
                    await interaction.followup.send(embed = embed)
                    raise

            embed = MessageTemplate(
                title = 'Affectation de roles :',
                description = message)
            await interaction.followup.send(embed = embed)


        @app_commands.checks.has_role('Administrateurs')
        @self.tree.command(guild = self.thalos_guild,
                           description = """
                           Vérifie si une personne est adhérente de
                           l'association """)
        async def check_member(interaction: discord.Interaction):
            data = {'prenom' : '',
                    'nom' : ''}
            modal = CheckModal()
            await interaction.response.send_modal(modal)
            await modal.wait()

        @self.tree.command(guild = self.thalos_guild,
                           description = """Ajoute le membre au groupe des
                           adhérents sur le discord""")
        async def make_membercheck(interaction: discord.Interaction):
            embed = MessageTemplate(
                title = 'Obtenir votre role de membre sur le discord',
                description = '')
            buttons = MemberProcessView(timeout = None,
                                        client = self.client.parent_client)
            await interaction.response.send_message(embed = embed,
                                                    view = buttons)

            
        @self.tree.command(guild = self.thalos_guild,
                           description = """
                           Lance la procédure de mise à jour des adhérents sur
                           le discord""")
        async def update_member_list(interaction: discord.Interaction):
            role = interaction.guild.get_role(1310285968393371770)
            member_list = await self.gsheet_client.get_members_by_discord_names(
                [member.name for member in interaction.guild.members])

            to_member = []
            to_unmember = []
            to_keep = []
            unaffected = []
            for member in member_list:
                member_obj = interaction.guild.get_member_named(member.discord_nickname)
                if member.member_current_year and role in member_obj.roles:
                    to_keep.append(member.discord_nickname)
                elif member.member_current_year:
                    to_member.append(member.discord_nickname)
                elif role in member_obj.roles:
                    to_unmember.append(member.discord_nickname)
                else:
                    unaffected.append(member.discord_nickname)

            embed = MessageTemplate(
                title = """ Mise à jour des adhérents sur le Discord""")

            # get the user list to member
            to_mem_str = ', '.join(
                [interaction.guild.get_member_named(member).mention
                 for member in to_member])

            # get members to display
            if len(to_mem_str) > 1000:
                display_mem_l = to_mem_str[:1000].split(',')[:-1]
            else:
                display_mem_l = to_mem_str.split(',')

            hidden_member_members = len(to_member) - len(display_mem_l)

            # make message
            to_mem_str_short = (
                ','.join(display_mem_l)
                + f'\n{max(0, hidden_member_members)}')
            if hidden_member_members <= 1:
                to_mem_str_short += ' utilisateur masqué'
            else:
                to_mem_str_short += ' utilisateurs masqués'
            
            # get the user list to unmember    
            to_unmem_str = ', '.join(
                [interaction.guild.get_member_named(member).mention
                 for member in to_unmember])

            # get unmembers to display
            if len(to_unmem_str) > 1000:
                display_unmem_l = to_unmem_str[:1000].split(',')[:-1]
            else:
                display_unmem_l = to_unmem_str.split(',')

            hidden_unmem_members = len(to_unmember) - len(display_unmem_l)
            
            # make message            
            to_unmem_str_short = (
                ','.join(display_unmem_l)
                + f'\n{max(0, hidden_unmem_members)}')
            if hidden_unmem_members <= 1:
                to_unmem_str_short += ' utilisateur masqué'
            else:
                to_unmem_str_short += ' utilisateurs masqués'                
            
            # get members unchanged     
            to_keep_str = ', '.join(
                [interaction.guild.get_member_named(member).mention
                 for member in to_keep])

            # get members unchanged to display
            if len(to_keep_str) > 1000:
                display_keep_l = to_keep_str[:1000].split(',')[:-1]
            else:
                display_keep_l = to_keep_str.split(',')

            hidden_keep_members = len(to_keep) - len(display_keep_l)
            
            # make message            
            to_keep_str_short = (
                ','.join(display_keep_l)
                + f'\n{max(0, hidden_keep_members)}')
            if hidden_keep_members <= 1:
                to_keep_str_short += ' utilisateur masqué'
            else:
                to_keep_str_short += ' utilisateurs masqués'
                
            embed.add_field(
                name = 'Ces utilisateurs gagneront le role membre :',
                value = to_mem_str_short,
                inline = False)
            embed.add_field(
                name = 'Ces utilisateurs conserveront leur role membre :',
                value = to_keep_str_short,
                inline = False)
            embed.add_field(
                name = 'Ces utilisateurs perdront leur role membre :',
                value = to_unmem_str_short,
                inline = False)

            class Buttons(discord.ui.View):
                def __init__(self, logger, *args, **kwargs):
                    super().__init__(*args, **kwargs)
                    self.logger = logger
                
                @discord.ui.button(label = 'Afficher les membres masqués',
                                   style = discord.ButtonStyle.primary,
                                   disabled = True,
                                   custom_id = 'display')
                async def button_display(self, interaction, button):
                    pass
                
                @discord.ui.button(label = 'Confirmer',
                                   style = discord.ButtonStyle.success,
                                   disabled = False,
                                   custom_id = 'confirm')
                async def button_confirm(self, interaction, button):
                    await interaction.response.defer()
                    for user in to_unmember:
                        user = interaction.guild.get_member_named(user)
                        await user.remove_roles(role)                        
                        self.logger.info(
                            f'{user} is removed from the member list')

                    for user in to_member:
                        user = interaction.guild.get_member_named(user)
                        await user.add_roles(role)
                        self.logger.info(f'{user} is added to the member list')

                    embed.description = 'Liste des membres mise à jour'
                    embed.clear_fields()
                    await interaction.followup.send(embed = embed)

                
                @discord.ui.button(label = 'Annuler',
                                   style = discord.ButtonStyle.danger,
                                   disabled = False,
                                   custom_id = 'cancel')
                async def button_cancel(self, interaction, button):
                    for item in self.children:
                        item.disabled = True

                    embed.description = 'COMMANDE ANNULÉE'
                    embed.clear_fields()

                    await interaction.response.edit_message(embed = embed,
                                                            view = buttons)



                    
            buttons = Buttons(logger = self.logger)


            await interaction.response.send_message(embed = embed,
                                                    view = buttons)

        
        @app_commands.checks.has_any_role('Administrateurs', 'Bureau')
        @self.tree.context_menu(name = 'Informations utilisateur',
                                guild = self.thalos_guild)
        async def info(interaction: discord.Interaction,
                       member: discord.Member):
            self.logger.info(f'context info called by {interaction.user.name}')

            first_name = 'INCONNU'
            last_name = 'INCONNU'

            member_info: MemberInfo = (
                await self.gsheet_client.get_member_by_discord_name(
                    member.name)
                )

            if member_info.in_spreadsheet:
                first_name = member_info.first_name
                last_name = member_info.last_name
            
            embed = MessageTemplate(title = "Informations sur l'utilisateur :")
            embed.add_field(name = 'Pseudo discord', value = member.mention)
            embed.add_field(name = 'Nom', value = last_name)
            embed.add_field(name = 'Prénom', value = first_name)
                                    
            await interaction.response.send_message(embed = embed, ephemeral = True)

                
                
        # @self.tree.command(guild = self.thalos_guild)
        # async def make_table(interaction: discord.Interaction):
        #     embed = MessageTemplate(
        #         title = 'Organisation du 14/12/24')
        #     embed.add_field(name = 'Parties prévues (1v1)',
        #                     value = '',
        #                     inline = False)
        #     embed.add_field(name = 'Joueurs en attente',
        #                     value = '',
        #                     inline = False)
        #     await interaction.response.send_message(embed = embed,
        #                                             view = MyView())
        
                            
            
        # Events
        @self.client.event
        async def on_ready() -> None:
            self.logger.info(f"Logged as {self.client.user}")
            #self.client.tree.clear_commands(guild = self.thalos_guild)
            for command in await self.client.tree.sync(
                    guild = self.thalos_guild):
                self.logger.info(f'Command "{command.name}" synced to the app')
            self.logger.info("Commands added")

        @self.client.event
        async def on_app_command_completion(
                interaction: discord.Interaction,
                command: Union[discord.app_commands.Command,
                               discord.app_commands.ContextMenu]):
            self.logger.info(
                f'Command {command.name} has successfully completed')

        @self.client.event
        async def on_interaction(interaction: discord.Interaction):
            if not interaction.command is None:
                self.logger.info(
                    f'Command {interaction.command.name}'
                    + f' is called by {interaction.user}'
                    + f' with these arguments :'
                    + f' {interaction.namespace}')
                
            
    #     @self.client.event
    #     async def on_message(message) -> None:
    #         self.logger.debug(
    #             f"message {message.content} received from {message.author}"
    #         )

    #         if message.author == self.client.user:
    #             return

    #         if message.channel.type == discord.ChannelType.private:
    #             await self.process_dm(message)

    # async def process_dm(self, message: discord.Message) -> None:
    #     """Process the DMs received by the bot and takes associated actions

    #     Args:
    #         message (discord.Message): _description_
    #     """
    #     await self.populate_guild_data()

    #     member = self.thalos_guild.get_member(message.author.id)
    #     if member is None:
    #         self.logger.info(
    #             f"{message.author.name} dm'd the bot but is not in the server"
    #         )
    #         await message.channel.send(
    #             "Ce bot n'a d'interêt que si vous êtes membre du serveur du thalos !"
    #         )
    #         return

    #     if self.thalos_role in member.roles:
    #         self.logger.info(
    #             f"{message.author.name} dm'd the bot but already has the role"
    #         )
    #         await message.channel.send(
    #             f"Bonjour {message.author.name}. Vous êtes déjà membre !"
    #         )
    #         return

    #     if message.content.startswith("thalosien"):
    #         content = message.content.split(" ")
    #         if len(content) < 3:
    #             await message.channel.send(
    #                 f'Bonjour {message.author.name}. Pour avoir le rôle membre, tapez "thalosien Prénom Nom ". Le bot va vérifier votre adhésion.'
    #             )
    #             return

    #         first_name, last_name = content[1], content[2]
    #         self.logger.info(f"{message.author.name} tried to get the role")
    #         await self.process_membership(
    #             member=member, first_name=first_name, last_name=last_name
    #         )
    #         return

    #     self.logger.info(f"{message.author.name} dm'd the bot with a random message")
    #     await message.channel.send(
    #         f'Bonjour {message.author.name}. Pour avoir le rôle membre, tapez "thalosien Prénom Nom ". Le bot va vérifier votre adhésion.'
    #     )
    #     return

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

    # async def populate_guild_data(self) -> None:
    #     """Fills the class attributes with the necessary guild and membership role"""
    #     if self.thalos_guild is None:
    #         self.thalos_guild = self.client.get_guild(int(getenv("THALOS_GUILD_ID")))
    #         if self.thalos_guild is not None:
    #             self.thalos_role = self.thalos_guild.get_role(
    #                 int(getenv("MEMBER_ROLE_ID"))
    #             )
    #         else:
    #             self.logger.warning("Could not get the member role")
    #             return

    # async def get_member(self, user_id: int) -> discord.Member:
    #     """Get the discord member with user_id

    #     Args:
    #         user_id (int): The user id

    #     Returns:
    #         discord.Member: the discord member
    #     """
    #     await self.populate_guild_data()
    #     member = self.thalos_guild.get_member(user_id)
    #     if member is None:
    #         self.logger.warning(f"User {user_id} could not be found")

    #     return member

    # async def process_membership(
    #     self, member: discord.Member, first_name: str, last_name: str
    # ) -> None:
    #     async with asyncio.TaskGroup() as tg:
    #         ha_task = tg.create_task(
    #             self.helloasso_client.get_membership(
    #                 first_name=first_name,
    #                 last_name=last_name,
    #             )
    #         )

    #         real_name_gsheet_task = tg.create_task(
    #             self.gsheet_client.get_member_by_name(
    #                 first_name=first_name, last_name=last_name
    #             )
    #         )

    #         discord_name_gsheet_task = tg.create_task(
    #             self.gsheet_client.get_member_by_discord_name(discord_name=member.name)
    #         )

    #     is_member = ha_task.result()
    #     real_name_member_info: MemberInfo = real_name_gsheet_task.result()
    #     discord_name_member_info: MemberInfo = discord_name_gsheet_task.result()

    #     if not is_member:
    #         self.logger.info(
    #             f"{first_name} {last_name} got denied the role, not a HelloAsso member"
    #         )
    #         await member.send(
    #             "Tu n'es apparemment pas membre. Vérifie que tu as envoyé les mêmes noms et prénoms que lors de ton inscription sur HelloAsso !"
    #         )
    #         return

    #     if discord_name_member_info.in_spreadsheet and (
    #         discord_name_member_info.first_name.lower() != first_name.lower()
    #         or discord_name_member_info.last_name.lower() != last_name.lower()
    #     ):
    #         self.logger.info(
    #             f"{member.name} got denied the role with {first_name} {last_name}, "
    #             "this discord name is already associated with {discord_name_member_info.first_name}, {discord_name_member_info.last_name}"
    #         )
    #         await member.send(
    #             "Ce compte est associé à un autre nom. Contactez un admin."
    #         )
    #         return

    #     if (
    #         real_name_member_info.in_spreadsheet
    #         and real_name_member_info.discord_nickname.lower() != member.name
    #     ):
    #         self.logger.info(
    #             f"{member.name} got denied the role with {first_name} {last_name}, "
    #             "this discord name is already associated with {discord_name_member_info.discord_nickname}"
    #         )
    #         await member.send(
    #             "Ce nom est associé à un autre pseudo discord. Contactez un admin."
    #         )
    #         return

    #     await self.set_membership(member, first_name, last_name)

    # async def set_membership(
    #     self, member: discord.Member, first_name: str, last_name: str
    # ) -> None:
    #     """Set the membership on discord and updates the spreadsheet

    #     Args:
    #         member (discord.Member): Discord guild member information
    #         first_name (str): First name of the member
    #         last_name (str): Last name of the member
    #     """
    #     await member.add_roles(self.thalos_role)
    #     await member.send("Tu es maintenant membre sur le serveur !")
    #     self.logger.info(f"{member.name} now has the thalos member role")

    #     member_info = MemberInfo(
    #         first_name=first_name,
    #         last_name=last_name,
    #         discord_nickname=member.name,
    #         server_nickname=member.display_name,
    #     )

    #     ret = await self.gsheet_client.add_member(member_info)
    #     if not ret:
    #         self.logger.error(f"Could not add {member_info} to spreadsheet")

    #     self.logger.info(f"{member_info} added to spreadsheet")
