from os import getenv
from dotenv import load_dotenv
import pytest
import asyncio
import logging
import sys

from SilicaAnimus.helloasso_client import HelloAssoClient

pytest_plugins = ('pytest_asyncio',)

def setup_function(function):
    load_dotenv()
    logging.basicConfig(stream=sys.stdout, level=logging.DEBUG)

@pytest.mark.asyncio
async def test_helloasso_client_connection() -> bool:
    client = HelloAssoClient(client_id=getenv("HELLOASSO_CLIENT_ID"), client_secret=getenv("HELLOASSO_CLIENT_SECRET"))
    future = asyncio.create_task(client.start())
    await asyncio.sleep(1)
    await client.close()
    await future
    return True

if __name__ == "__main__":
    setup_function(test_helloasso_client_connection)
    asyncio.run(test_helloasso_client_connection())
