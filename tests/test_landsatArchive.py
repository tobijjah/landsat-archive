import unittest
from tests.stubs import L1, L4, L7, L8, OpenStub, FileMock
from landsat.utils import LandsatArchive, LandsatMetadata, BAND_MAP


class TestLandsatArchive(unittest.TestCase):
    def setUp(self):
        self.meta_file = L8

        # prepare mock objects
        file_mock = FileMock(self.meta_file['data'])
        open_stub = OpenStub(file_mock)
        opener = open_stub.open

        # inject open stub
        LandsatMetadata._OPENER = opener

        self.meta = LandsatMetadata('foo')
        self.meta.parse()

    def test_directory_open(self):
        pass

    def test_metadata_read(self):
        pass

    def test_archive_read(self):
        pass

    def test_metadata_sniffer(self):
        vals = ['foo', 'bar', 'foo/bar/landsat_mtl.txt']

        self.assertEqual('landsat_mtl.txt', LandsatArchive.metadata_sniffer(vals, r'.+_mtl.txt'))

    def test_metadata_sniffer_raises(self):
        pass

    def test_load(self):
        pass

    def test_dispatch_mapping(self):
        expected = BAND_MAP[self.meta_file['id']]
        result = LandsatArchive.dispatch_mapping(self.meta, BAND_MAP)

        self.assertEqual(expected, result)

    def test_dispatch_mapping_raises(self):
        pass
