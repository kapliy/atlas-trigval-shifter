#!/usr/bin/env python

"""
# TEMPLATE TO ADD A NIGHTLY:
N = Nightly('','')
N.add(Project('TrigP1Test',''))
N.add(Project('TriggerTest',''))
N.add(Project('TrigAnalysisTest',''))
X.append(N)
"""

# enable tab completion
try:
    import readline
except ImportError:
    print "Module readline not available."
else:
    import rlcompleter
    readline.parse_and_bind("tab: complete")

import sys,re
import urllib2,httplib
import BeautifulSoup as bs
rel = 2
if len(sys.argv)==2:
    rel = int(sys.argv[1])
    assert rel>=0 and rel<=6,'Release must be an integer between 0 and 6'

_MATCH_BUGS = True
_URLTIMEOUT = 60

import Bug
bugs = Bug.BugTracker()
bugs.prefill()

class Nightly:
    """ One nightly cache along with a URL to its NICOS path
    name = 17.1.X.Y-VAL-P1HLT 
    nicos = URL_TO_NICOS_PAGE (make sure to substitute release number with %d)
    PS - nicos URL is optional
    """
    def __init__(s,name,nicos=None):
        s.name = name
        s.nicos = nicos
        s.projects = []
    def add(s,project):
        s.projects.append(project)
    def nicos_url(s,r=rel):
        return s.nicos % r
    def load(s):
        print 'Working on nightly:',s.name,'rel_%d'%rel
        return [p.load() for p in s.projects]
    def report(s):
        res = []
        res.append('')
        res.append('')
        res.append('%s (rel_%d)'%(s.name,rel))
        res.append( '' + '='*len(s.name) )
        for p in s.projects:
            res += p.report()
        return res

