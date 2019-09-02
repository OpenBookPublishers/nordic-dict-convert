
Nordic dictionary convertor
===========================

This code takes a SQLite database representing a dictionary of legal terms
in various Nordic languages and outputs its contents as well-formatted XML.

Installation
------------

The code relies on a handful of dependencies such as SQLite and `lxml`; if
installing these is a problem for someone,
we'll provide a `requirements.txt` file.

Usage
-----

    $ ./nordic_extract.py > output.xml

