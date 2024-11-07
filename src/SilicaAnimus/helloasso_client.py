import logging 
from urllib import request, parse
from os import getenv
from http.client import HTTPResponse

class HelloAssoClient:
    def __init__(self, client_id: str, client_secret: str):
        """_summary_

        Args:
            client_id (str): HelloAsso API association OAuth2 client_id
            client_secret (str): HelloAsso API association OAuth2 client_secret
        """
        self.logger = logging.getLogger(__name__)
        self.client_id = client_id
        self.client_secret = client_secret
        self.refresh_token = None

    @staticmethod
    def get_basic_headers():
        headers = {
            'User-Agent': 'Mozilla/5.0 (compatible; Discordbot/2.0; +https://discordapp.com/)'
        }
        return headers

    async def get_access_token(self) -> bool:
        token_request_data = parse.urlencode({"client_id": self.client_id,
                                              "client_secret": self.client_secret,
                                              "grant_type": "client_credentials"})
        token_request_data = token_request_data.encode()
        token_request = request.Request(url=getenv("HELLOASSO_TOKEN_URL"), data=token_request_data, headers=HelloAssoClient.get_basic_headers(), method='POST')
        token_request.add_header('Content-Type', 'application/x-www-form-urlencoded')

        self.logger.info("Getting token")
        resp: HTTPResponse
        with request.urlopen(token_request) as resp :
            if resp.status != 200:
                self.logger.info(f"Could not get token {resp.getcode()}")

        return True

    async def start(self) -> bool:
        """Starts the client
        """
        self.logger.info("Running...")
        await self.get_access_token()   

        return

    async def close(self):      
        """Stops the client
        """
        pass

        return


        