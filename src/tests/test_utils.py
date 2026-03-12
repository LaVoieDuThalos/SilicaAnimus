from SilicaAnimus import utils


class TestUtils:
    """Test suite for utility functions"""

    def test_normalize_name_basic(self):
        """Test basic normalization"""
        assert utils.normalize_name("test") == "test"

    def test_normalize_name_accents(self):
        """Test accent removal"""
        assert utils.normalize_name("tést") == "test"
        assert utils.normalize_name("tèst") == "test"
        assert utils.normalize_name("têst") == "test"
        assert utils.normalize_name("tàst") == "tast"

    def test_normalize_name_case(self):
        """Test case conversion"""
        assert utils.normalize_name("Test") == "test"
        assert utils.normalize_name("TEST") == "test"

    def test_normalize_name_special_chars(self):
        """Test special character handling"""
        assert utils.normalize_name("tæst") == "taest"
        assert utils.normalize_name("'test'") == "test"
        assert utils.normalize_name('"test"') == "test"
        assert utils.normalize_name(" test ") == "test"
