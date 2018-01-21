import re
import os
import zipfile
import tarfile
from pathlib import Path
from collections import namedtuple, OrderedDict


class LandsatArchive(object):
    def __init__(self, path=None, extract_path=None, alias='DEFAULT'):
        self.alias = alias
        self.extract = extract_path

        self._is_archive = False
        self._path = None
        self.path = path

        self._description = None
        self._metadata = None
        self._bands = None

    @property
    def path(self):
        return self._path

    @path.setter
    def path(self, value):
        path = Path(value)
        self._is_archive = False

        if path.is_file() and path.suffix in ['.gz', '.zip', 'bz2']:
            self._is_archive = True

        elif path.is_file() and path.suffix in ['.txt']:
            self._metadata = LandsatMetadata(path)
            path = path.parent

        elif path.is_dir():
            meta_path = self._metadata_sniffer(path)
            self._metadata = LandsatMetadata(meta_path)

        else:
            raise ValueError('{} is not a valid Landsat archive'.format(str(path)))

        self._path = path

    def load(self):
            if self._is_archive:
                self.path = self._decompress()

    def _decompress(self):
        ex = str(self.path.parent / self.path.stem.split('.')[0]) if self.extract is None else self.extract

        if tarfile.is_tarfile(self.path):
            opener = tarfile.TarFile
            mode = 'r:gz' if self.path.suffix == '.gz' else 'r:bz2'

        elif zipfile.is_zipfile(self.path):
            opener, mode = zipfile.ZipFile, 'r'

        else:
            raise ValueError('Unknown archive type "{}"'.format(self.path.suffix))

        with opener.open(self.path, mode) as src:
            src.extractall(ex)

        return Path(ex)

    def _metadata_sniffer(self, path):
        meta = None

        for item in os.listdir(str(path)):
            pass

        return meta

    def __repr__(self):
        return '{}({}, {})'.format(self.__class__.__name__, self.path, self.alias)


class LandsatMetadata(object):
    def __init__(self, metadata_path):
        self.path = Path(metadata_path)

        if not self.path.is_file():
            raise ValueError('{} is not a valid file'.format(str(self.path)))

    def _asdict(self):
        return OrderedDict([(k, v._asdict())
                            for k, v in self.__dict__.items()
                            if v is not self.path])

    def parse(self):
        metadata = self.__class__.read_metadata(self.path)

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
            raise AttributeError('Unknown metadata group {}'.format(group))

        for k, v in attr._asdict().items():
            yield k, v

    def __str__(self):
        return self.__repr__() + '\nMetadata attr: {}'.format(self._asdict())

    def __repr__(self):
        return '{}({})'.format(self.__class__.__name__, self.path)

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
                # handle unclosed groups
                yield from groups

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
                # skip item if not properly formatted
                try:
                    key, value = regex.match(item).groups()
                except AttributeError:
                    continue

                value = __class__.cast_to_best(value)
                keys.append(key)
                values.append(value)

            if len(keys) == len(values) and len(keys) > 1:
                Metadata = namedtuple('Metadata', keys)
                obj = Metadata(*values)
                metadata.append(obj)

        assert len(metadata) > 0

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
