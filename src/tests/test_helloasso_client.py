from os import getenv
from dotenv import load_dotenv
import pytest

from SilicaAnimus.helloasso_client import HelloAssoClient

pytest_plugins = ('pytest_asyncio',)

@pytest.mark.asyncio
async def test_helloasso_client_connection() -> bool:

    load_dotenv()
    client = HelloAssoClient(client_id=getenv("HELLOASSO_CLIENT_ID"), client_secret=getenv("HELLOASSO_CLIENT_SECRET"))
    await client.start()
    await client.close()

    return True
