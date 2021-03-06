# -*- coding: utf-8 -*-

# nordic_extract.py, by Martin Keegan
# A tool for extracting nordic dictionary entries from a database and dumping
# them to XML.
#
# Copyright (C) 2019, Open Book Publishers
#
# To the extent that this work is covered by copyright, you may redistribute
# and/or modify it under the terms of the Apache Software Licence v2.0

import shutil
import sqlite3
import nordic_order

DEV_MODE = True # print debug output to stderr

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
    ORDER BY nordic_headword.name COLLATE nordic
  ;
"""

main_english_query = """
  SELECT grammar.name AS part_of_speech,
         'Eng' AS language_code,
         english_headword.name AS english_headword_name,
         english_headword.id AS ehw_id
    FROM english_headword
    LEFT JOIN grammar ON english_headword.grammar_id = grammar.id
    ORDER BY english_headword.name COLLATE NOCASE
  ;
"""

translations_query = """
  SELECT * FROM translations WHERE nhw_id = ?
   ORDER BY nhw_id
         COLLATE nordic
  ;
"""

eng_translations_query = """
  SELECT * FROM translations WHERE ehw_id = ?
   ORDER BY nhw_id
         COLLATE nordic
  ;
"""

alternatives_query = """
  SELECT * FROM alternative
    LEFT JOIN language ON language_id = language.id
   WHERE nordic_headword_id = ?
   ORDER BY nordic_headword_id
         COLLATE nordic
  ;
"""

comparisons_query = """
  SELECT nordic_headword2_id, name FROM comparison
    LEFT JOIN nordic_headword ON nordic_headword2_id = nordic_headword.id
   WHERE nordic_headword1_id = ?
   ORDER BY nordic_headword1_id
         COLLATE nordic
  ;
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
                  nordic_headword.name AS nordic_name,
                  lang1.short_name AS lang_short_name,
                  lang2.short_name as trans_lang_short_name,
                  english_headword_id AS ehw_id,
                  english_headword.name AS english_name,
                  evidence AS evidence,
                  law.short_name AS law_short_name
             FROM translation_link
             LEFT JOIN english_headword ON
                       english_headword_id = english_headword.id
             LEFT JOIN language_law_instance ON
                       translation_link_id = translation_link.id
             LEFT JOIN language lang1 ON
                       language_law_instance.language_id = lang1.id
             LEFT JOIN law ON law_id = law.id
             LEFT JOIN nordic_headword ON
                       nordic_headword_id = nordic_headword.id
             LEFT JOIN language lang2 ON
                       nordic_headword.language_id = lang2.id
           ;
        """
          ]
    for ddl in ddls:
        c.execute(ddl)
    db.commit()
    db.close()

def get_db_handle(args, active_filename):
    """Provides a DBAPI-style handle to an open database, having previously
       copied that database to a temporary location and made some schema
       changes to the temporary copy."""
    fix_db(args.filename, active_filename)
    db = sqlite3.connect(active_filename)
    db.row_factory = sqlite3.Row
    nordic_order.add_collation(db, "nordic")
    return db

def run_query(db, q, q_args):
    c = db.cursor()

    c.execute(q, q_args)
    for row in c.fetchall():
        if DEV_MODE:
            pass # print(tuple(row), file=sys.stderr)
        yield row
