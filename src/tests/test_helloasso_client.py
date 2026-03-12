import pytest
import asyncio
from os import getenv
from dotenv import load_dotenv

from SilicaAnimus.helloasso_client import HelloAssoClient

pytest_plugins = ("pytest_asyncio",)

load_dotenv()


@pytest.mark.asyncio
async def test_helloasso_client_connection():
    """Test HelloAsso client connection and disconnection"""
    client = HelloAssoClient(
        client_id=getenv("HELLOASSO_CLIENT_ID"),
        client_secret=getenv("HELLOASSO_CLIENT_SECRET"),
    )
    future = asyncio.create_task(client.start())
    await asyncio.sleep(1)
    await client.close()
    await future


@pytest.mark.asyncio
async def test_helloasso_membership_check():
    """Test membership verification for individual members"""
    client = HelloAssoClient(
        client_id=getenv("HELLOASSO_CLIENT_ID"),
        client_secret=getenv("HELLOASSO_CLIENT_SECRET"),
    )
    future = asyncio.create_task(client.start())
    while not client.is_logged:
        await asyncio.sleep(1)

    # Test valid member
    result = await client.get_membership("Lucas", "MARTI")
    assert result is True, "Expected Lucas MARTI to be a member"

    # Test invalid member
    result = await client.get_membership("Luas", "MARTI")
    assert result is False, "Expected Luas MARTI to not be a member"

    # Test with quotes (should be normalized)
    result = await client.get_membership('"Lucas" ', '"MARTI" ')
    assert result is True, "Expected quoted name to be normalized and found"

    await client.close()
    await future


@pytest.mark.asyncio
async def test_helloasso_memberships_check():
    """Test batch membership verification"""
    client = HelloAssoClient(
        client_id=getenv("HELLOASSO_CLIENT_ID"),
        client_secret=getenv("HELLOASSO_CLIENT_SECRET"),
    )
    future = asyncio.create_task(client.start())
    while not client.is_logged:
        await asyncio.sleep(1)

    result = await client.get_memberships(
        [("Lucas", "MARTI"), ("Luas", "MARTI"), ('"Lucas" ', '"MARTI" ')]
    )

    assert isinstance(result, list), "Expected result to be a list"
    # Should return valid members only
    assert ("Lucas", "MARTI") in result or ('"Lucas" ', '"MARTI" ') in result

    await client.close()
    await future
