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

    load_dotenv()
    client = HelloAssoClient(client_id=getenv("HELLOASSO_CLIENT_ID"), client_secret=getenv("HELLOASSO_CLIENT_SECRET"))
    future = client.start()
    print("a")
    await asyncio.sleep(1)
    print("b")
    await client.close()
    print("c")
    await future
    return True

if __name__ == "__main__":
    setup_function(test_helloasso_client_connection)
    asyncio.run(test_helloasso_client_connection())
