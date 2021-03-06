#!/usr/bin/env python3

import sys
import argparse
from sqlite3 import dbapi2 as sqlite
import html
import lxml.html
import lxml.etree

def process_args():
    a = argparse.ArgumentParser()
    a.add_argument("--filename",
                   default="live.db",
                   help="Database filename to use instead of live.db")
    a.add_argument("--output-prefix",
                   default="narrative_doc_",
                   help="Filename prefix for extracted documents")
    args = a.parse_args()

    db = sqlite.connect(args.filename)
    c = db.cursor()
    c.execute("""SELECT id, title, text FROM document;""")
    for id_, title, text in c.fetchall():
        root = lxml.html.fromstring("<div>" + text + "</div>")
        fixed_text = lxml.etree.tostring(root)

        print(title, file=sys.stderr)
        filename = "{}{}.html".format(args.output_prefix, id_)
        with open(filename, "w") as f:
            f.write(fixed_text.decode('utf-8'))

if __name__ == '__main__':
    exit(process_args())