class Project:
    """ One trigger validation project that has its own ATN and NICOS page
    name = { TrigP1Test , TriggerTest , TrigAnalysisTest }
    atn = URL_TO_ATN_PAGE (make sure to substitute release number with %d)
    """
    def __init__(s,name,atn):
        s.name = name
        s.atn = atn
        s.soup = None
        s.pres = []
        s.last = []
        s.pres_soup = None
        s.last_soup = None
    def prel(s,r):
        """ A simple function to return previous release """
        return r-1 if r>0 else 6
    def pres_url(s,r=rel):
        return s.atn%r
    def last_url(s):
        return s.pres_url(s.prel(rel))
    def get_tests_from_url(s,url):
        res = []
        page = urllib2.urlopen(url,timeout=_URLTIMEOUT)
        soup = bs.BeautifulSoup(page)
        table = soup.find('table',id='ATNResults')
        assert table, 'Unable to find table: %s'%table
        rows = table.findAll('tr',{ "class" : "hi" })
        for row in rows:
            t = Test(urlbase=url)
            t.initAtn(row)
            res.append(t)
        return res,soup
    def load(s):
        print '--> Loading ATN project:',s.name
        s.pres,s.pres_soup = s.get_tests_from_url(s.pres_url())
        s.last,s.last_soup = s.get_tests_from_url(s.last_url())
    def dump(s):
        if s.pres_soup:
            print s.soup.prettify()
    def match_bugs(s,t):
        """ Look up the bugs in local BugTracker, as well as yesterday's cache 
        Uses log error extract, summary extract, and full log tail to do the matching
        """
        status = '' if any([l.samebug(t) for l in s.last]) else '[<b>NEW</b>] '
        bug = None
        bugid=00000
        bugurl = "none"
        bugcomment = "FIXME"
        if _MATCH_BUGS:
            if t.lerror:
                bug = bugs.match(urllib2.urlopen(t.lerror,timeout=_URLTIMEOUT).read())
            if not bug and t.lextract:
                bug = bugs.match(urllib2.urlopen(t.lextract,timeout=_URLTIMEOUT).read())
            if not bug and t.ltail:
                bug = bugs.match(urllib2.urlopen(t.ltail,timeout=_URLTIMEOUT).read())
            if bug:
                bugid=bug.id
                bugurl = bug.url()
                bugcomment = bug.fetch_comment()
        return status,bug,bugid,bugurl,bugcomment
    def process_errors(s,err):
        """ prints the errors in a nicely formatted way """
        total = 0
        res = []
        if len(err)==0:
            res.append('    None')
            return res,total
        else:
            ts,statuses,bugs,bugids,bugurls,bugcomments = [],[],[],[],[],[]
            for t in err:
                total += 1
                status,bug,bugid,bugurl,bugcomment = s.match_bugs(t)
                ts.append(t)
                statuses.append(status)
                bugs.append(bug)
                bugids.append(bugid)
                bugurls.append(bugurl)
                bugcomments.append(bugcomment)
            # group by bug id
            uniquebugs = list(set(bugids))
            for uid in uniquebugs:
                matchedidx = [i for i,bugid in enumerate(bugids) if bugid==uid]
                for iorder,i in enumerate(matchedidx):
                    t = ts[i]
                    # last test with this bug id: print bug summary
                    if iorder==len(matchedidx)-1:
                        offset = '       ' if len(matchedidx)>1 else '    -  '
                        res.append('%s<a href="%s">%s</a> (<a href="%s">err</a>)(<a href="%s">log</a>)(<a href="%s">tail</a>):\n       [<a href="%s">bug #%s</a>] %s%s'%(offset,ts[i].lextract,ts[i].name,ts[i].lerror,ts[i].llog,ts[i].ltail,bugurls[i],bugids[i],statuses[i],bugcomments[i]))
                    # for others, just list the bugs, one per line, with comma in the end of each line
                    else:
                        offset = '    -  ' if iorder==0 else '       '
                        res.append('%s<a href="%s">%s</a> (<a href="%s">err</a>)(<a href="%s">log</a>)(<a href="%s">tail</a>),'%(offset,ts[i].lextract,ts[i].name,ts[i].lerror,ts[i].llog,ts[i].ltail))
        return res,total
    def report(s):
        res = []
        res.append('')
        res.append( '<a href="%s">%s</a> (+link to <a href="%s">yesterday\'s cache</a>):'%(s.pres_url(),s.name,s.last_url()))
        total = 0
        # athena errors
        res.append('  <u>Tests with ERRORs</u>:')
        err = [t for t in s.pres if t.is_error_athena()]
        msg,tot = s.process_errors(err); res += msg; total+=tot
        # exit errors
        res.append('  <u>Tests that finished without errors, but crashed on Athena exit</u>:')
        err = [t for t in s.pres if t.is_error_exit()]
        msg,tot = s.process_errors(err); res += msg; total+=tot
        # validation errors
        res.append('  <u>Tests that finished and exited without errors, but post-test diff checks failed</u>:')
        err = [t for t in s.pres if t.is_error_post()]
        if len(err)==0:
            res.append('    None')
        else:
            for t in err:
                status = '' if any([l.samebug(t) for l in s.last]) else ' [<b>NEW</b>]'
                total += 1
                res.append('    - <a href="%s">%s</a>%s'%(t.lextract,t.name,status))
        # if there were no errors, just say so
        if total==0:
            res = res[0:2]
            res.append('  All OK!')
        return res

class Test:
    """ Once ATN test """
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
    
X = []

# high priority releases
N = Nightly('17.1.X.Y-VAL-P1HLT','http://atlas-computing.web.cern.ch/atlas-computing/links/distDirectory/nightlies/patchWebArea/nicos_web_area171XYVALP1HLT32BS5G4P1HLTOpt/nicos_testsummary_%d.html')
N.add(Project('TrigP1Test','http://atlas-computing.web.cern.ch/atlas-computing/links/buildDirectory/nightlies/17.1.X.Y-VAL/AtlasP1HLT/rel_%d/NICOS_area/NICOS_atntest171XYVALP1HLT32BS5G4P1HLTOpt/trigp1test_testconfiguration_work/'))
N.add(Project('TriggerTest','http://atlas-computing.web.cern.ch/atlas-computing/links/buildDirectory/nightlies/17.1.X.Y-VAL/AtlasP1HLT/rel_%d/NICOS_area/NICOS_atntest171XYVALP1HLT32BS5G4P1HLTOpt/triggertest_testconfiguration_work/'))
X.append(N)

