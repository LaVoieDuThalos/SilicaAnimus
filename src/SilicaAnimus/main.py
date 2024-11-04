import logging
import sys
import typer

from SilicaAnimus import SilicaAnimus

def main(discord_token: str) -> None:
        logging.basicConfig(stream=sys.stdout, level=logging.DEBUG)

        silica_animus = SilicaAnimus(discord_token=discord_token)
        silica_animus.run()

if __name__ == "__main__":
    typer.run(main)
