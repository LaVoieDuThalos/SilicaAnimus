import pytest
from os import getenv
from dotenv import load_dotenv

from SilicaAnimus.google_sheets_client import GoogleSheetsClient, MemberInfo

pytest_plugins = ("pytest_asyncio",)

load_dotenv()


@pytest.mark.asyncio
async def test_google_sheets_client_connection():
    """Test Google Sheets client initialization"""
    client = GoogleSheetsClient(getenv("GOOGLE_SERVICE_ACCOUNT_SECRETS_PATH"))
    assert client is not None


@pytest.mark.asyncio
async def test_google_sheets_get_spreadsheet():
    """Test fetching spreadsheet data"""
    client = GoogleSheetsClient(getenv("GOOGLE_SERVICE_ACCOUNT_SECRETS_PATH"))
    data = await client.get_spreadsheet()
    assert data is not None
    assert "values" in data or isinstance(data, dict)


@pytest.mark.asyncio
async def test_google_sheets_get_member_by_name():
    """Test fetching member by name"""
    client = GoogleSheetsClient(getenv("GOOGLE_SERVICE_ACCOUNT_SECRETS_PATH"))
    member = await client.get_member_by_name(first_name="titi", last_name="tata")
    assert isinstance(member, MemberInfo)


@pytest.mark.asyncio
async def test_google_sheets_get_members_by_discord_name():
    """Test fetching members by Discord usernames"""
    client = GoogleSheetsClient(getenv("GOOGLE_SERVICE_ACCOUNT_SECRETS_PATH"))
    members = await client.get_members_by_discord_names(
        [".endya", "lucasthepatator", "jeanpierrepernaud"]
    )
    assert isinstance(members, list)


@pytest.mark.asyncio
async def test_google_sheets_add_member():
    """Test adding a single member"""
    client = GoogleSheetsClient(getenv("GOOGLE_SERVICE_ACCOUNT_SECRETS_PATH"))
    member_info = MemberInfo("titi", "tata", "tata123", False, True, False)
    await client.add_member(member_info)
    # Test passes if no exception is raised

    member_info = MemberInfo("tutu", "tata", "qsdsqd", False, False, True)
    await client.add_member(member_info)
    # Test passes if no exception is raised


@pytest.mark.asyncio
async def test_google_sheets_add_members():
    """Test adding multiple members in batch"""
    client = GoogleSheetsClient(getenv("GOOGLE_SERVICE_ACCOUNT_SECRETS_PATH"))
    members_info = [
        MemberInfo("titi", "tata", "tata123", False, False, True),
        MemberInfo("tutu", "toto", "totolebg", False, False, True),
    ]
    await client.add_members(members_info)
    # Test passes if no exception is raised