N = Nightly('17.1.X.Y.Z-VAL-AtlasCAFHLT','http://atlas-computing.web.cern.ch/atlas-computing/links/distDirectory/nightlies/patchWebArea/nicos_web_area171XYZVALAtlasCAFHLT32BS5G4AtlasCAFHLTOpt/nicos_testsummary_%d.html')
N.add(Project('TrigP1Test','http://atlas-computing.web.cern.ch/atlas-computing/links/buildDirectory/nightlies/17.1.X.Y.Z-VAL/AtlasCAFHLT/rel_%d/NICOS_area/NICOS_atntest171XYZVALAtlasCAFHLT32BS5G4AtlasCAFHLTOpt/trigp1test_testconfiguration_work/'))
N.add(Project('TriggerTest','http://atlas-computing.web.cern.ch/atlas-computing/links/buildDirectory/nightlies/17.1.X.Y.Z-VAL/AtlasCAFHLT/rel_%d/NICOS_area/NICOS_atntest171XYZVALAtlasCAFHLT32BS5G4AtlasCAFHLTOpt/triggertest_testconfiguration_work/'))
X.append(N)

N = Nightly('17.1.X.Y-VAL2-P1HLT','')
N.add(Project('TrigP1Test','http://atlas-computing.web.cern.ch/atlas-computing/links/buildDirectory/nightlies/17.1.X.Y-VAL2/AtlasP1HLT/rel_%d/NICOS_area/NICOS_atntest171XYVAL2P1HLT32BS5G4P1HLTOpt/trigp1test_testconfiguration_work/'))
N.add(Project('TriggerTest','http://atlas-computing.web.cern.ch/atlas-computing/links/buildDirectory/nightlies/17.1.X.Y-VAL2/AtlasP1HLT/rel_%d/NICOS_area/NICOS_atntest171XYVAL2P1HLT32BS5G4P1HLTOpt/triggertest_testconfiguration_work/'))
X.append(N)

N = Nightly('17.1.X.Y.Z-VAL2-AtlasCAFHLT','')
N.add(Project('TrigP1Test','http://atlas-computing.web.cern.ch/atlas-computing/links/buildDirectory/nightlies/17.1.X.Y.Z-VAL2/AtlasCAFHLT/rel_%d/NICOS_area/NICOS_atntest171XYZVAL2AtlasCAFHLT32BS5G4AtlasCAFHLTOpt/trigp1test_testconfiguration_work/'))
N.add(Project('TriggerTest','http://atlas-computing.web.cern.ch/atlas-computing/links/buildDirectory/nightlies/17.1.X.Y.Z-VAL2/AtlasCAFHLT/rel_%d/NICOS_area/NICOS_atntest171XYZVAL2AtlasCAFHLT32BS5G4AtlasCAFHLTOpt/triggertest_testconfiguration_work/'))
X.append(N)

N = Nightly('17.1.X.Y-VAL-Prod','')
N.add(Project('TrigP1Test','http://atlas-computing.web.cern.ch/atlas-computing/links/buildDirectory/nightlies/17.1.X.Y-VAL/AtlasProduction/rel_%d/NICOS_area/NICOS_atntest171XYVALProd32BS5G4ProdOpt/trigp1test_testconfiguration_work/'))
N.add(Project('TriggerTest','http://atlas-computing.web.cern.ch/atlas-computing/links/buildDirectory/nightlies/17.1.X.Y-VAL/AtlasProduction/rel_%d/NICOS_area/NICOS_atntest171XYVALProd32BS5G4ProdOpt/triggertest_testconfiguration_work/'))
N.add(Project('TrigAnalysisTest','http://atlas-computing.web.cern.ch/atlas-computing/links/buildDirectory/nightlies/17.1.X.Y-VAL/AtlasProduction/rel_%d/NICOS_area/NICOS_atntest171XYVALProd32BS5G4ProdOpt/triganalysistest_testconfiguration_work/'))
X.append(N)

# low priority releases
N = Nightly('17.1.X','')
N.add(Project('TrigP1Test','http://atlas-computing.web.cern.ch/atlas-computing/links/buildDirectory/nightlies/17.1.X/AtlasHLT/rel_%d/NICOS_area/NICOS_atntest171X32BS5G4AtlasHLTOpt/trigp1test_testconfiguration_work/'))
N.add(Project('TriggerTest','http://atlas-computing.web.cern.ch/atlas-computing/links/buildDirectory/nightlies/17.1.X/AtlasTrigger/rel_%d/NICOS_area/NICOS_atntest171X32BS5G4TrgOpt/triggertest_testconfiguration_work/'))
N.add(Project('TrigAnalysisTest','http://atlas-computing.web.cern.ch/atlas-computing/links/buildDirectory/nightlies/17.1.X/AtlasAnalysis/rel_%d/NICOS_area/NICOS_atntest171X32BS5G4AnlOpt/triganalysistest_testconfiguration_work/'))
X.append(N)

