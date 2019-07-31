#!/usr/bin/env python3

# A tool for extracting nordic dictionary entries from a database and dumping
# them to XML.

# Work in progress.

# See also:
#   https://www.dhi.ac.uk/lmnl/nordicheadword/displayPage/200?browse=

import sys
import argparse
from   sqlite3 import dbapi2 as sqlite
import lxml.etree
import lxml.builder    
import html

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
    LEFT JOIN translation_link ON
      nordic_headword.id = translation_link.nordic_headword_id
    LEFT JOIN english_headword ON
      english_headword_id = translation_link.english_headword_id
    LIMIT 50
  ;
"""

def get_all_headwords():
    a = argparse.ArgumentParser()
    a.add_argument("--filename",
                   default="live.db",
                   help="Database filename to use instead of live.db")
    args = a.parse_args()

    db = sqlite.connect(args.filename)
    c = db.cursor()

    c.execute(main_query)
    for row in c.fetchall():
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

def run():
    headwords = [ transform(headword) for headword in get_all_headwords() ]

    the_doc = ROOT(*headwords)
    xml_text = lxml.etree.tostring(the_doc,
                                   pretty_print=True,
                                   encoding='UTF-8'
    )
    sys.stdout.buffer.write(xml_text)


if __name__ == '__main__':
    run()
