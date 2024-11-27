from os import getenv
from dotenv import load_dotenv
import pytest
import asyncio
import logging
import sys

from SilicaAnimus.google_sheets_client import GoogleSheetsClient, MemberInfo

pytest_plugins = ("pytest_asyncio",)


def setup_function(function):
    load_dotenv()
    logging.basicConfig(stream=sys.stdout, level=logging.DEBUG)


@pytest.mark.asyncio
async def test_google_sheets_client_connection() -> bool:
    client = GoogleSheetsClient(getenv("GOOGLE_SERVICE_ACCOUNT_SECRETS_PATH"))
    print(client)


@pytest.mark.asyncio
async def test_google_sheets_get_spreadsheet() -> bool:
    client = GoogleSheetsClient(getenv("GOOGLE_SERVICE_ACCOUNT_SECRETS_PATH"))
    print(await client.get_spreadsheet())


@pytest.mark.asyncio
async def test_google_sheets_get_member_by_name() -> bool:
    client = GoogleSheetsClient(getenv("GOOGLE_SERVICE_ACCOUNT_SECRETS_PATH"))
    print(await client.get_member_by_name(first_name="titi", last_name="tata"))


@pytest.mark.asyncio
async def test_google_sheets_get_members_by_discord_name() -> bool:
    client = GoogleSheetsClient(getenv("GOOGLE_SERVICE_ACCOUNT_SECRETS_PATH"))
    print(await client.get_members_by_discord_names([".endya", "lucasthepatator", "jeanpierrepernaud"]))


@pytest.mark.asyncio
async def test_google_sheets_add_member() -> bool:
    client = GoogleSheetsClient(getenv("GOOGLE_SERVICE_ACCOUNT_SECRETS_PATH"))
    member_info = MemberInfo("titi", "tata", "tata123", False, True, False)
    print(await client.add_member(member_info))
    member_info = MemberInfo("tutu", "tata", "qsdsqd", False, False, True)
    print(await client.add_member(member_info))


@pytest.mark.asyncio
async def test_google_sheets_add_members() -> bool:
    client = GoogleSheetsClient(getenv("GOOGLE_SERVICE_ACCOUNT_SECRETS_PATH"))
    members_info = [
        MemberInfo("titi", "tata", "tata123", False, False, True),
        MemberInfo("tutu", "toto", "totolebg", False, False, True),
    ]
    print(await client.add_members(members_info))


if __name__ == "__main__":
    setup_function(test_google_sheets_client_connection)
    asyncio.run(test_google_sheets_client_connection())
    asyncio.run(test_google_sheets_get_spreadsheet())
    asyncio.run(test_google_sheets_get_member_by_name())
    asyncio.run(test_google_sheets_get_members_by_discord_name())
    asyncio.run(test_google_sheets_add_member())
    asyncio.run(test_google_sheets_add_members())
