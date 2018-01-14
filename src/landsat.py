import re
import os
import zipfile
import tarfile
from pathlib import Path
from collections import namedtuple


class LandsatArchive(object):
    L8 = [(1, 'costal'), (2, 'blue'), (3, 'green'), (4, 'red'),
          (5, 'nir'), (6, 'swir1'), (7, 'swir2'), (8, 'panchromatic'),
          (9, 'cirrus'), (10, 'tirs1'), (11, 'tirs2'), ('BAND_QUALITY', 'bq'), ]
    LANDSAT_BANDS = {'LANDSAT_1_MSS': '',
                     'LANDSAT_2_MSS': '',
                     'LANDSAT_3_MSS': '',
                     'LANDSAT_4_MSS': '',
                     'LANDSAT_5_MSS': '',
                     'LANDSAT_4_TM': '',
                     'LANDSAT_5_TM': '',
                     'LANDSAT_7_ETM': '',
                     'LANDSAT_8_OLI_TIRS': dict.fromkeys(L8),
                     'GENERIC': {}, }

    def __init__(self, path, name='Landsat Archive', ex_path=None):
        self.__path = Path(path)
        self.__description = None
        self.__metadata = None
        self.__bands = None
        self.name = name

        if self.__path.is_file() and self.__path.suffix in ['.gz', '.zip', 'bz2']:
            ex = str(self.__path.parent / self.__path.stem.split('.')[0]) if ex_path is None else ex_path
            self.__path = self._decompress(ex)
            self._init_archive()

        elif self.__path.is_dir():
            self._init_archive()

        else:
            raise ValueError('{} is not a valid Landsat archive'.format(str(self.__path)))

    @property
    def path(self):
        return str(self.__path)

    @property
    def metadata(self):
        return self.__metadata

    @property
    def description(self):
        if self.__description is None:
            self._set_description()

        return self.__description

    def _set_description(self):
        if self.metadata is None:
            archive = 'GENERIC LANDSAT ARCHIVE'

        else:
            attrs = [('product_metadata', 'spacecraft_id'), ('product_metadata', 'sensor_id'),
                     ('product_metadata', 'date_aquired'), ('image_attributes', 'cloud_cover'),
                     ('image_attributes', 'image_quality'), ]

            values = [self.metadata.get(group, value)
                      for group, value in attrs]

            archive = '{0.0}_{0.1}_{0.2}_{0.3}_{0.3}'.format(values)

        # TODO append object info like number of bands etc.

        self.__description = archive

    def _init_archive(self):
        # init from metadata file
        # if no metadata file init from folder content and push to generic
        pass

    def _decompress(self, extract_path):
        if tarfile.is_tarfile(self.path):
            opener = tarfile.TarFile
            mode = 'r:gz' if self.__path.suffix == '.gz' else 'r:bz2'

        elif zipfile.is_zipfile(self.path):
            opener, mode = zipfile.ZipFile, 'r'

        else:
            raise ValueError('Unknown archive type "{}"'.format(self.__path.suffix))

        with opener.open(self.path, mode) as src:
            src.extractall(extract_path)

        return Path(extract_path)

    def __repr__(self):
        return '{}({}, {})'.format(self.__class__.__name__, self.__path, self.name)


class LandsatMetadata(object):
    def __init__(self, metadata_path):
        self.__path = Path(metadata_path)
        self.__groups = None

        if not self.__path.is_file():
            raise ValueError('{} is not a valid file'.format(str(self.__path)))

        self._init_attributes()

    @property
    def groups(self):
        if self.__groups is None:
            self.__groups = self._set_groups()

        return self.__groups

    def _set_groups(self):
        return {key: value
                for key, value in self.__dict__.items()
                if value is not self.__path}

    def _init_attributes(self):
        metadata = self.__class__.read_metadata(self.__path)

        for item in metadata:
            self.__setattr__(item.GROUP, item)

    def get(self, group, value, default=None):
        try:
            return self.__getattribute__(group.upper()).__getattribute__(value.upper())
        except AttributeError:
            return default

    def __str__(self):
        return self.__repr__() + '\nMetadata attr: {}'.format(self.groups)

    def __repr__(self):
        return '{}({})'.format(self.__class__.__name__, self.__path)

    @staticmethod
    def read_metadata(path):
        with open(str(path), 'r') as src:
            content = src.readlines()
            scan = __class__.scanner(content)
            lex = __class__.lexer(scan)
            metadata = __class__.parser(lex)

        return metadata

    @staticmethod
    def scanner(content):
        for line in content:
            yield line.strip()

    @staticmethod
    def lexer(scanner):
        start_group = re.compile(r'GROUP\s=\s.+')
        end_group = re.compile(r'END_GROUP\s=\s.+')
        eof = re.compile(r'END')

        groups = []
        for line in scanner:
            if bool(start_group.match(line)):
                current = [line]
                groups.append(current)

            elif bool(end_group.match(line)):
                yield groups.pop()

            elif bool(eof.match(line)):
                yield groups

            else:
                groups[-1].append(line)

    @staticmethod
    def parser(lexer):
        regex = re.compile(r'(?P<key>.+)\s=\s(?P<value>.+)')

        metadata = []
        for group in lexer:
            keys = []
            values = []

            for item in group:
                key, value = regex.match(item).groups()
                value = __class__.cast_to_best(value)
                keys.append(key)
                values.append(value)

            if len(keys) == len(values) and len(keys) > 1:
                Metadata = namedtuple('Metadata', keys)
                obj = Metadata(*values)
                metadata.append(obj)

        return metadata

    @staticmethod
    def cast_to_best(value):
        try:
            return int(value)

        except ValueError:
            try:
                return float(value)

            except ValueError:
                return '{}'.format(value.strip('"'))


if __name__ == '__main__':
    pass
