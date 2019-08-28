# -*- coding: utf-8 -*-

# nordic_extract.py, by Martin Keegan
# A tool for extracting nordic dictionary entries from a database and dumping
# them to XML.
#
# Copyright (C) 2019, Open Book Publishers
#
# To the extent that this work is covered by copyright, you may redistribute
# and/or modify it under the terms of the Apache Software Licence v2.0
#
# Given the trivial length of this file, and the fact that its contents are
# so determined by mechanical considerations as to bring its status as
# copyrightable subject matter into question, we effectively disclaim any
# copyright in it.

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
