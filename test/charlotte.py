#!/usr/bin/env python
# coding: utf-8

"""
Simple test program for johanna in background mode.
Creates and uses a ~/.johanna folder which can be disposed at will.

Created: 27.08.20
"""

import johanna

def main():
    johanna.apply_schema("./schema.sql")
    with johanna.Connection("Charlotte") as c:
        c.cur.execute("insert or ignore into kvpairs(k, v) values (1, 'eins')")
        c.commit()
    johanna.flag_as_error()

if __name__ == "__main__":
    johanna.main(main, dbname="hurz.sqlite")
