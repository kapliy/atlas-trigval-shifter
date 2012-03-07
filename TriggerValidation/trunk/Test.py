#!/usr/bin/env python

import re

class Test:
    """ One ATN test along with test results and log pointers """
    urlbase=''
    def __init__(s,urlbase):
        s.urlbase=urlbase
        s.name = 'EMPTY'
        # exit status
        s.overall = False
        s.exit = False
        s.error = None
        s.exitcode = None
        # links to log segments:
        s.lextract = None
        s.lerror = None
        s.ldir = None
        s.ltail = None
        s.llog = None
    def initAtn(s,row):
        """ Initializes one ATN test from a BeautifulSoup-formatted table row """
        s.row = v = row.findAll('td')
        assert len(v)==14,'Expecting 14 columns in ATN results table but found: %d'%len(v)
        s.name = str(v[0].contents[0].string)
        # exit status
        s.overall = str(v[2].contents[0].string)
        s.exit = str(v[3].contents[0].string)
        try:
            s.error = str(v[4].contents[0].contents[0].string)
        except:
            s.error = 'None'
        s.exitcode = str(v[10].string)
        # links to log segments:
        s.lextract = s.urlbase + str(v[0].a['href'])
        if v[4].a:
            s.lerror = s.urlbase + str(v[4].a['href'])
        s.ldir = s.urlbase + str(v[-2].a['href'])
        logs = v[-1].findAll('a')
        if s.overall != 'SKIP' and len(logs)==2:
            s.ltail = s.urlbase + str(logs[0]['href'])
            s.llog = s.urlbase + str(logs[1]['href'])
    def __str__(s):
        return '%s\t %s %s %s'%(s.name,s.overall,s.exit,s.error)
    def is_error_athena(s):
        nafail = (s.error == 'N/A') and (s.exit=='FAIL') and (s.overall=='ERROR')
        timeout = (s.exit=='TIMEOUT')
        return True if (re.match('FAIL',s.error) or nafail or timeout) else False
    def is_error_exit(s):
        if s.is_error_athena(): return False
        return True if re.match('FAIL',s.exit) else False
    def is_error_post(s):
        if s.is_error_athena(): return False
        if s.is_error_exit(): return False
        return True if re.match('ERROR',s.overall) else False
    def samebug(s,t):
        if t.name == s.name and t.overall==s.overall and t.exit==s.exit and t.error==s.error and t.exitcode==s.exitcode:
            return True
        return False
    def fixedbug(s,t):
        """ s = older nightly; t = current nightly"""
        if t.name != s.name: return False
        assert s.is_error_exit() or s.is_error_athena(),'This function should only be called from buggy tests'
        if t.is_error_athena(): return False
        if t.is_error_exit(): return False
        if t.is_error_post(): return False  # let's keep this as a failure category, too
        return True
