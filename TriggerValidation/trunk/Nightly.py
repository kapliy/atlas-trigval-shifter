#!/usr/bin/env python

import urllib2
import re,os

class Nightly:
    """ One nightly cache along with a URL to its NICOS path
    name = 17.1.X.Y-VAL-P1HLT 
    nicos = URL_TO_NICOS_PAGE (make sure to substitute release number with %d)
    PS - nicos URL is optional
    """
    rel = 0
    def __init__(s,name,details=''):
        s.name = name
        s.details = details
        s.projects = []
        # keep track of new bug reports
        s.new_bugs = []
    def add(s,project):
        project.parent = s
        s.projects.append(project)
    def load(s):
        assert len(s.projects)>0,'Detected empty nightly without any projects associated with it'
        print 'Working on nightly:',s.name+s.details,'rel_%d'%s.rel
        status = [p.load() for p in s.projects]
    def report(s):
        res = []
        res.append('')
        res.append('')
        rel = '(rel_%d)'%s.rel
        res.append('%s %s'%(s.name+s.details,rel))
        res.append( '' + '='*len(s.name+s.details) )
        for p in s.projects:
            res += p.report()
            s.new_bugs += p.new_bugs
        s.new_bugs = list(set(s.new_bugs))
        return res
