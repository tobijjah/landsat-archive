from contextlib import contextmanager


@contextmanager
def open_stub(name, mode):
    try:
        f = FileMock('foo')
        yield f

    finally:
        f.close()


class FileMock:
    def __init__(self, content):
        self.content = content

    def readlines(self):
        return self.content

    def close(self):
        pass
