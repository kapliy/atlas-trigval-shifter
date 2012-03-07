#!/usr/bin/env python

class Nightly:
    """ One nightly cache along with a URL to its NICOS path
    name = 17.1.X.Y-VAL-P1HLT 
    nicos = URL_TO_NICOS_PAGE (make sure to substitute release number with %d)
    PS - nicos URL is optional
    """
    rel = 0
    def __init__(s,name,rel,nicos=None):
        s.name = name
        s.nicos = nicos
        s.projects = []
    def add(s,project):
        s.projects.append(project)
    def nicos_url(s):
        return s.nicos % s.rel
    def load(s):
        print 'Working on nightly:',s.name,'rel_%d'%s.rel
        return [p.load() for p in s.projects]
    def report(s):
        res = []
        res.append('')
        res.append('')
        res.append('%s (rel_%d)'%(s.name,s.rel))
        res.append( '' + '='*len(s.name) )
        for p in s.projects:
            res += p.report()
        return res

