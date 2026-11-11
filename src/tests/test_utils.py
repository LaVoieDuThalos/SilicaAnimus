from SilicaAnimus import scripts


class TestUtils:
    """Test suite for utility functions"""

    def test_normalize_name_basic(self):
        """Test basic normalization"""
        assert scripts.normalize_name("test") == "test"

    def test_normalize_name_accents(self):
        """Test accent removal"""
        assert scripts.normalize_name("tést") == "test"
        assert scripts.normalize_name("tèst") == "test"
        assert scripts.normalize_name("têst") == "test"
        assert scripts.normalize_name("tàst") == "tast"

    def test_normalize_name_case(self):
        """Test case conversion"""
        assert scripts.normalize_name("Test") == "test"
        assert scripts.normalize_name("TEST") == "test"

    def test_normalize_name_special_chars(self):
        """Test special character handling"""
        assert scripts.normalize_name("tæst") == "taest"
        assert scripts.normalize_name("'test'") == "test"
        assert scripts.normalize_name('"test"') == "test"
        assert scripts.normalize_name(" test ") == "test"
