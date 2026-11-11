import asyncio
import logging
import os

import pandas as pd
from discord import Client, Forbidden, Intents
from dotenv import load_dotenv

load_dotenv()
logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)

FORUM_EVENEMENTS_ID = 1100474380405981247
DEBRIEF_THREAD_ID = 1565691165951529002
OUTPUT_CSV = "halloween_2026_messages.csv"


class MissingEnvironmentVariableError(Exception):
    pass


async def main() -> None:
    logger.info("Starting script")
    discord_token = os.getenv("DISCORD_TOKEN")
    if discord_token is None:
        logger.error("Environment variable DISCORD_TOKEN not found")
        raise MissingEnvironmentVariableError(
            "Environment variable DISCORD_TOKEN not found"
        )

    guild_id = os.getenv("THALOS_GUILD_ID")
    if guild_id is None:
        logger.error("Environment variable THALOS_GUILD_ID not found")
        raise MissingEnvironmentVariableError(
            "Environment variable THALOS_GUILD_ID not found"
        )

    client = Client(intents=Intents.default())
    rows = []

    async with client:
        asyncio.create_task(client.start(discord_token))
        await client.wait_until_ready()

        thalos_guild = client.get_guild(int(guild_id))
        if thalos_guild is None:
            logger.error("Guild %s not found", guild_id)
            return

        try:
            forum_evenements = thalos_guild.get_channel(
                FORUM_EVENEMENTS_ID
            ) or await client.fetch_channel(FORUM_EVENEMENTS_ID)

            halloween_tag = None
            for tag in forum_evenements.available_tags:
                if tag.name == "Halloween 2026":
                    halloween_tag = tag
                    break

            for thread in forum_evenements.threads:
                if halloween_tag not in thread.applied_tags:
                    continue

                async for message in thread.history(limit=None, oldest_first=True):
                    rows.append(
                        {
                            "thread": thread.name,
                            "author": str(message.author),
                            "created_at": message.created_at,
                        }
                    )

        except Forbidden:
            logger.error(
                "Bot lacks permission to view forum channel %s "
                "(check 'View Channel' / 'Read Message History' overwrites)",
                FORUM_EVENEMENTS_ID,
            )
            return

    messages_df = pd.DataFrame(rows)
    messages_df.to_csv(OUTPUT_CSV, index=False)
    logger.info("Exported %d messages to %s", len(messages_df), OUTPUT_CSV)


if __name__ == "__main__":
    asyncio.run(main())
