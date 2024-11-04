import logging
import sys
from SilicaAnimus import SilicaAnimus

if __name__ == "__main__":

    logging.basicConfig(stream=sys.stdout, level=logging.DEBUG)

    silica_animus = SilicaAnimus()
    silica_animus.run()