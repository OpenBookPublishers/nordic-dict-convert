#!/usr/bin/env python3
# -*- coding: utf-8 -*-

# nordic_extract.py, by Martin Keegan
# A tool for extracting nordic dictionary entries from a database and dumping
# them to XML.
#
# Copyright (C) 2019, Open Book Publishers
#
# To the extent that this work is covered by copyright, you may redistribute
# and/or modify it under the terms of the Apache Software Licence v2.0

# Work in progress.
#
# Known bugs (out of date):
#
#  * the system by design currently only emits one translation for each
#    headword. This is obviously wrong.
#  * does not disassemble the embedded (sic) HTML
#  * does not extract all relevant fields

# See also:
#   https://www.dhi.ac.uk/lmnl/nordicheadword/displayPage/200?browse=

import os
import shutil
import sys
import argparse
import tempfile
from contextlib import contextmanager
import sqlite3
import lxml.etree
import lxml.builder    
import html

DEV_MODE = True # print debug output to stderr
E        = lxml.builder.ElementMaker()

# The names on the right hand side below, e.g., "nordic_headword", are used
# as the tag names in the generated XML, i.e.,
#   <nordic_headword>...</nordic_headword>
ROOT         = E.nordic_headwords
HEADWORD     = E.nordic_headword
NAME         = E.name
POS          = E.type
LANG         = E.language
TEXT         = E.article
ENGLISH      = E.translation
REFERENCES   = E.references
COMPARISON   = E.comparison
EXPRESSIONS  = E.expressions
ALT_NAME     = E.alternative_name

main_query = """
  SELECT grammar.name AS part_of_speech,
         language.short_name AS language_code,
         nordic_headword.name AS nordic_headword_name,
         article AS article,
         expressions AS expressions,
         english_headword.name AS english_headword_name
    FROM nordic_headword
    LEFT JOIN grammar ON nordic_headword.grammar_id = grammar.id
    LEFT JOIN language ON language_id = language.id
    LEFT JOIN translation_link ON nordic_headword.id = nordic_headword_id
    LEFT JOIN english_headword ON english_headword.id = english_headword_id
    WHERE nordic_headword_id IS NOT NULL
  ;
"""

def fix_db(filename, active_filename):
    """Copy the database from FILENAME into ACTIVE_FILENAME, then modify
       its schema slightly."""
    shutil.copyfile(filename, active_filename)
    db = sqlite3.dbapi2.connect(active_filename)
    c = db.cursor()
    ddls = [
    ]
    for ddl in ddls:
        c.execute(ddl)
    db.commit()
    db.close()

def get_db_handle(args, active_filename):
    fix_db(args.filename, active_filename)
    db = sqlite3.dbapi2.connect(active_filename)
    db.row_factory = sqlite3.Row
    return db

def get_all_headwords(db):
    c = db.cursor()

    c.execute(main_query)
    for row in c.fetchall():
        if DEV_MODE:
            print(tuple(row), file=sys.stderr)
        yield row

def fixup_article(article):
    if article is None:
        return None
    if article == "":
        return None
    if article.startswith("<p>"):
        assert article.endswith("</p>")
        article = article[3:]
        article = article[:-4]
    return html.unescape(article)

def transform(headword):
    assert 6 == len(tuple(headword))

    args = [
        NAME(headword['nordic_headword_name']),
        POS(headword['part_of_speech']),
        LANG(headword['language_code']),
        ENGLISH(headword['english_headword_name']),
        REFERENCES("TBD"),
        COMPARISON("TBD"),
        EXPRESSIONS("TBD"),
        ALT_NAME("TBD")
    ]

    article_text = fixup_article(headword['article'])
    if article_text is not None:
        args.append(TEXT(article_text))

    return HEADWORD(*args)

def run(args, tmp_path):
    db = get_db_handle(args, tmp_path)
    headwords = [ transform(hw) for hw in get_all_headwords(db) ]

    the_doc = ROOT(*headwords)
    xml_text = lxml.etree.tostring(the_doc,
                                   pretty_print=True,
                                   encoding='UTF-8'
    )
    sys.stdout.buffer.write(xml_text)

@contextmanager
def named_temp():
    fd, path = tempfile.mkstemp()

    yield path

    os.unlink(path)

def process_args():
    a = argparse.ArgumentParser()
    a.add_argument("--filename",
                   default="live.db",
                   help="Database filename to use instead of live.db")
    args = a.parse_args()
    with named_temp() as tmp_path:
        return run(args, tmp_path)

if __name__ == '__main__':
    exit(process_args())
