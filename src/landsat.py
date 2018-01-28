import re
import os
from pathlib import Path
from zipfile import ZipFile, is_zipfile
from tarfile import TarFile, is_tarfile
from collections import namedtuple, OrderedDict
from contextlib import contextmanager


BAND_MAP = {
    'LANDSAT_4_TM': ''.split(),
    'LANDSAT_7_ETM': ''.split(),
    'LANDSAT_8_OLI_TIRS': ''.split(),
}


class LandsatError(Exception):
    """Base exception"""


class UnsupportedSourceError(LandsatError):
    """Exception for unsupported sources"""


class MetadataFileError(LandsatError):
    """Exception for Landsat metadata files"""


class MetadataFileParsingError(LandsatError):
    """Exception for errors occurring during metadata file parsing"""


class TarFileWrapper(TarFile):
    """Delegate a namelist call to TarFile.getnames. Required for convenient duck typing
    between ZipFile and TarFile"""
    def namelist(self):
        return self.getnames()


class LandsatArchive(object):
    def __init__(self, source, metadata_obj, alias, band_mapping):
        self.src = source
        self.alias = alias
        self.mapping = band_mapping
        self.metadata = metadata_obj

    @classmethod
    def open(cls, source, extract_to=None, alias=None, meta_template=r'.*_?MTL.txt', band_mapping=BAND_MAP):
        """

        :param source:
        :param extract_to:
        :param alias:
        :param meta_template:
        :param band_mapping:
        :return:
        """
        src = Path(source)

        if src.is_dir():
            return cls.directory_open(src, alias, meta_template, band_mapping)

        elif src.suffix == '.txt' and src.is_file():
            return cls.metadata_open(src, alias, band_mapping)

        elif is_zipfile(str(src)) or is_tarfile(str(src)):
            return cls.archive_open(src, extract_to, alias, meta_template, band_mapping)

        else:
            raise UnsupportedSourceError('%s is not supported' % source)

    @classmethod
    def directory_open(cls, directory, alias, meta_template, band_mapping):
        metadata_file = cls.metadata_sniffer(os.listdir(str(directory)), meta_template)
        metadata_obj = LandsatMetadata(directory / metadata_file)
        metadata_obj.parse()

        sensor = metadata_obj.get('PRODUCT_METADATA', 'SPACECRAFT_ID') + '_' + \
                 metadata_obj.get('PRODUCT_METADATA', 'SENSOR_ID')
        mapping = band_mapping[sensor]

        return cls(directory, metadata_obj, alias, mapping)

    @classmethod
    def metadata_open(cls, metadata, alias, band_mapping):
        metadata_obj = LandsatMetadata(metadata)
        metadata_obj.parse()

        sensor = metadata_obj.get('PRODUCT_METADATA', 'SPACECRAFT_ID') + '_' + \
                 metadata_obj.get('PRODUCT_METADATA', 'SENSOR_ID')
        mapping = band_mapping[sensor]

        path = metadata.parent

        return cls(path, metadata_obj, alias, mapping)

    @classmethod
    def archive_open(cls, archive, extract_to, alias, meta_template, band_mapping):
        if extract_to is None:
            ex = archive.parent / archive.name.split('.')[0]

        else:
            ex = Path(extract_to)

        with __class__.archive_opener(str(archive)) as src:
            metadata_file = cls.metadata_sniffer(src.namelist(), meta_template)
            src.extractall(str(ex))

        metadata_obj = LandsatMetadata(ex / metadata_file)
        metadata_obj.parse()

        sensor = metadata_obj.get('PRODUCT_METADATA', 'SPACECRAFT_ID') + '_' + \
                 metadata_obj.get('PRODUCT_METADATA', 'SENSOR_ID')
        mapping = band_mapping[sensor]

        return cls(ex, metadata_obj, alias, mapping)

    def load(self):
        for k, v in self.metadata.iter_group('PRODUCT_METADATA'):
            pass

    def __repr__(self):
        return '{}({}, {}, {}, {})'.format(__class__.__name__, self.src, self.metadata, self.alias, self.mapping)

    @staticmethod
    def metadata_sniffer(names, template):
        regex = re.compile(template)

        for name in names:
            name = os.path.basename(name)

            if bool(regex.match(name)):
                return name

        raise MetadataFileError('Missing Landsat metadata file in %s' % names)

    @staticmethod
    @contextmanager
    def archive_opener(archive, mode='r'):
        try:
            if is_tarfile(archive):
                opener = TarFileWrapper.open(archive, mode=mode)
                yield opener

            elif is_zipfile(archive):
                opener = ZipFile(archive, mode=mode)
                yield opener

            else:
                raise UnsupportedSourceError('Unsupported archive file %s' % archive)

        # TODO meaningful error message
        except:
            pass

        finally:
            opener.close()


class LandsatMetadata(object):
    # hook for testing
    _OPENER = open

    def __init__(self, path):
        self.path = Path(path)

    def _asdict(self):
        return OrderedDict([(k, v._asdict())
                            for k, v in self.__dict__.items()
                            if v is not self.path])

    def _delete_attributes(self):
        for attr in self._asdict():
            delattr(self, attr)

    def parse(self):
        metadata = self.__class__.read(str(self.path))

        for item in metadata:
            self.__setattr__(item.GROUP, item)

    def get(self, group, value=None, default=None):
        try:
            attr = self.__getattribute__(group.upper())

            if value is None:
                return attr

            else:
                return attr.__getattribute__(value.upper())

        except AttributeError:
            return default

    def iter_group(self, group):
        attr = self.get(group)

        if attr is None:
            return

        yield from attr._asdict().items()

    # TODO return meaningful string currently it is a mess
    def __str__(self):
        return self.__repr__() + '\nMetadata attr: {}'.format(self._asdict())

    def __repr__(self):
        return '{}({})'.format(self.__class__.__name__, self.path)

    @staticmethod
    def read(path):
        with __class__._OPENER(path, 'r') as src:
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

        groups = []
        for line in scanner:
            if bool(start_group.match(line)):
                current = [line]
                groups.append(current)

            elif bool(end_group.match(line)):
                yield groups.pop()

            else:
                if groups:
                    groups[-1].append(line)
                else:
                    groups.append([line])

        yield from groups

    @staticmethod
    def parser(lexer):
        regex = re.compile(r'(?P<key>.+)\s=\s(?P<value>.+)')

        metadata = []
        for group in lexer:
            keys = []
            values = []

            for item in group:
                # skip item if not properly formatted
                try:
                    key, value = regex.match(item).groups()
                except AttributeError:
                    continue

                value = __class__.cast_to_best(value)
                keys.append(key)
                values.append(value)

            # TODO accept without GROUP key and create a generic group key
            if len(keys) == len(values) and len(keys) > 1 and 'GROUP' in keys:
                Metadata = namedtuple('Metadata', keys)
                obj = Metadata(*values)
                metadata.append(obj)

        if len(metadata) == 0:
            raise MetadataFileParsingError('It appears that this metadata file does not contain any metadata')

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
