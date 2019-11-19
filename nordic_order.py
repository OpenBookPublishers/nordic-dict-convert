#!/usr/bin/env python3

import os

def get_char_order():
    path = os.path.join(os.path.dirname(__file__), 'all-chars')
    norder = []
    with open(path) as f:
        for line in f.readlines():
            char = line.strip()
            norder.append(char)
    return norder

char_order = get_char_order()

def nordic_alpha_p(c):
    return c in char_order

def collate_nordic(string1, string2):
    if string1 == string2:
        return 0
    if string1 == "":
        return -1
    if string2 == "":
        return 1
    char1 = string1[0]
    char2 = string2[0]

    if char1.lower() == char2.lower():
        return collate_nordic(string1[1:], string2[1:])
    else:
        if nordic_alpha_p(char1) and nordic_alpha_p(char2):
            idx1 = char_order.index(char1.lower())
            idx2 = char_order.index(char2.lower())
            assert idx1 != idx2
            if idx1 < idx2:
                return -1
            return 1
        else:
            if char1 < char2:
                return -1
            else:
                return 1

def add_collation(db, collation_name):
    db.create_collation(collation_name, collate_nordic)
