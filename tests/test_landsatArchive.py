import unittest
from landsat.utils import LandsatArchive


class TestLandsatArchive(unittest.TestCase):
    def test_directory_open(self):
        self.fail()

    def test_metadata_sniffer(self):
        vals = ['foo', 'bar', 'foo/bar/landsat_mtl.txt']

        self.assertEqual('landsat_mtl.txt', LandsatArchive.metadata_sniffer(vals, r'.+_mtl.txt'))

