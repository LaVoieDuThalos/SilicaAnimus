import logging 

class HelloAssoClient:
    def __init__(self, token: str):
        self.logger = logging.getLogger(__name__)
        
    async def start(self):
        self.logger.info("Running...")
        