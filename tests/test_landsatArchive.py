import unittest
from pathlib import Path
from zipfile import ZipFile
from tarfile import TarFile
from src.landsat import LandsatArchive


class TestLandsatArchive(unittest.TestCase):
    @unittest.skip('mock required')
    def test_factory(self):
        _tar = LandsatArchive.factory(Path('foo.tar.gz'))
        _zip = LandsatArchive.factory(Path('foo.zip'))

        self.assertTrue(isinstance(_tar, TarFile))
        self.assertTrue(isinstance(_zip, ZipFile))

    def test_metadata_sniffer(self):
        vals = ['foo', 'bar', 'foo/bar/landsat_mtl.txt']

        self.assertEqual('landsat_mtl.txt', LandsatArchive.metadata_sniffer(vals))

