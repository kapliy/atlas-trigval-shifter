#!/usr/bin/env python
# coding: utf-8

# enable bug lookup functionality
MATCH_BUGS = True
# choose default release (may be over-ridden on command line)
rel = 5

import common

import sys,getpass,datetime
if len(sys.argv)==2:
    rel = int(sys.argv[1])
    assert rel>=0 and rel<=6,'Release must be an integer between 0 and 6'

import Nightly
Nightly.Nightly.rel = rel
import Project
Project.Project.rel = rel
from Test import Test
from Bug import BugTracker
if MATCH_BUGS:
    Project.Project.MATCH_BUGS = True
    bugs = BugTracker()
    bugs.prefill()
    Project.Project.bugs = bugs

# ADD NEW BUGS HERE
# (but sweep them into Bug.py BugTracker::prefill() at the end of the shift)
#bugs.add_new()
bugs.add_new(92407,['CRITICAL stopped by user interrupt','CRITICAL stopped by user interrupt','CRITICAL stopped by user interrupt','BackCompAthenaTrigBStoESDAOD'])
bugs.add_new(92413,['Start of HLT Processing in EF','Current algorithm: TrigSteer_EF','Segmentation fault'])
    
# Load the list of nightlies that we need to validate
from configure_nightlies import X    

# Dump shift report to an html file
if __name__=="__main__":
    if getpass.getuser()=='antonk':
        f = open('/hep/public_html/VAL/index.html','w')
    else:
        f = open('index.html','w')
    print >>f,'<html><head><title>Trigger Validation Shift Report: rel_%d</title></head><body><pre>'%rel
    if True:
        print >>f,"ValShift Report"
        print >>f,str(datetime.datetime.today()).split()[0]
        print >>f,''
        print >>f,'General-'
        print >>f,''
        print >>f,'New bug reports:'
        for bug in bugs.new_bugs():
            print >>f,'- [<a href="%s">bug #%d</a>] : %s'%(bug.url(),bug.id,bug.fetch_comment())
        print >>f,''
        print >>f,'RTT memory report:'
        print >>f,'The following tests had a >10% increase in total memory consumption with respect to the maximum memory usage in the past 6 days:'
        print >>f,''
        print >>f,'Detailed report is below.'
        print >>f,'Failures that were NOT present in yesterday’s release are marked with %s.'%(Project.NEWSTATUS)
        print >>f,'Failures that were fixed between yesterday and today are marked with %s.'%(Project.FIXEDSTATUS)
        print >>f,''
        print >>f,'Cheers,'
        if getpass.getuser()=='antonk':
            print >>f,'Anton'
        else:
            print >>f,'Superman'
        print >>f,''
    for N in X[:]:
        try:
            N.load()
        except:
            print 'WARNING: skipping release',N.name
            # raise # enable for debugging
            continue
        for l in N.report():
            print >>f,l
    print >>f,'</pre></body></html>'
    f.close()
