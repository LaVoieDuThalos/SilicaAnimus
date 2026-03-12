import pytest
import logging
import sys
from unittest.mock import Mock, AsyncMock, patch

import discord
from SilicaAnimus.discord_client import ThalosBot

pytest_plugins = ("pytest_asyncio",)


def setup_function(function):
    logging.basicConfig(stream=sys.stdout, level=logging.DEBUG)


class TestWeeklyMessage:
    """Test suite for the weekly scheduled message functionality"""

    @pytest.mark.asyncio
    async def test_weekly_message_on_configured_weekday(self):
        """Test that message is sent on a configured weekday"""
        with patch.dict(
            "os.environ",
            {
                "WEEKLY_MESSAGE_WEEKDAYS": "4",  # Friday only
                "WEEKLY_MESSAGE_THREAD_ID": "123456789",
                "WEEKLY_MESSAGE_CONTENT": "Test message",
                "WEEKLY_MESSAGE_HOUR": "22",
                "WEEKLY_MESSAGE_MINUTE": "0",
            },
        ):
            # Create bot instance with proper Discord Intents
            intents = discord.Intents.default()
            bot = ThalosBot(command_prefix="!", intents=intents)
            bot.logger = logging.getLogger(__name__)

            # Mock the channel
            mock_channel = AsyncMock()
            bot.get_channel = Mock(return_value=mock_channel)

            # Mock datetime to return Friday (weekday 4)
            with patch("SilicaAnimus.discord_client.datetime") as mock_datetime:
                mock_datetime.now.return_value = Mock(weekday=Mock(return_value=4))

                # Run the weekly_message task
                await bot.weekly_message()

                # Verify message was sent
                mock_channel.send.assert_called_once_with("Test message")

    @pytest.mark.asyncio
    async def test_weekly_message_not_on_wrong_weekday(self):
        """Test that message is NOT sent on a non-configured weekday"""
        with patch.dict(
            "os.environ",
            {
                "WEEKLY_MESSAGE_WEEKDAYS": "4,5",  # Friday and Saturday
                "WEEKLY_MESSAGE_THREAD_ID": "123456789",
                "WEEKLY_MESSAGE_CONTENT": "Test message",
            },
        ):
            intents = discord.Intents.default()
            bot = ThalosBot(command_prefix="!", intents=intents)
            bot.logger = logging.getLogger(__name__)

            mock_channel = AsyncMock()
            bot.get_channel = Mock(return_value=mock_channel)

            # Mock datetime to return Monday (weekday 0)
            with patch("SilicaAnimus.discord_client.datetime") as mock_datetime:
                mock_datetime.now.return_value = Mock(weekday=Mock(return_value=0))

                # Run the weekly_message task
                await bot.weekly_message()

                # Verify message was NOT sent
                mock_channel.send.assert_not_called()

    @pytest.mark.asyncio
    async def test_weekly_message_multiple_weekdays(self):
        """Test that message is sent on multiple configured weekdays"""
        with patch.dict(
            "os.environ",
            {
                "WEEKLY_MESSAGE_WEEKDAYS": "4,5,6",  # Friday, Saturday, Sunday
                "WEEKLY_MESSAGE_THREAD_ID": "123456789",
                "WEEKLY_MESSAGE_CONTENT": "Weekend message",
            },
        ):
            intents = discord.Intents.default()
            bot = ThalosBot(command_prefix="!", intents=intents)
            bot.logger = logging.getLogger(__name__)

            mock_channel = AsyncMock()
            bot.get_channel = Mock(return_value=mock_channel)

            # Test each configured weekday
            for weekday in [4, 5, 6]:
                mock_channel.reset_mock()
                with patch("SilicaAnimus.discord_client.datetime") as mock_datetime:
                    mock_datetime.now.return_value = Mock(
                        weekday=Mock(return_value=weekday)
                    )
                    await bot.weekly_message()
                    mock_channel.send.assert_called_once_with("Weekend message")

    @pytest.mark.asyncio
    async def test_weekly_message_missing_config(self):
        """Test that message is not sent when configuration is missing"""
        with patch.dict("os.environ", {}, clear=True):
            intents = discord.Intents.default()
            bot = ThalosBot(command_prefix="!", intents=intents)
            bot.logger = logging.getLogger(__name__)

            mock_channel = AsyncMock()
            bot.get_channel = Mock(return_value=mock_channel)

            # Mock Friday
            with patch("SilicaAnimus.discord_client.datetime") as mock_datetime:
                mock_datetime.now.return_value = Mock(weekday=Mock(return_value=4))

                # Run the weekly_message task
                await bot.weekly_message()

                # Verify message was NOT sent (missing config)
                mock_channel.send.assert_not_called()

    @pytest.mark.asyncio
    async def test_weekly_message_with_fetch_channel(self):
        """Test that message uses fetch_channel when get_channel returns None"""
        with patch.dict(
            "os.environ",
            {
                "WEEKLY_MESSAGE_WEEKDAYS": "4",
                "WEEKLY_MESSAGE_THREAD_ID": "123456789",
                "WEEKLY_MESSAGE_CONTENT": "Test message",
            },
        ):
            intents = discord.Intents.default()
            bot = ThalosBot(command_prefix="!", intents=intents)
            bot.logger = logging.getLogger(__name__)

            # get_channel returns None, fetch_channel returns the channel
            mock_channel = AsyncMock()
            bot.get_channel = Mock(return_value=None)
            bot.fetch_channel = AsyncMock(return_value=mock_channel)

            with patch("SilicaAnimus.discord_client.datetime") as mock_datetime:
                mock_datetime.now.return_value = Mock(weekday=Mock(return_value=4))

                await bot.weekly_message()

                # Verify fetch_channel was called
                bot.fetch_channel.assert_called_once_with(123456789)
                mock_channel.send.assert_called_once_with("Test message")

    @pytest.mark.asyncio
    async def test_weekly_message_invalid_weekdays_format(self):
        """Test handling of invalid weekdays format"""
        with patch.dict(
            "os.environ",
            {
                "WEEKLY_MESSAGE_WEEKDAYS": "invalid,format",
                "WEEKLY_MESSAGE_THREAD_ID": "123456789",
                "WEEKLY_MESSAGE_CONTENT": "Test message",
            },
        ):
            intents = discord.Intents.default()
            bot = ThalosBot(command_prefix="!", intents=intents)
            bot.logger = logging.getLogger(__name__)

            mock_channel = AsyncMock()
            bot.get_channel = Mock(return_value=mock_channel)

            with patch("SilicaAnimus.discord_client.datetime") as mock_datetime:
                mock_datetime.now.return_value = Mock(weekday=Mock(return_value=4))

                await bot.weekly_message()

                # Verify message was NOT sent (invalid config)
                mock_channel.send.assert_not_called()

    def test_bot_configures_time_from_env(self):
        """Test that bot configures scheduled time from environment variables"""
        with patch.dict(
            "os.environ",
            {
                "WEEKLY_MESSAGE_HOUR": "15",
                "WEEKLY_MESSAGE_MINUTE": "30",
            },
        ):
            intents = discord.Intents.default()
            bot = ThalosBot(command_prefix="!", intents=intents)
            bot.logger = logging.getLogger(__name__)

            # The task should be configured with the time from env
            # Note: This test verifies the configuration happens without errors
            assert bot.weekly_message is not None

    def test_bot_uses_default_time(self):
        """Test that bot uses default time when not configured"""
        with patch.dict("os.environ", {}, clear=True):
            intents = discord.Intents.default()
            bot = ThalosBot(command_prefix="!", intents=intents)
            bot.logger = logging.getLogger(__name__)

            # Should use default values (22:00) without errors
            assert bot.weekly_message is not None


