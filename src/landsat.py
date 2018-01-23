import re
import os
from pathlib import Path
from zipfile import ZipFile
from tarfile import TarFile
from collections import namedtuple, OrderedDict


class TarFileWrapper(TarFile):
    def namelist(self):
        return self.getnames()


class LandsatArchive(object):
    def __init__(self, path, extract_path=None, alias='DEFAULT'):
        self.alias = alias
        self.extract = extract_path

        self._is_archive = False
        self._metadata = LandsatMetadata()
        self._description, self._bands, self._path = None, None, None

        self.path = path

    @property
    def path(self):
        return self._path

    @path.setter
    def path(self, value):
        path = Path(value)
        self._is_archive = False

        if path.is_file() and path.suffix in ('.gz', '.zip', 'bz2',):
            # TODO sniff in archive for metadata
            self._is_archive = True

        elif path.is_file() and path.suffix == '.txt':
            self._metadata.path = path
            path = path.parent

        elif path.is_dir():
            self._metadata.path = path / self._metadata_sniffer(os.listdir(str(path)))

        else:
            raise ValueError('{} is not a valid Landsat archive'.format(str(path)))

        self._path = path

    def load(self):
            if self._is_archive:
                self.path = self._decompress()

    def _decompress(self):
            pass

    def _metadata_sniffer(self, names):
        meta = None

        for name in names:
            pass

        # TODO meaningful error
        if meta is None:
            raise ValueError

        return 'name'

    def __repr__(self):
        return '{}({}, {})'.format(self.__class__.__name__, self.path, self.alias)

    @staticmethod
    def factory(archive):
        # TODO use mock for testing
        if archive.suffix == '.zip':
            return ZipFile(str(archive), mode='r')

        else:
            return TarFileWrapper.open(str(archive), mode='r')


class LandsatMetadata(object):
    def __init__(self, metadata_path=None):
        if metadata_path is None:
            self._path = metadata_path

        else:
            self.path = metadata_path

    @property
    def path(self):
        return str(self._path)

    @path.setter
    def path(self, value):
        # TODO check is file and is .txt
        self._delete_attributes()
        self._path = Path(value)

    def _asdict(self):
        return OrderedDict([(k, v._asdict())
                            for k, v in self.__dict__.items()
                            if v is not self._path])

    def _delete_attributes(self):
        for attr in self._asdict():
            delattr(self, attr)

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
            return

        yield from attr._asdict().items()

    # TODO return meaningful string currently it is a mess
    def __str__(self):
        return self.__repr__() + '\nMetadata attr: {}'.format(self._asdict())

    def __repr__(self):
        return '{}({})'.format(self.__class__.__name__, self.path)

    @staticmethod
    def read_metadata(path):
        with open(path, 'r') as src:
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

        # TODO convert into a meaningful exception
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
