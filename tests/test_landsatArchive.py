import unittest
from pathlib import Path
from zipfile import ZipFile
from tarfile import TarFile
from src.landsat import LandsatArchive


class TestLandsatArchive(unittest.TestCase):
    # TODO mock required
    def test_factory(self):
        _tar = LandsatArchive.factory(Path('foo.tar.gz'))
        _zip = LandsatArchive.factory(Path('foo.zip'))

        self.assertTrue(isinstance(_tar, TarFile))
        self.assertTrue(isinstance(_zip, ZipFile))
