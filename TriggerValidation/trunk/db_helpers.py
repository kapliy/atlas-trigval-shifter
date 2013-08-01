#!/usr/bin/env python

"""
A global wrapper around the Oracle nightlies database
"""

import cx_Oracle

class DB:
    def __init__(s):
        s.ps='nghtldb_ru'
        s.connection = cx_Oracle.connect("ATLAS_NICOS_RUSER", s.ps, "ATLR")
        s.cursor = s.connection.cursor()
        s.cursor.execute('ALTER SESSION SET current_schema = ATLAS_NICOS')
    def fetch(s,cmd,verbose=False):
        res = []
        if verbose:
            print 'ORACLE:',cmd
        s.cursor.execute(cmd)
        for row in s.cursor.fetchall():
            res.append(row)
        return res
    def close(s):
        s.connection.close()

oracle = DB()

import atexit
def close_connection():
    oracle.close()
atexit.register(close_connection)
