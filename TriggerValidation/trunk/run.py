#!/usr/bin/env python
# coding: utf-8

# enable bug lookup functionality
MATCH_BUGS = True
# choose default release (may be over-ridden on command line)
rel = 2

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
#bugs.add_new(,[''])
bugs.add_new(92165,["No such file or directory: '../AllPT_physicsV4_rerun/ef_Default_setup.txt'"],"CheckKeysV4 test failing because previous test (AllPT_physicsV4_rerun) has no output")
bugs.add_new(92501,['invalid next size','ibTrigTauDiscriminant'],"Invalid read in TrigTauDiscriBuilder")
bugs.add_new(92516,['AthMasterSeq', 'AthAlgSeq','TrigSteer_EF','EFBMuMuFex_DiMu_noOS','stack trace'],"Segfault in EFBMuMuFex_DiMu_noOS--fix to be in TrigBphysHypo-00-03-07")
bugs.add_new(92532,"ERROR FATAL No input BS file could be found matching '../AthenaTrigRDOtoBS/raw*.data'")
bugs.add_new(92536,"HLTJobLib:       crash ERROR HLTProcess: could not find any files starting")
# Load the list of nightlies that we need to validate
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
        if len(bugs.new_bugs())>0:
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
