from unittest import TestCase
from landsat.utils import LandsatMetadata
from tests.stubs import L1, L4, L7, L8, OpenStub, FileMock
from landsat.utils import MetadataFileParsingError


class TestLandsatMetadata(TestCase):
    # TODO test _asdict, parse, scanner, init, read
    # TODO del hard coded test attributes
    def setUp(self):
        self.meta_file = L7

        # prepare mock objects
        file_mock = FileMock(self.meta_file['data'])
        open_stub = OpenStub(file_mock)
        opener = open_stub.open

        # inject open stub
        LandsatMetadata._OPENER = opener

        self.meta = LandsatMetadata('foo')
        self.meta.parse()

    def test_delete_attributes(self):
        self.assertTrue(len(self.meta._asdict()) > 0)

        self.meta._delete_attributes()

        self.assertTrue(len(self.meta._asdict()) == 0)

    def test_get_with_valid_attributes(self):
        self.assertTrue(isinstance(self.meta.get('PRODUCT_METADATA'), tuple))
        self.assertTrue(self.meta.get('pROduct_metaDATA', 'spacecraft_id') == self.meta_file['spacecraft'])

    def test_get_with_invalid_attributes(self):
        self.assertTrue(self.meta.get('foo', 'bar') is None)

    def test_iter_group_with_valid_attribute(self):
        result = list(self.meta.iter_group('product_metadata'))

        self.assertTrue(len(result) == self.meta_file['product_len'])

    def test_iter_group_with_invalid_attribute(self):
        result = list(self.meta.iter_group('foo'))

        self.assertTrue(result == [])

    def test_lexer_with_valid_metadata(self):
        result = list(LandsatMetadata.lexer(self.meta_file['data']))

        self.assertTrue(len(result) == self.meta_file['groups'])

    def test_lexer_with_malicious_metadata(self):
        mock_gen = ['GROUP = T1', 'ATTR1 = 1', 'END_GROUP = T1', 'GROUP = T2', 'ATTR1 = 1',
                    'GROUP = T3', 'ATTR1 = 1', 'END_GROUP = T3']
        result = list(LandsatMetadata.lexer(mock_gen))

        self.assertTrue(len(result) == 3)

    def test_parser_returns_expected_on_valid_metadata(self):
        mock_gen = [['GROUP = TEST1', 'ATTR1 = 1', 'ATTR2 = 2.0', 'ATTR3 = "A TEST"']]
        fields = ('GROUP', 'ATTR1', 'ATTR2', 'ATTR3')

        result = LandsatMetadata.parser(mock_gen)
        for item in result:
            self.assertTrue(item, tuple)
            self.assertEqual(fields, item._fields)

    def test_parser_fails_on_invalid_metadata(self):
        mock_gen = [['GROUP = TEST1'], ['FOO', 'BAR'], []]

        with self.assertRaises(MetadataFileParsingError):
            LandsatMetadata.parser(mock_gen)

    def test_cast_to_best(self):
        int_typ = LandsatMetadata.cast_to_best('1')
        flt_typ = LandsatMetadata.cast_to_best('1.0')
        str_typ = LandsatMetadata.cast_to_best('aaa')

        self.assertTrue(isinstance(int_typ, int))
        self.assertTrue(isinstance(flt_typ, float))
        self.assertTrue(isinstance(str_typ, str))