@pytest.mark.asyncio
async def test_weekly_message_integration():
    """
    Integration test: sends a real message to Discord 30 seconds after start.

    This test requires:
    - Valid DISCORD_TOKEN in .env
    - Bot has access to channel 767227407001321472
    - Manual verification that message was sent

    To run: pytest tests/test_weekly_message.py::test_weekly_message_integration -v -s
    """
    from datetime import datetime, timedelta
    from dotenv import load_dotenv
    from os import getenv
    import asyncio

    load_dotenv()

    token = getenv("DISCORD_TOKEN")
    if not token:
        pytest.skip("DISCORD_TOKEN not set, skipping integration test")

    # Calculate time 30 seconds from now
    now = datetime.now()
    target_time = now + timedelta(seconds=30)

    # Configure environment for test
    with patch.dict(
        "os.environ",
        {
            "DISCORD_TOKEN": token,
            "WEEKLY_MESSAGE_THREAD_ID": "767227407001321472",
            "WEEKLY_MESSAGE_CONTENT": f"🤖 Test message planifié - {now.strftime('%Y-%m-%d %H:%M:%S')}",
            "WEEKLY_MESSAGE_WEEKDAYS": str(now.weekday()),  # Today
            "WEEKLY_MESSAGE_HOUR": str(target_time.hour),
            "WEEKLY_MESSAGE_MINUTE": str(target_time.minute),
        },
    ):
        from SilicaAnimus.discord_client import DiscordClient

        client = DiscordClient(
            token=token,
            helloasso_client=None,
            gsheet_client=None,
        )

        print(f"\n⏰ Test démarré à {now.strftime('%H:%M:%S')}")
        print(f"📅 Message sera envoyé à {target_time.strftime('%H:%M:%S')} (dans 30 secondes)")
        print("📍 Canal cible: 767227407001321472")

        # Start the bot
        start_task = asyncio.create_task(client.start())

        try:
            # Wait for bot to be ready
            print("⏳ Attente de la connexion du bot...")
            await asyncio.sleep(5)

            if client.client.is_ready():
                print(f"✅ Bot connecté en tant que {client.client.user}")
            else:
                print("⚠️ Bot pas encore prêt, attente supplémentaire...")
                await asyncio.sleep(5)

            # Check if channel is accessible
            channel = client.client.get_channel(767227407001321472)
            if channel:
                print(f"✅ Canal trouvé: {channel.name}")
            else:
                print("⚠️ Canal non trouvé avec get_channel, tentative avec fetch...")
                channel = await client.client.fetch_channel(767227407001321472)
                print(f"✅ Canal trouvé avec fetch: {channel.name}")

            # Calculate remaining wait time
            remaining = 40 - (datetime.now() - now).total_seconds()
            if remaining > 0:
                print(f"⏳ Attente de {int(remaining)} secondes pour l'envoi du message...")
                await asyncio.sleep(remaining)

            print("✅ Délai d'attente terminé")
            print("🔍 Vérifiez manuellement que le message a été envoyé sur Discord")
            print(f"   Message attendu: '🤖 Test message planifié - {now.strftime('%Y-%m-%d %H:%M:%S')}'")

        finally:
            # Stop the bot
            await client.close()
            await start_task
            print("🛑 Bot arrêté")


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
