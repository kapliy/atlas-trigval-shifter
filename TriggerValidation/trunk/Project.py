#!/usr/bin/env python

import sys,os,re,urllib2,time,datetime
import BeautifulSoup as bs
from Test import Test

from constants import *

class Project:
    """ One trigger validation project that has its own ATN and NICOS page
    name = { TrigP1Test , TriggerTest , TrigAnalysisTest }
    atn = URL_TO_ATN_PAGE (make sure to substitute release number with %d)
    """
    rel = 0
    USE_ORACLE = False
    URLTIMEOUT = 60
    SKIP_ERRORS = True
    dby = False
    def __init__(s,name,atn,grep=None,project=None,arch=None,opt=None,linuxos=None,comp=None):
        """ Most attributes can be bootstrapped from the atn URL """
        s.name = name
        s.atn = atn
        s.grep = name if grep==None else grep  # grep string to select a subset of tests (eg: TrigAnalysisTest)
        s.parent = None  # back-navigation to the Nightly
        # optional *input* metadata for Oracle access that can be used to narrow down particular arch
        s.project = project if project else s.project_from_atn(atn)  # AtlasTrigger, AtlasHLT
        s.arch = arch if arch else s.arch_from_atn(atn)              # x86_64, i686
        s.opt = opt if opt else s.opt_from_atn(atn)                  # opt, dbg
        s.linuxos = linuxos                                          # slc5, slc6
        s.comp = comp                                                # gcc43
        # derived metadata from oracle DB
        s.cur_nid,s.cur_relid,s.cur_jid = None,None,None
        s.last_nid,s.last_relid,s.last_jid = None,None,None
        # link and contents of the NICOS *build* page
        s.nicoslinks = []
        # tests that failed to build
        s.errBuildPackages,s.errBuildLinks = [],[]
        # tests that built OK but failed build unit tests
        s.errUnitPackages, s.errUnitLinks    = [],[]
        # tests that had build warnings
        s.warnBuildPackages,s.warnBuildLinks = [],[]
        # derived quantities
        s.pres_nicoslink = None
        s.last_nicoslink = None
        s.pres = []
        s.last = []
        s.pres_soup = None
        s.last_soup = None
        s.new_bugs = []
    def project_from_atn(s,atn):
        parts = atn.split('/')
        for part in parts:
            if part[:5] == 'Atlas':
                return part
        raise ValueError("project_from_atn: failed to detect project substring (AtlasBLABLA) in url %s"%atn)
    def arch_from_atn(s,atn):
        parts = atn.split('/')
        for part in parts:
            if re.search('64B',part):
                return 'x86_64'
            elif re.search('32B',part):
                return 'i686'
        raise ValueError("arch_from_atn: failed to detect arch substring (64B or 32B) in url %s"%atn)
    def opt_from_atn(s,atn):
        parts = atn.split('/')
        for part in parts:
            if part[-3:] == 'Opt':
                return 'opt'
            elif part[-3:] == 'Dbg':
                return 'dbg'
        raise ValueError("opt_from_atn: failed to detect compiler opt substring (Opt or Dbg) in %s"%atn)
    def project_from_atn(s,atn):
        parts = atn.split('/')
        for part in parts:
            if part[:5] == 'Atlas':
                return part
        raise ValueError("project_from_atn failed on %s"%atn)
    def prel(s,r):
        """ A simple function to return previous release """
        if not s.dby: # use yesterday:
            return r-1 if r>0 else 6
        else:         # use day-before-yesterday:
            return r-2 if r>1 else (5 if r==0 else 6)
    def last_rel(s):
        return s.prel(s.rel)
    def pres_url(s):
        return s.atn%s.rel
    def any_url(s,r):
        return s.atn%r
    def last_url(s):
        return s.any_url(s.last_rel())
    def get_tests_from_url(s,url):
        res = []
        try:
            page = urllib2.urlopen(url,timeout=s.URLTIMEOUT)
        except:
            # sometimes web page was not created and this can cause the skipping some release
            print 'OOPS: check web page availability (maybe not yet available): '
            print '     ',url
            pass    
        soup = bs.BeautifulSoup(page)
        # make sure we are not accidentally looking at last week's results
        # (e.g., if we are fetching the page before it's been updated)
        if not soup.find('p'):
            print 'OOPS: check web page availability: '
            print '     ',url
        lastupdate = str(soup.find('p').string).strip()
        assert re.match('Last updated ',lastupdate),'Unexpected page format: cannot find "Last Updated" element'
        # compute a delta between today and test date
        l = lastupdate.replace('Last updated ','').replace('CET ','').replace('CEST ','')
        testdate_time = time.strptime(l)
        testdate = datetime.datetime(*testdate_time[:6])
        nowdate = datetime.datetime.now()
        delta = (nowdate-testdate).days
        #print 'DEBUG: DELTA =',delta
        #print 'DEBUG: URL =',url
        if delta>4:
            print '(delta>4): DELTA =',delta
            print 'See URL =',url
        assert delta<=4,"Results on this page are older than 5 days - probably, the test hasn't finished yet"
        # retrieve links to NICOS logs that are grepped before truncation
        # the following parameters exploit the layout of NICOS summary page as seen in May 2012
        TABLE_INDEX = 2
        COLOR_ERROR = '#E87DA8'
        COLOR_WARNING = '#FA9EB0'
        nicoslogs = {}  # key = test_name; value = [iserror,iswarning,nicoslink]
        nicoslink = None
        try:
            nicoslink = (soup.findAll('p')[1]).findAll('a')[0]['href']
            #print nicoslink
            data = urllib2.urlopen(nicoslink)
            soupn = bs.BeautifulSoup(data.read())
            table = soupn.findAll('table',{'cellspacing':'0','cellpadding':'5'})[TABLE_INDEX]
            rows = table.findAll('tr')
            assert len(rows)>0,'Cannot find any records in NICOS build summary table'
            for row in rows[1:]:
                links = row.findAll('a')
                if len(links)!=2:
                    break # break out on the last row
                # only look at tests that correspond to current Project
                tname_full = (links[0].string).strip()
                # If s.name == TriggerTest-SLC6-GCC46, separate out the first part: sname_pt1 = TriggerTest
                sname_pt1 = s.name
                if len(s.grep.split('-'))>=2:
                    sname_pt1 = s.grep.split('-')[0]
                if not (re.match(s.grep,tname_full) or re.match(sname_pt1,tname_full)):
                    continue
                tname = tname_full.split('#')[1]
                nicosdir = os.path.dirname(nicoslink)
                tlink = nicosdir + '/' + links[0].get('href')
                tcolor = row.get('bgcolor')
                iserror = (tcolor==COLOR_ERROR)
                iswarning = (tcolor==COLOR_WARNING)
                # sometimes, the same test appears multiple times
                if not tname in nicoslogs:
                    nicoslogs[tname] = (iserror,iswarning,tlink)
        except:
            print 'WARNING: unable to retrieve NICOS logs for Project [%s]. Will continue using ATN logs only'%s.name
            if not s.SKIP_ERRORS:
                raise
            pass
        # retrieve actual test table
        table = soup.find('table',id='ATNResults')
        assert table, 'Unable to find table: %s'%table
        rows = table.findAll('tr',{ "class" : "hi" })
        for row in rows:
            t = Test(urlbase=url)
            t.initSoup(row,nicoslogs)
            res.append(t)
        return res,soup,nicoslink
    def get_tests_from_oracle(s,jid):
        """ returns a list of failed Tests using direct queries to Oracle """
        from db_helpers import oracle
        res = []
        cmd = """ select TR.NAME,TR.TNAME,TR.Ecode,TR.CODE,TR.RES,TR.NAMELN,TR.WDIRLN from testresults TR inner join PROJECTS P on P.projid=TR.projid where TR.jid=%d and P.PROJNAME='%s' """%(jid,s.project)
        if s.grep:
            cmd += " and TR.NAME like '%s%%' "%s.grep  # and TR.Res>0 
        q = oracle.fetch(cmd)
        q.sort(key = lambda x: x[0])
        for x in q:
            st = x[3] # Status code: 0 - initialization, 1 - ongoing (in progress), 2 - completion
            if st!=2:
                print 'WARNING: skipping test [%s], which is still %s: '%(x[0],'initializing' if st==0 else 'running')
                continue
            t = Test()
            t.initOracle(x)
            res.append(t)
        return res
    def load(s):
        print '--> Loading ATN project:',s.name
        if Project.USE_ORACLE:
            # tests from today's rel
            s.load_oracle_keys(False)
            s.pres = s.get_tests_from_oracle(s.cur_jid)
            # tets from yesterday's rel
            s.load_oracle_keys(True)
            s.last = s.get_tests_from_oracle(s.last_jid)
            # build errors
            s.load_build_oracle(s.cur_jid)
        else:
            s.pres,s.pres_soup,s.pres_nicoslink = s.get_tests_from_url(s.pres_url())
            s.last,s.last_soup,s.last_nicoslink = s.get_tests_from_url(s.last_url())
            s.load_build_soup()
        return True
    def load_oracle_keys(s,last=False):
        """ Loads primary keys from the oracle DB """
        from db_helpers import oracle
        xtra = ''
        if s.linuxos:
            xtra += " and J.os='%s'"%s.linuxos
        if s.comp:
            xtra += " and J.comp='%s'"%s.comp
        rel = s.last_rel() if last else s.rel
        cmd = " select J.jid,N.nid,R.relid from JOBS J inner join Nightlies N on N.nid=J.nid inner join Releases R on R.relid=J.relid where N.nname='%s' and J.arch='%s' and J.opt='%s' %s and R.name='rel_%d' and R.RELTSTAMP > sysdate - interval '6' day " % (s.parent.name,s.arch,s.opt,xtra,rel)
        res = oracle.fetch(cmd)
        assert len(res)>0,'ERROR: cannot locate %s in the oracle DB. Query: [%s]'%(s.name,cmd)
        assert len(res)<2,'ERROR: multiple entries found in oracle DB for %s. Consider adding linuxos and comp options in configure_nightlies to specialize to a particular compiler or scientific linux version. Query: [%s]'%(s.name,cmd)
        assert len(res[0])==3,'ERROR: buggy query in Project::load_oracle_keys()'
        if last:
            s.last_jid,s.last_nid,s.last_relid = res[0]
        else:
            s.cur_jid,s.cur_nid,s.cur_relid = res[0]
        return
    def load_build_oracle(s,jid):
        """ Query build errors directly from the database 
        Results are saved in s.errBuildPackages and s.errBuildLinks (etc)
        """
        from db_helpers import oracle
        assert jid,'ERROR: s.jid not populated, which should happen in Project::load_oracle_keys()'
        cmd = """ select PK.PNAME,CR.NAMELN,CR.Res from compresults CR inner join PROJECTS P on P.projid=CR.projid inner join PACKAGES PK on PK.pid=CR.PID where CR.jid=%d and P.PROJNAME='%s' and CR.Res>0 """%(jid,s.project)
        res = oracle.fetch(cmd)
        # errors: status code = 3
        s.errBuildPackages = [ x[0] for x in res if x[2]>=3 ]
        s.errBuildLinks = [ x[1] for x in res if x[2]>=3 ]
        # serious warnings: status code = 2
        s.warnBuildPackages = [ x[0] for x in res if x[2]==2 ]
        s.warnBuildLinks = [ x[1] for x in res if x[2]==2 ]
        return
    def load_build_soup(s):
        """Extract a NICOS link to be able to detect build errors.
        If this throws errors, you'll have to check for build errors manually
        """
        try:
            nicos = str(s.pres_soup.findAll('script')[-2].string.split(',')[1].replace('"','').replace(')',''))
            nicoslinks = [nicos,]
            nicoslinks = list(set(nicoslinks))
            # this also acts as a validation for user's input of ATN links for this nightly:
            assert len(nicoslinks)>0,'Unable to locate a link to NICOS build summary table'
            s.nicoslinks = nicoslinks
            for nicoslink in s.nicoslinks:
                # now check nicos page for any build errors (those don't get reported by ATN!)
                data = urllib2.urlopen(nicoslink)
                # fix some buggy html (align tag outside of parent tag) before parsing
                soup = bs.BeautifulSoup(data.read().replace('<align=center >',''))
                table = soup.find('table',{'cellspacing':'10%'})
                rows = table.findAll('tr')
                assert len(rows)>0,'Cannot find any records in NICOS build summary table'
                errBuildPackages = []
                errBuildLinks = []
                errUnitPackages = []
                errUnitLinks = []
                # locate the column containing unit test results
                idxUnit = None
                try:
                    for ititle,title in enumerate(rows[0].findAll('td')):
                        if title.find('b') and title.find('b').text=='Unit Test':
                            idxUnit = ititle
                            break
                except:
                    idxUnit = None
                nicosdir = os.path.dirname(nicoslink)
                for row in rows[1:]:
                    # build errors
                    if row.find('img',src='cross_red.gif'):
                        errBuildPackages.append( row.contents[0].a.string )
                        errBuildLinks.append( nicosdir + '/' + row.contents[0].a['href'] )
                    # unit test errors in builds
                    failUnit = idxUnit!=None and len(row.findAll('td'))>idxUnit and row.findAll('td')[idxUnit]
                    if failUnit:
                        alink = row.findAll('td')[idxUnit].find('a')
                        if alink and alink.text=='FAIL':
                            errUnitPackages.append( row.contents[0].a.string )
                            errUnitLinks.append( nicosdir + '/' + alink['href'] )
                s.errBuildPackages += errBuildPackages
                s.errBuildLinks += errBuildLinks
                s.errUnitPackages += errUnitPackages
                s.errUnitLinks += errUnitLinks
        except:
            print 'WARNING: unable to parse the NICOS build page. Build errors will NOT be detected!'
            raise # enable for debugging
    def dump(s):
        if s.pres_soup:
            print s.soup.prettify()
    def process_errors(s,err):
        """ prints the errors in a nicely formatted way """
        total = 0
        res = []
        if len(err)==0:
            res.append('    None')
            return res,total
        else:
            ts,statuses,bugs,bugids,bugurls,bugtitles = [],[],[],[],[],[]
            for t in err:
                total += 1
                status,bug,bugid,bugurl,bugtitle = t.match(s.last)
                # separately keep track of "new" bug reports. Note that this functionality
                # depends on the user to separately add these bugs via bugs.add_new().
                if bug and bug.new==True and not bug in s.new_bugs:
                    s.new_bugs.append(bug)
                ts.append(t)
                statuses.append(status)
                bugs.append(bug)
                bugids.append(bugid)
                bugurls.append(bugurl)
                bugtitles.append(bugtitle)
            # group by bug id
            uniquebugs = list(set(bugids))
            for uid in uniquebugs:
                matchedidx = [i for i,bugid in enumerate(bugids) if bugid==uid]
                # see if all or some tests in this bug group are NEW
                nnew_statuses = [statuses[i] for i in matchedidx if statuses[i]==NEWSTATUS]
                ntotal_statuses = [statuses[i] for i in matchedidx]
                status_summary = NEWSTATUS if len(nnew_statuses)==len(ntotal_statuses) else NEWSTATUS+'(some are old) '
                if len(nnew_statuses)==0: status_summary=''
                # loop over tests in this bug group
                for iorder,i in enumerate(matchedidx):
                    t = ts[i]
                    # highlight the log link that was actually used to match a bug
                    b1,b2 = ('<b>','</b>') if ts[i].uextract else ('','')
                    lextract = '<a href="%s">%s%s%s</a>'%(ts[i].lextract if ts[i].lextract else DUMMY_LINK,b1,ts[i].name,b2)
                    b1,b2 = ('<b>','</b>') if ts[i].uerror else ('','')
                    lerror = '<a href="%s">%serr%s</a>'%(ts[i].lerror if ts[i].lerror else DUMMY_LINK,b1,b2)
                    b1,b2 = ('<b>','</b>') if ts[i].ulog else ('','')
                    llog = '<a href="%s">%slog%s</a>'%(ts[i].llog if ts[i].llog else DUMMY_LINK,b1,b2)
                    b1,b2 = ('<b>','</b>') if ts[i].utail else ('','')
                    ltail = '<a href="%s">%stail%s</a>'%(ts[i].ltail if ts[i].ltail else DUMMY_LINK,b1,b2)
                    b1,b2 = ('<b>','</b>') if ts[i].unicos else ('','')
                    lnicos = '<a href="%s">%snicos%s</a>'%(ts[i].lnicos if ts[i].lnicos else DUMMY_LINK,b1,b2)
                    # last test with this bug id: print bug summary
                    if iorder==len(matchedidx)-1:
                        # special handling for the case of one test only affected by this bug
                        offset = '       ' if len(matchedidx)>1 else '    -  '
                        closed_summary = ''
                        wontfix_summary = ''
                        if bugs[i]:
                            if bugs[i].is_closed():
                                closed_summary = CLOSEDSTATUS
                            if bugs[i].is_wontfix():
                                wontfix_summary = WONTFIXSTATUS
                        if bugids[i] >= 0:
                            res.append('%s%s (%s)(%s)(%s)(%s):\n       [<a href="%s">bug #%s</a>] %s%s%s%s'%(offset,lextract,lerror,llog,ltail,lnicos,bugurls[i],bugids[i],closed_summary,wontfix_summary,status_summary,bugtitles[i]))
                        else:
                            res.append('%s%s (%s)(%s)(%s)(%s):\n       [Exit Category #%s] %s%s%s%s'%(offset,lextract,lerror,llog,ltail,lnicos,bugids[i],closed_summary,wontfix_summary,status_summary,bugtitles[i]))
 
                    # for others, just list the bugs, one per line, with comma in the end of each line
                    else:
                        offset = '    -  ' if iorder==0 else '       '
                        res.append('%s%s (%s)(%s)(%s)(%s),'%(offset,lextract,lerror,llog,ltail,lnicos))
        return res,total
    def report(s):
        res = []
        res.append('')
        res.append( '%s [<a href="%s">ATN</a> , <a href="%s">NICOS</a>]   +yesterday\'s links: [<a href="%s">ATN</a> , <a href="%s">NICOS</a>]:'%(s.name,s.pres_url(),s.pres_nicoslink,s.last_url(),s.last_nicoslink))
        res += s.report_build()
        header_len = len(res)
        total = 0
        # athena errors
        err = [t for t in s.pres if t.is_error_athena()]
        msg,tot = s.process_errors(err)
        if tot>0:
            res.append('  <i>Tests with ERRORs</i>:')
            res += msg; total+=tot
        # exit errors
        err = [t for t in s.pres if t.is_error_exit()]
        msg,tot = s.process_errors(err)
        if tot>0:
            res.append('  <i>Tests that finished without errors, but crashed on Athena exit</i>:')
            res += msg; total+=tot
        # validation errors
        err = [t for t in s.pres if t.is_error_post()]
        if len(err)!=0:
            res.append('  <i>Tests that finished and exited without errors, but post-test diff checks failed</i>:')
            for t in err:
                status = '' if any([l.samebug(t) for l in s.last]) else ' '+NEWSTATUS
                total += 1
                res.append('    - <a href="%s">%s</a> (<a href="%s">nicos</a>)%s'%(t.lextract,t.name,t.lnicos,status))
        # warnings
        err = [t for t in s.pres if t.is_warning()]
        msg,tot = s.process_errors(err)
        if tot>0:
            res.append('  <i>Tests that finished without errors, but warnings given at ATN</i>:')
            res += msg; total+=tot
        # if there were no errors of any kind, just say so
        if total==0:
            res = res[0:header_len]
            res.append('  All OK!')
        # summarize bugs that were fixed since previous release
        res += s.report_fixed()
        return res
    def report_build(s):
        """ Reports a summary of build failures """
        res = []
        if len(s.nicoslinks)>0:
            res.append( 'Build links: ' + ' '.join( ['<a href="%s">%d</a>'%(nicoslink,i+1) for i,nicoslink in enumerate(s.nicoslinks)] ) )
        if len(s.errBuildPackages)>0:
            pout = '<font color="#FF6666">Build errors:</font>'
            iprinted = 0
            for package,blink in sorted( zip(s.errBuildPackages,s.errBuildLinks) , key = lambda t: t[0] ):
                # see if s.errBuildLinks are already wrapped around "a href" tags
                pout += ' %s'%blink if re.search('a href',blink) else ' <a href="%s">%s</a>'%(blink,package)
                iprinted += 1
                if iprinted>=15:
                    pout += ' ... and others (check build links above)'
                    break
            res.append(pout)
        if len(s.errUnitPackages)>0:
            pout = '<font color="#FF00BF">Unit test errors (in builds):</font>'
            iprinted=0
            for package,blink in sorted( zip(s.errUnitPackages,s.errUnitLinks) , key = lambda t: t[0] ):
                pout += ' %s'%blink if re.search('a href',blink) else ' <a href="%s">%s</a>'%(blink,package)
                iprinted += 1
                if iprinted>=15:
                    res.append( ' ... and others (check build links above)' )
                    break
            res.append(pout)
        return res
    def report_fixed(s):
        """ Returns a summary of tests that were fixed between previous and current releases """
        res = []
        # yesterday's errors:
        err = [t for t in s.last if t.is_error_athena() or t.is_error_exit() or t.is_warning()]
        # yesterday's errors that were fixed, and their matches in today's release
        fixed = [] # yesterday's test
        match = [] # corresponding today's test
        bugs = []
        bugids = []
        bugurls = []
        bugtitles = []
        for t in err:
            # today's corresponding tests (if fixed)
            matches = [pres for pres in s.pres if t.fixedbug(pres)]
            assert len(matches) in (0,1), 'Found tests with duplicate names'
            if len(matches)==1:
                fixed.append(t)
                match.append(matches[0])
                status,bug,bugid,bugurl,bugtitle = t.match(s.last)
                bugs.append(bug)
                bugids.append(bugid)
                bugurls.append(bugurl)
                bugtitles.append(bugtitle)
        res.append("  <i>Link to yesterday's broken tests that passed successfully today (as of rel_%d)</i>:"%s.rel)
        # group by bug id
        uniquebugs = list(set(bugids))
        for uid in uniquebugs:
            matchedidx = [i for i,bugid in enumerate(bugids) if bugid==uid]
            # loop over tests in this bug group
            for iorder,i in enumerate(matchedidx):
                t = match[i]
                old = fixed[i]
                # highlight the log link that was actually used to match a bug
                b1,b2 = ('<b>','</b>') if old.uextract else ('','')
                lextract = '<a href="%s">%s%s%s</a>'%(old.lextract if old.lextract else DUMMY_LINK,b1,old.name,b2)
                b1,b2 = ('<b>','</b>') if old.uerror else ('','')
                lerror = '<a href="%s">%serr%s</a>'%(old.lerror if old.lerror else DUMMY_LINK,b1,b2)
                b1,b2 = ('<b>','</b>') if old.ulog else ('','')
                llog = '<a href="%s">%slog%s</a>'%(old.llog if old.llog else DUMMY_LINK,b1,b2)
                b1,b2 = ('<b>','</b>') if old.utail else ('','')
                ltail = '<a href="%s">%stail%s</a>'%(old.ltail if old.ltail else DUMMY_LINK,b1,b2)
                b1,b2 = ('<b>','</b>') if old.unicos else ('','')
                lnicos = '<a href="%s">%snicos%s</a>'%(old.lnicos if old.lnicos else DUMMY_LINK,b1,b2)
                # last test with this bug id: print bug summary
                if iorder==len(matchedidx)-1:
                    # special handling for the case of one test only affected by this bug
                    offset = '       ' if len(matchedidx)>1 else '    -  '
                    closed_summary = ''
                    wontfix_summary = ''
                    if bugs[i]:
                        if bugs[i].is_closed():
                            closed_summary = CLOSEDSTATUS
                        if bugs[i].is_wontfix():
                            wontfix_summary = WONTFIXSTATUS
                    if bugids[i] >= 0:
                        res.append('%s%s (%s)(%s)(%s)(%s):\n       [<a href="%s">bug #%s</a>] %s%s%s%s'%(offset,lextract,lerror,llog,ltail,lnicos,bugurls[i],bugids[i],closed_summary,wontfix_summary,FIXEDSTATUS,bugtitles[i]))
                    else:
                        res.append('%s%s (%s)(%s)(%s)(%s):\n       [Exit Category #%s] %s%s%s%s'%(offset,lextract,lerror,llog,ltail,lnicos,bugids[i],closed_summary,wontfix_summary,FIXEDSTATUS,bugtitles[i]))
                # for others, just list the bugs, one per line, with comma in the end of each line
                else:
                    offset = '    -  ' if iorder==0 else '       '
                    res.append('%s%s (%s)(%s)(%s)(%s),'%(offset,lextract,lerror,llog,ltail,lnicos))
        # don't print anything if no tests were fixed
        if len(match)==0:
            res = []
        return res
