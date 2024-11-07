import logging 
from urllib import request, parse
from os import getenv

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

    async def start(self):
        """Starts the client
        """
        self.logger.info("Running...")

        token_request_data = parse.urlencode({"client_id": self.client_id,
                                              "client_secret": self.client_secret,
                                              "grant_type": "client_credentials"})
        token_request_data = token_request_data.encode()
        token_request = request.Request(url=getenv("HELLOASSO_TOKEN_URL"), data=token_request_data, method='POST')
        token_request.add_header('Content-Type', 'application/x-www-form-urlencoded')
        self.logger.info("Getting token")
        with request.urlopen(token_request) as resp:
            print(resp)
            pass

        return

    async def close(self):      
        """Stops the client
        """
        pass

        return


        