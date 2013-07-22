#!/usr/bin/env python

import sys,cx_Oracle
#assert len(sys.argv)>1
ps='nghtldb_r'
connection = cx_Oracle.connect("ATLAS_NICOS_R", ps, "int8r")
cursor = connection.cursor()
cursor.execute('ALTER SESSION SET current_schema = ATLAS_NICOS_RND')

def describe_table():
    cmd='select * from tags where 1=0'
    print cursor.description

cmd="""select res,projname,nameln,contname,to_char(tstamp, 'RR/MM/DD') as tstamp,mngrs from compresults natural join projects natural join packages where jid=201305080008001 and projname='AtlasReconstruction'"""

cmd = """select nname,ngroup,ntype,val from NIGHTLIES where nname='17.1.X.Y.Z-VAL2-AtlasCAFHLT'  """
cmd = """select N.nname,R.name,R.TCREL,R.RELTSTAMP from NIGHTLIES N inner join releases R on N.nid = R.nid where nname='17.1.X.Y.Z-VAL2-AtlasCAFHLT' order by R.RELTSTAMP"""
cmd = "select projname from projects where projname like '%Trig%'"
cmd = "select N.nname,R.name,P.projname,T.tagname from tags T inner join projects P on P.projid = T.projid inner join releases R on R.relid=T.relid inner join nighlies N on N.nid=T.nid where R.name='rel_2' and rownum<10"
cmd='select pname,contname from packages where rownum<10'
cmd = "select N.nname,R.name,P.projname,T.tagname,PK.pname,PK.contname from tags T inner join projects P on P.projid = T.projid inner join releases R on R.relid=T.relid inner join nightlies N on N.nid=T.nid inner join packages PK on PK.pid=T.pid where R.name='rel_2' and N.nname='17.1.X.Y-VAL-P1HLT' and rownum<50"

cmd='select name,tname,fname from tests where rownum<10'
print cmd
cursor.execute(cmd)
for bla in cursor.fetchall():
    print bla

connection.close()
