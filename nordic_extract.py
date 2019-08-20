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
COMPARISON   = E.comparison
ALTERNATIVES = E.alternatives
ALTERNATIVE  = E.alternative
ALT_NAME     = E.alternative_name
ALT_LANG     = E.alternative_lang
TRANSLATIONS = E.translations
TRANSLATION  = E.translation
ENG_HEADWORD = E.english_headword
EVIDENCE     = E.evidence

main_query = """
  SELECT grammar.name AS part_of_speech,
         language.short_name AS language_code,
         nordic_headword.name AS nordic_headword_name,
         article AS article,
         expressions AS expressions,
         refs AS refs,
         nordic_headword.id AS nhw_id
    FROM nordic_headword
    LEFT JOIN grammar ON nordic_headword.grammar_id = grammar.id
    LEFT JOIN language ON language_id = language.id
  ;
"""

translations_query = """
  SELECT * FROM translations WHERE nhw_id = ?;
"""

alternatives_query = """
  SELECT * FROM alternative WHERE nordic_headword_id = ?;
"""

def fix_db(filename, active_filename):
    """Copy the database from FILENAME into ACTIVE_FILENAME, then modify
       its schema slightly."""
    shutil.copyfile(filename, active_filename)
    db = sqlite3.dbapi2.connect(active_filename)
    c = db.cursor()
    ddls = [
        """DELETE FROM translation_link WHERE nordic_headword_id IS NULL;""",
        """DELETE FROM translation_link WHERE english_headword_id IS NULL;""",
        """DELETE FROM comparison WHERE nordic_headword1_id IS NULL;""",
        """DELETE FROM comparison WHERE nordic_headword2_id IS NULL;""",
        """CREATE VIEW translations AS
           SELECT translation_link.id AS tl_id,
                  translation_link.nordic_headword_id AS nhw_id,
                  language.short_name AS lang_short_name,
                  english_headword.name AS english_name,
                  evidence AS evidence,
                  law.short_name AS law_short_name
             FROM translation_link
             LEFT JOIN english_headword ON
                       english_headword_id = english_headword.id
             LEFT JOIN language_law_instance ON
                       translation_link_id = translation_link.id
             LEFT JOIN language ON
                       language_law_instance.language_id = language.id
             LEFT JOIN law ON law_id = law.id
           ;
        """
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

def run_query(db, q, q_args):
    c = db.cursor()

    c.execute(q, q_args)
    for row in c.fetchall():
        if DEV_MODE:
            pass # print(tuple(row), file=sys.stderr)
        yield row

def get_all_headwords(db):
    return run_query(db, main_query, [])

def fixup_text(text):
    if text is None:
        return None
    if text == "":
        return None
    if text.startswith("<p>"):
        assert text.endswith("</p>")
        text = text[3:]
        text = text[:-4]
    return html.unescape(text)

def transform(db, headword):
    assert 7 == len(tuple(headword))

    def make_translation(t):
        results = [
            ENG_HEADWORD(t["english_name"])
        ]
        lang = t["lang_short_name"]
        if lang is not None:
            results.append(LANG(lang))

        evidence_text = fixup_text(t["evidence"])
        if evidence_text is not None:
            results.append(EVIDENCE(evidence_text))

        return TRANSLATION(
            *results
        )

    def make_alternative(a):
        results = [
            ALT_NAME(a["alternative_name"]),
            ALT_LANG("TBD")
        ]

        return ALTERNATIVE(
            *results
        )

    tt = run_query(db, translations_query, (headword["nhw_id"],))
    translations = [ make_translation(t) for t in tt ]

    aa = run_query(db, alternatives_query, (headword["nhw_id"],))
    alternatives = [ make_alternative(a) for a in aa ]

    args = [
        NAME(headword['nordic_headword_name']),
        POS(headword['part_of_speech']),
        LANG(headword['language_code']),
        COMPARISON("TBD"),
        TRANSLATIONS(*translations),
        ALTERNATIVES(*alternatives)
    ]

    attributes = ['article', 'refs', 'expressions']
    for a in attributes:
        a_text = fixup_text(headword[a])
        if a_text is not None:
            args.append(E.__getattr__(a)(a_text))

    return HEADWORD(*args)

def run(args, tmp_path):
    db = get_db_handle(args, tmp_path)
    headwords = [ transform(db, hw) for hw in get_all_headwords(db) ]

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
