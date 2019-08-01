#!/usr/bin/env python3

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
# Known bugs:
#
#  * the system by design currently only emits one translation for each
#    headword. This is obviously wrong.
#  * the script only emits the first 50 headwords
#  * does not strip the <p> and </p> from the article
#  * does not disassemble the embedded (sic) HTML
#  * does not extract all relevant fields

# See also:
#   https://www.dhi.ac.uk/lmnl/nordicheadword/displayPage/200?browse=

import sys
import argparse
import sqlite3
import lxml.etree
import lxml.builder    
import html

DEV_MODE = True # print debug output to stderr
E        = lxml.builder.ElementMaker()

# The names on the right hand side below, e.g., "nordic_headword", are used
# as the tag names in the generated XML, i.e.,
#   <nordic_headword>...</nordic_headword>
ROOT     = E.nordic_headwords
HEADWORD = E.nordic_headword
NAME     = E.name
POS      = E.type
LANG     = E.language
TEXT     = E.article
ENGLISH  = E.translation

main_query = """
  SELECT grammar.name, language.short_name, nordic_headword.name,
         article, expressions, english_headword.name
    FROM nordic_headword
    LEFT JOIN grammar ON nordic_headword.grammar_id = grammar.id
    LEFT JOIN language ON language_id = language.id
    LEFT JOIN translation_link ON nordic_headword.id = nordic_headword_id
    LEFT JOIN english_headword ON english_headword.id = english_headword_id
    WHERE nordic_headword_id IS NOT NULL
  ;
"""

def get_all_headwords(args):
    db = sqlite3.dbapi2.connect(args.filename)
    c = db.cursor()

    c.execute(main_query)
    for row in c.fetchall():
        if DEV_MODE:
            print(row, file=sys.stderr)
        yield row

def fixup_article(article):
    return html.unescape(article)

def transform(headword):
    (part_of_speech, language, word, article, expressions,
     english_word) = headword

    args = [
        NAME(word),
        POS(part_of_speech),
        LANG(language),
        ENGLISH(english_word)
    ]

    if article is not None:
        args.append(TEXT(fixup_article(article)))

    return HEADWORD(*args)

def run(args):
    headwords = [ transform(hw) for hw in get_all_headwords(args) ]

    the_doc = ROOT(*headwords)
    xml_text = lxml.etree.tostring(the_doc,
                                   pretty_print=True,
                                   encoding='UTF-8'
    )
    sys.stdout.buffer.write(xml_text)

if __name__ == '__main__':
    a = argparse.ArgumentParser()
    a.add_argument("--filename",
                   default="live.db",
                   help="Database filename to use instead of live.db")
    args = a.parse_args()
    run(args)
