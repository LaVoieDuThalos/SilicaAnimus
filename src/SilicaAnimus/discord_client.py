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


class UpdateMemberButtons(discord.ui.View):
    def __init__(self, logger, embed, role, data: dict, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.logger = logger
        self.embed = embed
        self.data = data
        self.role = role
                
    @discord.ui.button(label = 'Afficher les membres masqués',
                       style = discord.ButtonStyle.primary,
                       disabled = True,
                       custom_id = 'display')
    async def button_display(self,
                             interaction: discord.Interaction,
                             button: discord.ui.Button):
        pass
                
    @discord.ui.button(label = 'Confirmer',
                       style = discord.ButtonStyle.success,
                       disabled = False,
                       custom_id = 'confirm')
    async def button_confirm(self,
                             interaction: discord.Interaction,
                             button: discord.ui.Button):
        await interaction.response.defer()
        for user in self.data['to_unmember']:
            user = interaction.guild.get_member_named(user)
            await user.remove_roles(self.role)                        
            self.logger.info(
                f'{user} is removed from the member list')

        for user in self.data['to_member']:
            user = interaction.guild.get_member_named(user)
            await user.add_roles(self.role)
            self.logger.info(f'{user} is added to the member list')

        self.embed.description = 'Liste des membres mise à jour'
        self.embed.clear_fields()
        await interaction.followup.send(embed = self.embed)

                
    @discord.ui.button(label = 'Annuler',
                       style = discord.ButtonStyle.danger,
                       disabled = False,
                       custom_id = 'cancel')
    async def button_cancel(self,
                            interaction: discord.Interaction,
                            button: discord.ui.Button):
        for item in self.children:
            item.disabled = True
            
        self.embed.description = 'COMMANDE ANNULÉE'
        self.embed.clear_fields()
            
        await interaction.response.edit_message(embed = self.embed,
                                                view = self)


@app_commands.command(
    description = """
    Envoie un signal à l'application et affiche le temps de latence
    """)
async def ping(interaction: discord.Interaction):
    client = interaction.client
    embed = MessageTemplate(
        title = 'Pong Pong!',
        description = (
            f'Bot ping is {round(1000*client.latency)} ms'))
    
    await interaction.response.send_message(embed = embed,
                                            ephemeral = True)


@app_commands.command(
    description = "L'application répète le message envoyé")
@app_commands.describe(text = 'Texte à répéter')
@app_commands.rename(text = 'texte')
async def echo(interaction: discord.Interaction, text: str):
    embed = MessageTemplate(
        description = text,
    )
    await interaction.response.send_message(embed = embed,
                                            ephemeral = True)

@app_commands.command(
    description = 'Fais la listes des rôles que tu possèdes')
@app_commands.describe(show = 'Envoyer la réponse en public ?')
@app_commands.rename(show = 'montrer')
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

@app_commands.command(
    description = """
    Affiche les utilisateurs ayant le rôle fourni en paramètre
    """)
@app_commands.rename(role = 'rôle')
@app_commands.describe(role =  'Role dont il faut lister les membres')
async def whois(interaction: discord.Interaction,
                role: discord.Role,
                show: bool = False):
    embed = MessageTemplate(
        description = f'Les membres ayant le role {role.mention} sont :')
    max_fields = 25
    number_by_field = len(role.members) // max_fields + 1

    for i in range(min(max_fields, len(role.members))):
        embed.add_field(name = '', value = ''.join(
            [member.mention + '\n'
             for member in role.members[i::max_fields]]))
    await interaction.response.send_message(embed = embed,
                                            ephemeral = not show)

            
@app_commands.context_menu(name = 'Epingler')
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
@app_commands.command(
    description =
    """ Vérifie si une personne est adhérente de l'association """)
async def check_member(interaction: discord.Interaction):
    data = {'prenom' : '',
            'nom' : ''}
    modal = CheckModal()
    await interaction.response.send_modal(modal)
    await modal.wait()


@app_commands.checks.has_role('Administrateurs')
@app_commands.command(
    description = """
    Donne un rôle à tous les membres ayant le rôle fourni en paramètre
    """)
@app_commands.describe(
    role_given = 'Rôle à donner',
    user_group = """Groupe d'utilisateurs recevant le nouveau rôle"""
    )
async def give_role(
        interaction: discord.Interaction,
        role_given: discord.Role,
        user_group: discord.Role,
        show: bool = False):
    client = interaction.client

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
            client.logger.info(message)
            
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
    await interaction.followup.send(embed = embed,
                                    ephemeral = not show)


@app_commands.command(description =
                      """Ajoute le membre au groupe des
                      adhérents sur le discord""")
async def make_membercheck(interaction: discord.Interaction):
    client = interaction.client
    embed = MessageTemplate(
        title = 'Obtenir votre role de membre sur le discord',
        description = '')
    buttons = MemberProcessView(timeout = None,
                                client = client.parent_client)
    await interaction.response.send_message(embed = embed,
                                            view = buttons)
        
@app_commands.checks.has_any_role('Administrateurs', 'Bureau')
@app_commands.context_menu(name = 'Informations utilisateur')
async def info(interaction: discord.Interaction,
               member: discord.Member):
    client = interaction.client
    parent = client.parent_client

    first_name = 'INCONNU'
    last_name = 'INCONNU'

    member_info: MemberInfo = (
        await parent.gsheet_client.get_member_by_discord_name(
            member.name)
    )

    if member_info.in_spreadsheet:
        first_name = member_info.first_name
        last_name = member_info.last_name
            
    embed = MessageTemplate(title = "Informations sur l'utilisateur :")
    embed.add_field(name = 'Pseudo discord', value = member.mention)
    embed.add_field(name = 'Nom', value = last_name)
    embed.add_field(name = 'Prénom', value = first_name)
                                    
    await interaction.response.send_message(embed = embed,
                                            ephemeral = True)

            
@app_commands.command(
    description = """
    Lance la procédure de mise à jour des adhérents sur le discord"""
    )
async def update_member_list(interaction: discord.Interaction):
    role = interaction.guild.get_role(678922012109963294)
    client = interaction.client
    parent = client.parent_client
    member_list = await parent.gsheet_client.get_members_by_discord_names(
        [member.name for member in interaction.guild.members])

    to_member = []
    to_unmember = []
    to_keep = []
    unaffected = []
    for member in member_list:
        member_obj = interaction.guild.get_member_named(
            member.discord_nickname)
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

                    
    buttons = UpdateMemberButtons(logger = client.logger, embed = embed,
                                  role = role,
                                  data = {'to_member': to_member,
                                          'to_unmember': to_unmember})


    await interaction.response.send_message(embed = embed,
                                            view = buttons)


    
class ThalosBot(commands.Bot):

    async def setup_hook(self):
        self.logger.info('Running setup hook')
        commands = [
            ping, echo, my_roles, whois, pin, check_member, give_role,
            make_membercheck, info, update_member_list,
            ]
        for command in commands:
            self.tree.add_command(command, guild = self.thalos_guild)


    async def on_ready(self) -> None:
        self.logger.info(f"Logged as {self.user}")
        #self.client.tree.clear_commands(guild = self.thalos_guild)
        for command in await self.tree.sync(
                guild = self.thalos_guild): 
            self.logger.info(f'Command "{command.name}" synced to the app')
        self.logger.info("Commands added")


    async def on_app_command_completion(self,
            interaction: discord.Interaction,
            command: Union[discord.app_commands.Command,
                           discord.app_commands.ContextMenu]):
        self.logger.info(
            f'Command {command.name} has successfully completed')


    async def on_interaction(self, interaction: discord.Interaction):
        if not interaction.command is None:
            self.logger.info(
                f'Command {interaction.command.name}'
                + f' is called by {interaction.user}'
                + f' with these arguments :'
                + f' {interaction.namespace}')

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

        self.client = ThalosBot(
            command_prefix = '!', intents = self.intents)

        
        self.client.parent_client = self
        self.tree = self.client.tree

        
        self.logger = self.client.logger = logging.getLogger(__name__)

        self.token = token
        self.client.thalos_guild = self.thalos_guild = None
        self.thalos_role = None


        self.start_future = None
        self.run = True


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

