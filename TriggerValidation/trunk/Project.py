#!/usr/bin/env python

import sys,os,re,urllib2,time,datetime
import BeautifulSoup as bs
from Test import Test

DUMMY_LINK='http://www.NOT.AVAILABLE.com'
NEWSTATUS='[<b><FONT style="BACKGROUND-COLOR: FF6666">NEW</FONT></b>] '
FIXEDSTATUS='[<b><FONT style="BACKGROUND-COLOR: 99FF00">FIXED</FONT></b>] '

class Project:
    """ One trigger validation project that has its own ATN and NICOS page
    name = { TrigP1Test , TriggerTest , TrigAnalysisTest }
    atn = URL_TO_ATN_PAGE (make sure to substitute release number with %d)
    """
    rel = 0
    URLTIMEOUT = 60
    bugs = None
    MATCH_BUGS = False
    SKIP_ERRORS = True
    dby = False
    # special settings for matching bugs in full logs (that are huge)
    full_enable=True       # enable at the beginning?
    full_counter=0         # counter for number of times we downloaded a full log
    full_maxsize=50        # maximum size of "full log" to be downloadable, in megabytes
    full_nmax=10           # after full_nmax full logs are downloaded, full_enabled will be set to False
    def __init__(s,name,atn):
        s.name = name
        s.atn = atn
        s.pres_nicoslink = None
        s.last_nicoslink = None
        s.pres = []
        s.last = []
        s.pres_soup = None
        s.last_soup = None
        s.new_bugs = []
    def prel(s,r):
        """ A simple function to return previous release """
        if not s.dby: # use yesterday:
            return r-1 if r>0 else 6
        else:         # use day-before-yesterday:
            return r-2 if r>1 else (5 if r==0 else 6)
    def pres_url(s):
        return s.atn%s.rel
    def any_url(s,r):
        return s.atn%r
    def last_url(s):
        return s.any_url(s.prel(s.rel))
    def get_tests_from_url(s,url):
        res = []
        page = urllib2.urlopen(url,timeout=s.URLTIMEOUT)
        soup = bs.BeautifulSoup(page)
        # make sure we are not accidentally looking at last week's results
        # (e.g., if we are fetching the page before it's been updated)
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
                if not re.match(s.name,tname_full):
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
            t.initAtn(row,nicoslogs)
            res.append(t)
        return res,soup,nicoslink
    def load(s):
        print '--> Loading ATN project:',s.name
        s.pres,s.pres_soup,s.pres_nicoslink = s.get_tests_from_url(s.pres_url())
        s.last,s.last_soup,s.last_nicoslink = s.get_tests_from_url(s.last_url())
        return True
    def dump(s):
        if s.pres_soup:
            print s.soup.prettify()
    def match_bugs(s,t):
        """ Look up the bugs in local BugTracker, as well as yesterday's cache 
        Uses log error extract, summary extract, and full log tail to do the matching
        """
        status = '' if any([l.samebug(t) for l in s.last]) else NEWSTATUS
        bug = None
        bugid=00000
        bugurl = "none"
        bugcomment = '<font style="BACKGROUND-COLOR: yellow">FIXME</font>'
        if s.MATCH_BUGS:
            if t.lerror:
                try:
                    bug = s.bugs.match(urllib2.urlopen(t.lerror,timeout=s.URLTIMEOUT).read())
                except (urllib2.HTTPError,urllib2.URLError) as e :
                    print 'WARNING: the following error-grep link leads to "404 page not found":'
                    print '   ',t.lerror
                    bug = None
            if not bug and t.lextract:
                try:
                    bug = s.bugs.match(urllib2.urlopen(t.lextract,timeout=s.URLTIMEOUT).read())
                except (urllib2.HTTPError,urllib2.URLError) as e :
                    print 'WARNING: the following error-summary link leads to "404 page not found":'
                    print '   ',t.lextract
                    bug = None
            if not bug and t.ltail:
                try:
                    bug = s.bugs.match(urllib2.urlopen(t.ltail,timeout=s.URLTIMEOUT).read())
                except (urllib2.HTTPError,urllib2.URLError) as e :
                    print 'WARNING: the following tail link leads to "404 page not found":'
                    print '   ',t.ltail
                    print '   ','THIS BUG CANNOT BE MATCHED'
                    bug = None
            if not bug and t.lnicos:
                try:
                    bug = s.bugs.match(urllib2.urlopen(t.lnicos,timeout=s.URLTIMEOUT).read())
                except (urllib2.HTTPError,urllib2.URLError) as e :
                    print '%s: the following NICOS link leads to "404 page not found":'%('WARNING' if Project.full_enable else 'ERROR')
                    print '   ',t.lnicos
                    print '   ','THIS BUG CANNOT BE MATCHED'
                    bug = None
                # special fake bug number for unmatched NICOS-only bugs
                if not bug and t.is_error_athena_nicos():
                    bugid=1
            if not bug and t.llog and Project.full_enable:
                try:
                    # only check full logs if they are under 50 MB in size
                    site = urllib2.urlopen(t.llog,timeout=s.URLTIMEOUT)
                    meta = site.info()
                    nmbX = meta.getheaders("Content-Length")[0]
                    nmb = int(nmbX)/1024/1024
                    if nmb < Project.full_maxsize:
                        Project.full_counter += 1
                        bug = s.bugs.match(site.read())
                except (urllib2.HTTPError,urllib2.URLError) as e :
                    print 'ERROR: the following test log link leads to "404 page not found":'
                    print '   ',t.llog
                    print '   ','THIS BUG CANNOT BE MATCHED'
                    bug = None
                # if we exceeded the maximum number of times to download a full log, disable further attempts
                # this is here to prevent cases where a build failure causes a gazillion ATN test crashes,
                # in which case checking full log for each of them would take forever. So limit it to full_nmax attempts.
                if Project.full_counter>=Project.full_nmax:
                    print 'WARNING: disabling full-log matching because maximum number of full-log downloads has been reached:',Project.full_nmax
                    Project.full_enable = False
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
                # separately keep track of "new" bug reports. Note that this functionality
                # depends on the user to separately add these bugs via bugs.add_new().
                if bug and bug.new==True and not bug in s.new_bugs:
                    s.new_bugs.append(bug)
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
                # see if all or some tests in this bug group are NEW
                nnew_statuses = [statuses[i] for i in matchedidx if statuses[i]==NEWSTATUS]
                ntotal_statuses = [statuses[i] for i in matchedidx]
                status_summary = NEWSTATUS if len(nnew_statuses)==len(ntotal_statuses) else NEWSTATUS+'(some are old) '
                if len(nnew_statuses)==0: status_summary=''
                # loop over tests in this bug group
                for iorder,i in enumerate(matchedidx):
                    t = ts[i]
                    lextract = ts[i].lextract if ts[i].lextract else DUMMY_LINK
                    lerror = ts[i].lerror if ts[i].lerror else DUMMY_LINK
                    llog = ts[i].llog if ts[i].llog else DUMMY_LINK
                    ltail = ts[i].ltail if ts[i].ltail else DUMMY_LINK
                    lnicos = ts[i].lnicos if ts[i].lnicos else DUMMY_LINK
                    # last test with this bug id: print bug summary
                    if iorder==len(matchedidx)-1:
                        # special handling for the case of one test only affected by this bug
                        offset = '       ' if len(matchedidx)>1 else '    -  '
                        if bugids[i] >= 0:
                            res.append('%s<a href="%s">%s</a> (<a href="%s">err</a>)(<a href="%s">log</a>)(<a href="%s">tail</a>)(<a href="%s">nicos</a>):\n       [<a href="%s">bug #%s</a>] %s%s'%(offset,lextract,ts[i].name,lerror,llog,ltail,lnicos,bugurls[i],bugids[i],status_summary,bugcomments[i]))
                        else:
                            res.append('%s<a href="%s">%s</a> (<a href="%s">err</a>)(<a href="%s">log</a>)(<a href="%s">tail</a>)(<a href="%s">nicos</a>):\n       [Exit Category #%s] %s%s'%(offset,lextract,ts[i].name,lerror,llog,ltail,lnicos,bugids[i],status_summary,bugcomments[i]))
 
                    # for others, just list the bugs, one per line, with comma in the end of each line
                    else:
                        offset = '    -  ' if iorder==0 else '       '
                        if bugids[i] >= 0:
                            res.append('%s<a href="%s">%s</a> (<a href="%s">err</a>)(<a href="%s">log</a>)(<a href="%s">tail</a>)(<a href="%s">nicos</a>),'%(offset,lextract,ts[i].name,lerror,llog,ltail,lnicos))
                        
        return res,total
    def report(s):
        res = []
        res.append('')
        res.append( '%s [<a href="%s">ATN</a> , <a href="%s">NICOS</a>]   +yesterday\'s links: [<a href="%s">ATN</a> , <a href="%s">NICOS</a>]:'%(s.name,s.pres_url(),s.pres_nicoslink,s.last_url(),s.last_nicoslink))
        total = 0
        # athena errors
        err = [t for t in s.pres if t.is_error_athena()]
        msg,tot = s.process_errors(err);
        if tot>0:
            res.append('  <i>Tests with ERRORs</i>:')
            res += msg; total+=tot
        # exit errors
        err = [t for t in s.pres if t.is_error_exit()]
        msg,tot = s.process_errors(err);
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
                res.append('    - <a href="%s">%s</a>%s'%(t.lextract,t.name,status))
        # if there were no errors of any kind, just say so
        if total==0:
            res = res[0:2]
            res.append('  All OK!')
        # summarize bugs that were fixed since previous release
        res += s.fixed_error_report()
        return res
    def fixed_error_report_old(s):
        """ Returns a list of tests that were fixed between previous and current releases """
        res = []
        # yesterday's errors:
        err = [t for t in s.last if t.is_error_athena() or t.is_error_exit()]
        # yesterday's errors that were fixed, and their matches in today's release
        fixed = [] # yesterday's test
        match = [] # today's test
        for t in err:
            # today's corresponding tests (if fixed)
            matches = [pres for pres in s.pres if t.fixedbug(pres)]
            assert len(matches) in (0,1), 'Found tests with duplicate names'
            if len(matches)==1:
                fixed.append(t)
                match.append(matches[0])
        res.append("  <i>Link to yesterday's broken tests that passed successfully today (as of rel_%d)</i>:"%s.rel)
        for t,old in zip(match,fixed):
            status,bug,bugid,bugurl,bugcomment = s.match_bugs(old)
            lextract = old.lextract if old.lextract else DUMMY_LINK
            lerror = old.lerror if old.lerror else DUMMY_LINK
            llog = old.llog if old.llog else DUMMY_LINK
            ltail = old.ltail if old.ltail else DUMMY_LINK
            lnicos = old.lnicos if old.lnicos else DUMMY_LINK
            offset = '    - '
            if bugid >= 0:
                res.append( '%s<a href="%s">%s</a> (<a href="%s">err</a>)(<a href="%s">log</a>)(<a href="%s">tail</a>)(<a href="%s">nicos</a>) : %s %s'%(offset,lextract,old.name,lerror,llog,ltail,lnicos,('[<a href="%s">bug #%s</a>]'%(bugurl,bugid)) if bugid!=0 else '',FIXEDSTATUS) )
            else:
                res.append( '%s<a href="%s">%s</a> (<a href="%s">err</a>)(<a href="%s">log</a>)(<a href="%s">tail</a>)(<a href="%s">nicos</a>) : %s %s'%(offset,lextract,old.name,lerror,llog,ltail,lnicos,('[Exit Category #%s]'%(bugid)) if bugid!=0 else '',FIXEDSTATUS) )
        # don't print anything if no tests were fixed
        if len(match)==0:
            res = []
        return res
    def fixed_error_report(s):
        """ Returns a list of tests that were fixed between previous and current releases """
        res = []
        # yesterday's errors:
        err = [t for t in s.last if t.is_error_athena() or t.is_error_exit()]
        # yesterday's errors that were fixed, and their matches in today's release
        fixed = [] # yesterday's test
        match = [] # corresponding today's test
        bugs = []
        bugids = []
        bugurls = []
        bugcomments = []
        for t in err:
            # today's corresponding tests (if fixed)
            matches = [pres for pres in s.pres if t.fixedbug(pres)]
            assert len(matches) in (0,1), 'Found tests with duplicate names'
            if len(matches)==1:
                fixed.append(t)
                match.append(matches[0])
                status,bug,bugid,bugurl,bugcomment = s.match_bugs(t)
                bugs.append(bug)
                bugids.append(bugid)
                bugurls.append(bugurl)
                bugcomments.append(bugcomment)
        res.append("  <i>Link to yesterday's broken tests that passed successfully today (as of rel_%d)</i>:"%s.rel)
        # group by bug id
        uniquebugs = list(set(bugids))
        for uid in uniquebugs:
            matchedidx = [i for i,bugid in enumerate(bugids) if bugid==uid]
            # loop over tests in this bug group
            for iorder,i in enumerate(matchedidx):
                t = match[i]
                old = fixed[i]
                lextract = old.lextract if old.lextract else DUMMY_LINK
                lerror = old.lerror if old.lerror else DUMMY_LINK
                llog = old.llog if old.llog else DUMMY_LINK
                ltail = old.ltail if old.ltail else DUMMY_LINK
                lnicos = old.lnicos if old.lnicos else DUMMY_LINK
                # last test with this bug id: print bug summary
                if iorder==len(matchedidx)-1:
                    # special handling for the case of one test only affected by this bug
                    offset = '       ' if len(matchedidx)>1 else '    -  '
                    if bugids[i] >= 0:
                        res.append('%s<a href="%s">%s</a> (<a href="%s">err</a>)(<a href="%s">log</a>)(<a href="%s">tail</a>)(<a href="%s">nicos</a>):\n       [<a href="%s">bug #%s</a>] %s%s'%(offset,lextract,old.name,lerror,llog,ltail,lnicos,bugurls[i],bugids[i],FIXEDSTATUS,bugcomments[i]))
                    else:
                        res.append('%s<a href="%s">%s</a> (<a href="%s">err</a>)(<a href="%s">log</a>)(<a href="%s">tail</a>)(<a href="%s">nicos</a>):\n       [Exit Category #%s] %s%s'%(offset,lextract,old.name,lerror,llog,ltail,lnicos,bugids[i],FIXEDSTATUS,bugcomments[i]))
                # for others, just list the bugs, one per line, with comma in the end of each line
                else:
                    offset = '    -  ' if iorder==0 else '       '
                    res.append('%s<a href="%s">%s</a> (<a href="%s">err</a>)(<a href="%s">log</a>)(<a href="%s">tail</a>)(<a href="%s">nicos</a>),'%(offset,lextract,old.name,lerror,llog,ltail,lnicos))
        # don't print anything if no tests were fixed
        if len(match)==0:
            res = []
        return res
