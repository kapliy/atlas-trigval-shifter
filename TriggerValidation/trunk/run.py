#!/usr/bin/env python

# enable bug lookup functionality
MATCH_BUGS = True
# choose default release (may be over-ridden on command line)
rel = 2

import common

import sys,getpass,datetime
if len(sys.argv)==2:
    rel = int(sys.argv[1])
    assert rel>=0 and rel<=6,'Release must be an integer between 0 and 6'

from Nightly import Nightly
Nightly.rel = rel
from Project import Project
Project.rel = rel
from Test import Test
from Bug import BugTracker
if MATCH_BUGS:
    Project.MATCH_BUGS = True
    bugs = BugTracker()
    bugs.prefill()
    Project.bugs = bugs

# Load the list of nightlies that we need to validate
from configure_nightlies import X    

# Dump shift report to an html file
if __name__=="__main__":
    if getpass.getuser()=='antonk':
        f = open('/hep/public_html/VAL/index.html','w')
    else:
        f = open('index.html','w')
    print >>f,'<html><body><basefont face=""Courier New", Courier, monospace" size="10" color="green"><pre>'
    if True:
        print >>f,"ValShift Report"
        print >>f,str(datetime.datetime.today()).split()[0]
        print >>f,''
        print >>f,'General-'
        print >>f,''
        print >>f,'New bug reports:'
        print >>f,'- '
        print >>f,''
        print >>f,'RTT memory report:'
        print >>f,'The following tests had a >10% increase in total memory consumption with respect to the maximum memory usage in the past 6 days:'
        print >>f,''
        print >>f,'Cheers,'
        if getpass.getuser()=='antonk':
            print >>f,'Anton'
        else:
            print >>f,'Validation shifter'
        print >>f,''
    for N in X[:]:
        try:
            N.load()
        except:
            print 'WARNING: skipping release',N.name
            continue
        for l in N.report():
            print >>f,l
    print >>f,'</pre></body></html>'
    f.close()
