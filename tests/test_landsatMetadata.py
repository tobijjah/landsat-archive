from unittest import TestCase
from src.landsat import LandsatMetadata


class TestLandsatMetadata(TestCase):
    def test__init_attributes(self):
        self.fail()

    def test__get_metadata_attributes(self):
        self.fail()

    def test_read_metadata(self):
        self.fail()

    def test_scanner(self):
        self.fail()

    def test_lexer(self):
        self.fail()

    def test_parser(self):
        self.fail()

    def test_cast_to_best(self):
        int_typ = LandsatMetadata.cast_to_best('1')
        flt_typ = LandsatMetadata.cast_to_best('1.0')
        str_typ = LandsatMetadata.cast_to_best('aaa')

        self.assertTrue(isinstance(int_typ, int))
        self.assertTrue(isinstance(flt_typ, float))
        self.assertTrue(isinstance(str_typ, str))
