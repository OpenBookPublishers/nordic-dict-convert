import tempfile
import os
from contextlib import contextmanager

@contextmanager
def named_temp():
    fd, path = tempfile.mkstemp()

    try:
        yield path
    finally:
        os.unlink(path)
