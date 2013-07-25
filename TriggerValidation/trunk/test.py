#!/usr/bin/env python

import sys

try:
    import cx_Oracle
except ImportError:
    print 'ERROR: cannot import cx_Oracle module'
    print '       if not on lxplus, you can try compiling it by sourcing oracle/source.sh'
    sys.exit(1)

ps='nghtldb_ru'
connection = cx_Oracle.connect("ATLAS_NICOS_RUSER", ps, "ATLR")
cursor = connection.cursor()
cursor.execute('ALTER SESSION SET current_schema = ATLAS_NICOS')

def describe_table():
    cmd='select * from tags where 1=0'
    print cursor.description

PROJECTS = ['AtlasP1HLT','AtlasAnalysis','AtlasTrigger','AtlasHLT','AtlasProduction']
nname = '17.2.X-VAL' #'17.1.X.Y-VAL2-P1HLT'
nid,relid,jid = 10, 5312, 201307220010002

cmd="""select res,projname,nameln,contname,to_char(tstamp, 'RR/MM/DD') as tstamp,mngrs from compresults natural join projects natural join packages where jid=201305080008001 and projname='AtlasReconstruction'"""

cmd = """select nname,ngroup,ntype,val from NIGHTLIES where nname='17.1.X.Y.Z-VAL2-AtlasCAFHLT'  """
cmd = """select N.nname,R.name,R.TCREL,R.RELTSTAMP from NIGHTLIES N inner join releases R on N.nid = R.nid where nname='17.1.X.Y.Z-VAL2-AtlasCAFHLT' order by R.RELTSTAMP"""
cmd = "select projname from projects where projname like '%Trig%'"
cmd = "select N.nname,R.name,P.projname,T.tagname from tags T inner join projects P on P.projid = T.projid inner join releases R on R.relid=T.relid inner join nighlies N on N.nid=T.nid where R.name='rel_2' and rownum<10"
cmd='select pname,contname from packages where rownum<10'
cmd = "select N.nname,R.name,P.projname,T.tagname,PK.pname,PK.contname from tags T inner join projects P on P.projid = T.projid inner join releases R on R.relid=T.relid inner join nightlies N on N.nid=T.nid inner join packages PK on PK.pid=T.pid where R.name='rel_2' and N.nname='17.1.X.Y-VAL-P1HLT' and rownum<50"
cmd=""" select name,tname,fname,type from tests where tests.type='INT' and rownum<20 """

# select nightly
cmd = """select nname,ngroup,ntype,val from NIGHTLIES where nname='%s'  """%nname
# select release
cmd = """select R.nid,R.relid,N.nname,R.name,R.TCREL,R.RELTSTAMP from NIGHTLIES N inner join releases R on N.nid = R.nid where nname='%s' and R.RELTSTAMP > sysdate - interval '6' day order by R.RELTSTAMP"""%nname
# select jobid (for a given nightly+release, contains various architecture+gcc tags)
cmd = """ select * from JOBS where nid=%d and relid=%d and OPT='opt' and ARCH='x86_64' """%(nid,relid)
# jobstat for a jobid (repeated for each project) - USELESS
cmd = """ select JS.projid,P.projname from JOBSTAT JS inner join projects P on P.projid=JS.projid where JS.jid=%d """%jid
# compilation statistics for a given project - USELESS
cmd = """ select P.PROJNAME,C.NPACK,C.NPB,C.NER from CSTAT C inner join PROJECTS P on P.projid=C.projid where C.jid=%d and P.PROJNAME='AtlasAnalysis' """%(jid)
# compilation results: list of packages with a warning or error
cmd = """ select P.PROJNAME,PK.PNAME,PK.CONTNAME,CR.Res,CR.ERRTEXT,CR.NAMELN from compresults CR inner join PROJECTS P on P.projid=CR.projid inner join PACKAGES PK on PK.pid=CR.PID where CR.jid=%d and P.PROJNAME='AtlasAnalysis' and CR.Res>0 """%(jid)
# test results TODO
cmd = """ select P.PROJNAME,PK.PNAME,PK.CONTNAME,TR.Ecode,TR.CODE,TR.RES,TR.NAME,TR.NAMELN,TR.WDIRLN from testresults TR inner join PROJECTS P on P.projid=TR.projid inner join PACKAGES PK on PK.pid=TR.PID where TR.jid=%d and P.PROJNAME='AtlasAnalysis' and TR.Res>-10 """%(jid)

cmd = """ select J.jid,N.nid,R.relid from JOBS J inner join Nightlies N on N.nid=J.nid inner join Releases R on R.relid=J.relid where N.nname='18.X.0-VAL' and J.arch='x86_64' and J.opt='opt' and R.name='rel_3' and R.RELTSTAMP > sysdate - interval '6' day"""

print cmd
cursor.execute(cmd)
ntot=0
for bla in cursor.fetchall():
    print bla
    ntot+=1
print 'Total =',ntot

connection.close()
