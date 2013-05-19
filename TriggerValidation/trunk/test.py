#!/usr/bin/env python

import sys,cx_Oracle
assert len(sys.argv)>1
ps=sys.argv[1]
connection = cx_Oracle.connect("ATLAS_NICOS_R", ps, "int8r")