N = Nightly('17.1.X-VAL','')
N.add(Project('TrigP1Test','http://atlas-computing.web.cern.ch/atlas-computing/links/buildDirectory/nightlies/17.1.X-VAL/AtlasHLT/rel_%d/NICOS_area/NICOS_atntest171XVAL32BS5G4AtlasHLTOpt/trigp1test_testconfiguration_work/'))
N.add(Project('TriggerTest','http://atlas-computing.web.cern.ch/atlas-computing/links/buildDirectory/nightlies/17.1.X-VAL/AtlasTrigger/rel_%d/NICOS_area/NICOS_atntest171XVAL32BS5G4TrgOpt/triggertest_testconfiguration_work/'))
N.add(Project('TrigAnalysisTest','http://atlas-computing.web.cern.ch/atlas-computing/links/buildDirectory/nightlies/17.1.X-VAL/AtlasAnalysis/rel_%d/NICOS_area/NICOS_atntest171XVAL32BS5G4AnlOpt/triganalysistest_testconfiguration_work/'))
X.append(N)

N = Nightly('17.2.X','')
N.add(Project('TrigP1Test','http://atlas-computing.web.cern.ch/atlas-computing/links/buildDirectory/nightlies/17.2.X/AtlasHLT/rel_%d/NICOS_area/NICOS_atntest172X64BS5G4AtlasHLTOpt/trigp1test_testconfiguration_work/'))
N.add(Project('TriggerTest','http://atlas-computing.web.cern.ch/atlas-computing/links/buildDirectory/nightlies/17.2.X/AtlasTrigger/rel_%d/NICOS_area/NICOS_atntest172X64BS5G4TrgOpt/triggertest_testconfiguration_work/'))
N.add(Project('TrigAnalysisTest','http://atlas-computing.web.cern.ch/atlas-computing/links/buildDirectory/nightlies/17.2.X/AtlasAnalysis/rel_%d/NICOS_area/NICOS_atntest172X64BS5G4AnlOpt/triganalysistest_testconfiguration_work/'))
X.append(N)

N = Nightly('17.2.X-VAL','')
N.add(Project('TrigP1Test','http://atlas-computing.web.cern.ch/atlas-computing/links/buildDirectory/nightlies/17.2.X-VAL/AtlasHLT/rel_%d/NICOS_area/NICOS_atntest172XVAL64BS5G4AtlasHLTOpt/trigp1test_testconfiguration_work/'))
N.add(Project('TriggerTest','http://atlas-computing.web.cern.ch/atlas-computing/links/buildDirectory/nightlies/17.2.X-VAL/AtlasTrigger/rel_%d/NICOS_area/NICOS_atntest172XVAL64BS5G4TrgOpt/triggertest_testconfiguration_work/'))
N.add(Project('TrigAnalysisTest','http://atlas-computing.web.cern.ch/atlas-computing/links/buildDirectory/nightlies/17.2.X-VAL/AtlasAnalysis/rel_%d/NICOS_area/NICOS_atntest172XVAL64BS5G4AnlOpt/triganalysistest_testconfiguration_work/'))
X.append(N)

N = Nightly('17.X.0','')
N.add(Project('TriggerTest','http://atlas-computing.web.cern.ch/atlas-computing/links/buildDirectory/nightlies/dev/AtlasTrigger/rel_%d/NICOS_area/NICOS_atntest17X064BS5G4TrgOpt/triggertest_testconfiguration_work/'))
N.add(Project('TrigAnalysisTest','http://atlas-computing.web.cern.ch/atlas-computing/links/buildDirectory/nightlies/dev/AtlasAnalysis/rel_%d/NICOS_area/NICOS_atntest17X064BS5G4AnlOpt/triganalysistest_testconfiguration_work/'))
X.append(N)

# OK process everything
if __name__=="__main__":
    res = []
    for N in X[:]:
        try:
            N.load()
        except:
            print 'WARNING: skipping release',N.name
            continue
        res += N.report()
    f = open('/hep/public_html/VAL/index.html','w')
    print >>f,'<html><body><basefont face=""Courier New", Courier, monospace" size="10" color="green"><pre>'
    for l in res:
        print >>f,l
    print >>f,'</pre></body></html>'
