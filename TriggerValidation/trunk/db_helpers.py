#!/usr/bin/env python

"""
A global wrapper around the Oracle nightlies database
"""

import cx_Oracle

class DB:
    def __init__(s):
        s.ps='nghtldb_ru'
        s.connection = cx_Oracle.connect("ATLAS_NICOS_RUSER", s.ps, "ATLR")
        s.cursor = connection.cursor()
        s.cursor.execute('ALTER SESSION SET current_schema = ATLAS_NICOS')
    def fetch(s,cmd):
        res = []
        s.cursor.execute(cmd)
        for row in cursor.fetchall():
            res.append(row)
        return res
    def close():
        connection.close()

oracle = DB()
