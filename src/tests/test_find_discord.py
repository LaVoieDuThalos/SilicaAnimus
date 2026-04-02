import pytest
from unittest.mock import AsyncMock, MagicMock, patch

import discord

from SilicaAnimus.discord_client import FindDiscordModal, _bureau_or_admin_predicate
from SilicaAnimus.google_sheets_client import MemberInfo

pytest_plugins = ("pytest_asyncio",)


def make_interaction(gsheet_client, guild_member=None):
    interaction = MagicMock()
    interaction.client.parent_client.gsheet_client = gsheet_client
    interaction.response.send_message = AsyncMock()
    interaction.guild.get_member_named = MagicMock(return_value=guild_member)
    return interaction


class TestFindDiscord:
    @pytest.mark.asyncio
    async def test_find_discord_member_found(self):
        """Member is in spreadsheet with a linked Discord account found on the server"""
        gsheet_client = MagicMock()
        gsheet_client.get_member_by_name = AsyncMock(
            return_value=MemberInfo(
                first_name="Paul",
                last_name="Bismuth",
                discord_nickname="paul_b",
                in_spreadsheet=True,
            )
        )

        guild_member = MagicMock()
        guild_member.name = "paul_bismuth"
        guild_member.display_name = "paul_b"

        modal = FindDiscordModal()
        modal.prenom = MagicMock(value="Paul")
        modal.nom = MagicMock(value="Bismuth")

        interaction = make_interaction(gsheet_client, guild_member=guild_member)
        await modal.on_submit(interaction)

        call_kwargs = interaction.response.send_message.call_args
        embed = call_kwargs.kwargs["embed"]
        assert "paul_bismuth" in embed.description
        assert "paul_b" in embed.description
        assert call_kwargs.kwargs["ephemeral"] is True

    @pytest.mark.asyncio
    async def test_find_discord_member_found_not_on_server(self):
        """Member is in spreadsheet but their Discord account is not on the server"""
        gsheet_client = MagicMock()
        gsheet_client.get_member_by_name = AsyncMock(
            return_value=MemberInfo(
                first_name="Paul",
                last_name="Bismuth",
                discord_nickname="paul_b",
                in_spreadsheet=True,
            )
        )

        modal = FindDiscordModal()
        modal.prenom = MagicMock(value="Paul")
        modal.nom = MagicMock(value="Bismuth")

        interaction = make_interaction(gsheet_client, guild_member=None)
        await modal.on_submit(interaction)

        call_kwargs = interaction.response.send_message.call_args
        embed = call_kwargs.kwargs["embed"]
        assert "paul_b" in embed.description
        assert "introuvable" in embed.description

    @pytest.mark.asyncio
    async def test_find_discord_member_no_discord(self):
        """Member is in spreadsheet but has no linked Discord account"""
        gsheet_client = MagicMock()
        gsheet_client.get_member_by_name = AsyncMock(
            return_value=MemberInfo(
                first_name="Paul",
                last_name="Bismuth",
                discord_nickname="",
                in_spreadsheet=True,
            )
        )

        modal = FindDiscordModal()
        modal.prenom = MagicMock(value="Paul")
        modal.nom = MagicMock(value="Bismuth")

        interaction = make_interaction(gsheet_client)
        await modal.on_submit(interaction)

        call_kwargs = interaction.response.send_message.call_args
        embed = call_kwargs.kwargs["embed"]
        assert "pas de compte Discord associé" in embed.description

    @pytest.mark.asyncio
    async def test_find_discord_member_not_found(self):
        """Member is not in the spreadsheet"""
        gsheet_client = MagicMock()
        gsheet_client.get_member_by_name = AsyncMock(
            return_value=MemberInfo(
                first_name="Inconnu",
                last_name="Inconnu",
                in_spreadsheet=False,
            )
        )

        modal = FindDiscordModal()
        modal.prenom = MagicMock(value="Inconnu")
        modal.nom = MagicMock(value="Inconnu")

        interaction = make_interaction(gsheet_client)
        await modal.on_submit(interaction)

        call_kwargs = interaction.response.send_message.call_args
        embed = call_kwargs.kwargs["embed"]
        assert "n'a pas été trouvé" in embed.description


class TestBureauOrAdminCheck:
    def _make_interaction(self, role_ids):
        interaction = MagicMock(spec=discord.Interaction)
        roles = [MagicMock(id=rid) for rid in role_ids]
        interaction.user.roles = roles
        return interaction

    @pytest.mark.asyncio
    async def test_admin_role_is_allowed(self):
        with patch.dict("os.environ", {"ADMIN_ROLE_ID": "100", "BUREAU_ROLE_ID": "200"}):
            interaction = self._make_interaction([100])
            assert await _bureau_or_admin_predicate(interaction) is True

    @pytest.mark.asyncio
    async def test_bureau_role_is_allowed(self):
        with patch.dict("os.environ", {"ADMIN_ROLE_ID": "100", "BUREAU_ROLE_ID": "200"}):
            interaction = self._make_interaction([200])
            assert await _bureau_or_admin_predicate(interaction) is True

    @pytest.mark.asyncio
    async def test_other_role_is_denied(self):
        with patch.dict("os.environ", {"ADMIN_ROLE_ID": "100", "BUREAU_ROLE_ID": "200"}):
            interaction = self._make_interaction([999])
            assert await _bureau_or_admin_predicate(interaction) is False
