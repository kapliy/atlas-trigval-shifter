#!/usr/bin/env python

# enable bug lookup functionality
MATCH_BUGS = True
# choose default release (to be over-ridden on command line)
rel = 2

import common

import sys,getpass
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
