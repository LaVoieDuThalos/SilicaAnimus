from dotenv import load_dotenv
import logging
import sys

from SilicaAnimus import utils


def setup_function(function):
    load_dotenv()
    logging.basicConfig(stream=sys.stdout, level=logging.DEBUG)


def test_normalize_name() -> bool:
    assert utils.normalize_name("test") == "test"
    assert utils.normalize_name("tést") == "test"
    assert utils.normalize_name("tèst") == "test"
    assert utils.normalize_name("têst") == "test"
    assert utils.normalize_name("Test") == "test"
    assert utils.normalize_name("tàst") == "tast"
    assert utils.normalize_name("tæst") == "taest"
    assert utils.normalize_name("'test'") == "test"


if __name__ == "__main__":
    test_normalize_name()
