import os
from pathlib import Path
from unittest import TestCase
from src.landsat import LandsatMetadata


RES = Path(os.getcwd()) / 'res'


class TestLandsatMetadata(TestCase):
    # TODO test _asdict, parse, scanner, init

    def test_get_with_valid_attributes(self):
        meta = LandsatMetadata(RES / 'ls8_mtl.txt')
        meta.parse()

        self.assertTrue(isinstance(meta.get('PRODUCT_METADATA'), tuple))
        self.assertTrue(meta.get('pROduct_metaDATA', 'spacecraft_id') == 'LANDSAT_8')

    def test_get_with_invalid_attributes(self):
        meta = LandsatMetadata(RES / 'ls8_mtl.txt')
        meta.parse()

        self.assertTrue(meta.get('FOO', 'BAR') is None)

    def test_iter_group_with_valid_attribute(self):
        meta = LandsatMetadata(RES / 'ls8_mtl.txt')
        meta.parse()
        result = list(meta.iter_group('PRODUCT_METADATA'))

        self.assertTrue(len(result) == 54)

    def test_iter_group_with_invalid_attribute(self):
        meta = LandsatMetadata(RES / 'ls8_mtl.txt')
        meta.parse()
        result = list(meta.iter_group('foo'))

        self.assertTrue(result == [])

    def test_lexer_with_valid_metadata(self):
        # mock of valid metadata content
        mock_gen = ['GROUP = T1', 'ATTR1 = 1', 'END_GROUP = T1', 'GROUP = T2', 'ATTR1 = 1', 'END_GROUP = T2']
        result = list(LandsatMetadata.lexer(mock_gen))

        self.assertTrue(len(result) == 2)

    def test_lexer_with_malicious_metadata(self):
        # mock of valid metadata content
        mock_gen = ['GROUP = T1', 'ATTR1 = 1', 'END_GROUP = T1', 'GROUP = T2', 'ATTR1 = 1',
                    'GROUP = T3', 'ATTR1 = 1', 'END_GROUP = T3']
        result = list(LandsatMetadata.lexer(mock_gen))

        self.assertTrue(len(result) == 3)

    def test_parser_returns_expected_on_valid_metadata(self):
        # mock of a valid metadata group
        mock_gen = [['GROUP = TEST1', 'ATTR1 = 1', 'ATTR2 = 2.0', 'ATTR3 = "A TEST"']]
        fields = ('GROUP', 'ATTR1', 'ATTR2', 'ATTR3')

        result = LandsatMetadata.parser(mock_gen)
        for item in result:
            self.assertTrue(item, tuple)
            self.assertEqual(item._fields, fields)

    def test_parser_fails_on_invalid_metadata(self):
        # mock of a invalid metadata group
        mock_gen = [['GROUP = TEST1'], ['FOO', 'BAR'], []]

        with self.assertRaises(AssertionError):
            LandsatMetadata.parser(mock_gen)

    def test_cast_to_best(self):
        int_typ = LandsatMetadata.cast_to_best('1')
        flt_typ = LandsatMetadata.cast_to_best('1.0')
        str_typ = LandsatMetadata.cast_to_best('aaa')

        self.assertTrue(isinstance(int_typ, int))
        self.assertTrue(isinstance(flt_typ, float))
        self.assertTrue(isinstance(str_typ, str))
