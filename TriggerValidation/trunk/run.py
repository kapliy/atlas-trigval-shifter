#!/usr/bin/env python
# coding: utf-8

# enable bug lookup functionality
MATCH_BUGS = True
# Set to false to die on first exception (and print detailed error summary)
SKIP_ERRORS = True
# choose default release (may be over-ridden on command line)
rel = 5
# compare with the dby(day-before-yesterday) release, rather than yesterday?
dby = False

import common
import sys,getpass,datetime

if len(sys.argv)>=2:
    rel = int(sys.argv[1])
    assert rel>=0 and rel<=6,'Release must be an integer between 0 and 6'

if len(sys.argv)>=4:
    dby = True
    print 'INFO: using Day-Before-Yesterday nightly instead of Yesterday'
    print '      (this is useful if yesterday nightly build failed)'

import Nightly
Nightly.Nightly.rel = rel
import Project
Project.Project.rel = rel
Project.Project.dby = dby
Project.Project.SKIP_ERRORS = SKIP_ERRORS
# tweaks for *full* log matching:
Project.Project.full_enable = False
Project.Project.full_nmax   = 10    # increase this if you really NEED to match more full logs
from Test import Test
Test.CHECK_NICOS = True
from Bug import BugTracker
Project.Project.MATCH_BUGS = MATCH_BUGS
bugs = BugTracker()
bugs.prefill()
Project.Project.bugs = bugs

# ADD NEW BUGS HERE
# (but sweep them into Bug.py BugTracker::prefill() at the end of the shift)
#bugs.add_new(,[""])

# Load the list of nightlies that we need to validate
from configure_nightlies import X    

# Dump shift report to an html file
if __name__=="__main__":
    if getpass.getuser()=='antonk':
        f = open('/hep/public_html/VAL/index2.html','w')
    else:
        f = open('index.html','w')
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
                print >>f,'- [<a href="%s">bug #%d</a>] : %s'%(bug.url(),bug.id,bug.fetch_comment())
        print >>f,''
        print >>f,'RTT memory report:'
        print >>f,'The following tests had a >10% increase in total memory consumption with respect to the minimum memory usage in the past 6 days:'
        print >>f,''
        print >>f,'Detailed report is below.'
        print >>f,'Failures that were NOT present in yesterday’s release are marked with %s.'%(Project.NEWSTATUS)
        print >>f,'Failures that were fixed between yesterday and today are marked with %s.'%(Project.FIXEDSTATUS)
        print >>f,''
        if getpass.getuser()=='antonk':
            print >>f,'Cheers,'
            print >>f,'Anton'
        else:
            print >>f,''
        print >>f,''
    for N in X[:]:
        try:
            N.load()
        except:
            print 'WARNING: skipping release',N.name
            if not SKIP_ERRORS:
                raise
            continue
        for l in N.report():
            print >>f,l
    print >>f,'</pre></body></html>'
    f.close()
