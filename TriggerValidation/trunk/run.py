#!/usr/bin/env python
# coding: utf-8

# Set to false to die on first exception (and print detailed error summary)
SKIP_ERRORS = True
#SKIP_ERRORS = False
# choose default release (may be over-ridden on command line)
rel = 5
# compare with the dby(day-before-yesterday) release, rather than yesterday?
dby = False
# print (to stdout) a summary of all found bugs
SUMMARIZE_BUGS = True
# name of output file
OUTNAME = 'index2.html'
# access experimental Nicos database from Oracle?
USE_ORACLE = False

import sys
print ' '.join(sys.argv)

import common
import getpass,socket,datetime
from constants import *

if len(sys.argv)>=2:
    rel = int(sys.argv[1])
    assert rel>=0 and rel<=6,'Release must be an integer between 0 and 6'

if len(sys.argv)>=4:
    assert sys.argv[3] in ('1','0')
    dby = int(sys.argv[3])
    if dby==1:
        print 'INFO: using Day-Before-Yesterday nightly instead of Yesterday'
        print '      (this is useful if yesterday nightly build failed)'

if len(sys.argv)>=5:
    OUTNAME = sys.argv[4]

try:
    import cx_Oracle
except ImportError:
    if USE_ORACLE:
        print 'ERROR: USE_ORACLE is set to True, but cx_Oracle extension is missing. Disabling it...'
        USE_ORACLE = False

import Nightly
Nightly.Nightly.rel = rel
import Project
Project.Project.rel = rel
Project.Project.USE_ORACLE = USE_ORACLE
Project.Project.dby = dby
Project.Project.SKIP_ERRORS = SKIP_ERRORS
from Test import Test
Test.CHECK_NICOS = True
# tweaks for *full* log matching:
Test.full_enable = False
Test.full_nmax   = 10    # increase this if you really NEED to match more full logs
from Bug import BugTracker
bugs = BugTracker()
bugs.prefill()
Test.bugs = bugs


# Load the list of nightlies that we need to validate
from configure_nightlies import X,nightly_sel

# Dump shift report to an html file
if __name__=="__main__":
    if getpass.getuser()=='antonk' and socket.gethostname()=='kapliy':
        f = open('/hep/public_html/VAL/%s'%OUTNAME,'w')
    else:
        f = open(OUTNAME,'w')
    print >>f,'<html><head><title>Trigger Validation Shift Report: rel_%d</title></head><body>'%rel
    print >>f,'<pre style="font-size: 12; font-family: Courier, \'Courier New\', monospace">'
    if True:
        print >>f,"ValShift Report"
        print >>f,str(datetime.datetime.today()).split()[0]
        print >>f,''
        print >>f,'General-'
        print >>f,''
        if len(bugs.new_bugs())>0:
            print >>f,'New bug reports:'
            for bug in bugs.new_bugs():
                print >>f,'- [<a href="%s">bug #%d</a>] : %s'%(bug.url(),bug.id,bug.fetch_metadata())
        print >>f,''
        if nightly_sel not in (1,2): # RTT report is only expected in PART3
            print >>f,'RTT memory report:'
            print >>f,'The following tests had a >10% increase in total memory consumption with respect to the maximum memory usage in the past 6 days:'
            print >>f,''
        print >>f,'Detailed report is below.'
        print >>f,'Failures that were NOT present in yesterday\'s release are marked with %s.'%(NEWSTATUS)
        print >>f,'Failures that were fixed between yesterday and today are marked with %s.'%(FIXEDSTATUS)
        print >>f,'Bugs that were closed on Savannah (perhaps prematurely) are marked with %s.'%(CLOSEDSTATUS)
        print >>f,''
        if getpass.getuser()=='antonk':
            print >>f,'Cheers,'
            print >>f,'Anton'
        else:
            print >>f,''
        print >>f,''
        f.flush()
        sys.stdout.flush()
    for N in X[:]:
        try:
            N.load()
        except:
            print 'WARNING: skipping release',N.name+N.details
            if not SKIP_ERRORS:
                raise
            continue
        for l in N.report():
            print >>f,l
            f.flush()
            sys.stdout.flush()
    print >>f,'</pre></body></html>'
    f.close()
    sys.stdout.flush()
    if SUMMARIZE_BUGS:
        bugs.summarize_bugs()
