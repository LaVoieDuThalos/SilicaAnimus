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

        self.refresh_token_handle: asyncio.TimerHandle = None

        self.run = True

    @staticmethod
    def get_basic_headers() -> dict:
        """Utility function to define the basic headers for any HTTPS request

        Returns:
            dict: The headers dict
        """

        headers = {
            "User-Agent": "Mozilla/5.0 (compatible; Discordbot/2.0; +https://discordapp.com/)"
        }
        return headers

    async def get_access_token(self) -> bool:
        """Get the access token from the authentifaction endpoint

        Returns:
            bool: True if it managed to get the token
        """
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
                self.logger.warning(f"Could not get token {resp.getcode()}")

            resp_values = json.loads(resp.read())
            self.access_token = resp_values["access_token"]
            self.refresh_token = resp_values["refresh_token"]
            self.token_expiration_time = resp_values["expires_in"]

            self.refresh_token_handle = asyncio.get_event_loop().call_later(
                self.token_expiration_time - 60, self.refresh_access_token
            )

        self.logger.info("Token gotten succesfully")
        return True

    async def refresh_access_token(self) -> bool:
        """Refresh the token

        Returns:
            bool: True if it managed to refresh the token
        """

        self.logger.info("Refreshing token")
        token_request_data = parse.urlencode(
            {
                "refresh_token": self.refresh_token,
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

        resp: HTTPResponse
        with request.urlopen(token_request) as resp:
            if resp.status != 200:
                self.logger.warning(f"Could not get token {resp.getcode()}")

            resp_values = json.loads(resp.read())
            self.access_token = resp_values["access_token"]
            self.refresh_token = resp_values["refresh_token"]
            self.token_expiration_time = resp_values["expires_in"]

            self.refresh_token_handle = asyncio.get_event_loop().call_later(
                self.token_expiration_time - 60, self.refresh_access_token
            )

        self.logger.info("Access token refreshed")
        return True

    async def get_membership(self, first_name: str, last_name: str) -> bool:
        """Check if a person is a current member of the association

        Returns:
            bool: True if the person is a member
        """

        if self.access_token is None:
            self.logger.warning("No token for get_membership request")
            return False

        members_request_data = parse.urlencode(
            {
                "organizationSlug": getenv("HELLOASSO_ORGANIZATIONSLUG"),
                "formType": "membership",
                "formSlug": "qsdqd",
            }
        )

        members_request_data = members_request_data.encode()
        request_url = f"{getenv('HELLOASSO_API_URL')}/organizations/{getenv('HELLOASSO_ORGANIZATIONSLUG')}/forms/membership/qsdqd/orders"
        self.logger.debug(request_url)
        members_request = request.Request(
            url=request_url,
            data=members_request_data,
            headers=HelloAssoClient.get_basic_headers(),
            method="GET",
        )
        members_request.add_header("accept", "application/json")
        members_request.add_header("authorization", f"Bearer {self.access_token}")

        self.logger.info("Getting members")
        resp: HTTPResponse
        with request.urlopen(members_request) as resp:
            if resp.status != 200:
                self.logger.warning(f"Could not get members {resp.getcode()}")

            resp_data = json.loads(resp.read())
            for data in resp_data["data"]:
                payer = data["payer"]
                if (
                    first_name.lower() == payer["firstName"].lower()
                    and last_name.lower() == payer["lastName"].lower()
                ):
                    self.logger.info(f"{first_name} {last_name} is a member")
                    return True

            self.logger.info(f"{first_name} {last_name} is not a member")
            return False

        return False

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

    @property
    def is_logged(self):
        return self.access_token is not None
