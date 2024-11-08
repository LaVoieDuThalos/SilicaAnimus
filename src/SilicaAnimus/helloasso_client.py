import logging
from urllib import request, parse
from os import getenv
from http.client import HTTPResponse
import json
import asyncio


class HelloAssoClient:
    def __init__(self, client_id: str, client_secret: str):
        """_summary_

        Args:
            client_id (str): HelloAsso API association OAuth2 client_id
            client_secret (str): HelloAsso API association OAuth2 client_secret
        """
        self.logger: logging.Logger = logging.getLogger(__name__)
        self.client_id = client_id
        self.client_secret = client_secret

        # OAuth2 Credentials
        self.access_token = None
        self.refresh_token = None
        self.token_expiration_time = None

        self.refresh_token_handle = None

        self.run = True

    @staticmethod
    def get_basic_headers():
        headers = {
            "User-Agent": "Mozilla/5.0 (compatible; Discordbot/2.0; +https://discordapp.com/)"
        }
        return headers

    async def get_access_token(self) -> bool:
        token_request_data = parse.urlencode(
            {
                "client_id": self.client_id,
                "client_secret": self.client_secret,
                "grant_type": "client_credentials",
            }
        )
        token_request_data = token_request_data.encode()
        token_request = request.Request(
            url=getenv("HELLOASSO_TOKEN_URL"),
            data=token_request_data,
            headers=HelloAssoClient.get_basic_headers(),
            method="POST",
        )
        token_request.add_header("Content-Type", "application/x-www-form-urlencoded")

        self.logger.info("Getting token")
        resp: HTTPResponse
        with request.urlopen(token_request) as resp:
            if resp.status != 200:
                self.logger.info(f"Could not get token {resp.getcode()}")

            resp_values = json.loads(resp.read())
            self.access_token = resp_values["access_token"]
            self.refresh_token = resp_values["refresh_token"]
            self.token_expiration_time = resp_values["expires_in"]

            self.refresh_token_handle = asyncio.get_event_loop().call_later(
                self.token_expiration_time - 60, self.get_access_token
            )

        return True

    async def refresh_token(self) -> bool:
        token_request_data = parse.urlencode(
            {
                "client_id": self.client_id,
                "client_secret": self.refresh_token,
                "grant_type": "refresh_token",
            }
        )

        token_request_data = token_request_data.encode()
        token_request = request.Request(
            url=getenv("HELLOASSO_TOKEN_URL"),
            data=token_request_data,
            headers=HelloAssoClient.get_basic_headers(),
            method="POST",
        )
        token_request.add_header("Content-Type", "application/x-www-form-urlencoded")

        self.logger.info("Refreshing token")
        resp: HTTPResponse
        with request.urlopen(token_request) as resp:
            if resp.status != 200:
                self.logger.info(f"Could not get token {resp.getcode()}")

            resp_values = json.loads(resp.read())
            self.access_token = resp_values["access_token"]
            self.refresh_token = resp_values["refresh_token"]
            self.token_expiration_time = resp_values["expires_in"]

            self.refresh_token_handle = asyncio.get_event_loop().call_later(
                self.token_expiration_time - 60, self.get_access_token
            )

        return True

    async def start(self) -> bool:
        """Starts the client"""
        self.logger.info("Running...")
        self.run = True
        await self.get_access_token()

        while self.run:
            await asyncio.sleep(1)

        if self.refresh_token is not None:
            self.refresh_token_handle.cancel()

    async def close(self):
        """Stops the client"""

        self.run = False
        return
