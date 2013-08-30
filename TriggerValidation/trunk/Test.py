#!/usr/bin/env python

import re,urllib2,os
import constants

class Test:
    """ One ATN test along with test results and log pointers """
    bugs = None
    # special settings for matching bugs in full logs (that are huge)
    full_enable=True       # enable at the beginning?
    full_counter=0         # counter for number of times we downloaded a full log
    full_maxsize=50        # maximum size of "full log" to be downloadable, in megabytes
    full_nmax=10           # after full_nmax full logs are downloaded, full_enabled will be set to False
    # test settings
    urlbase=''
    CHECK_NICOS = True
    URLTIMEOUT = 60
    def __init__(s,urlbase=''):
        s.urlbase=urlbase
        s.name = 'EMPTY'
        # exit status
        s.overall = False
        s.exit = False
        s.error = None
        s.warn = False
        s.exitcode = None
        # links to log segments:
        s.lextract = None
        s.lerror = None
        s.ldir = None
        s.ltail = None
        s.llog = None
        # information from NICOS summary page for the same test
        s.nicoserr = False
        s.nicoswarn = False
        s.lnicos = None
        # marks log extracts that were actually used to match this test to a bug
        s.uextract = False
        s.uerror = False
        s.utail = False
        s.ulog = False
        s.unicos = False
    def initSoup(s,row,nicoslogs={}):
        """ Initializes one ATN test from two pieces of information:
        - a BeautifulSoup-formatted table row
        - a map (indexed by test name), containing for each test its NICOS info: (iserror,iswarning,nicoslink)
        """
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
        # identify tests labeled with yellow "WARN"
        warnf = v[6].find('font',attrs={'color':'orange'})
        if warnf:
            s.warn = str(warnf.contents[0])=='WARN'
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
        # nicos information
        tnicos = nicoslogs.get(s.name)
        if tnicos:
            s.nicoserr = tnicos[0]
            s.nicoswarn = tnicos[1]
            s.lnicos = tnicos[2]
        else:
            # assert False
            pass
    def initOracle(s,row):
        """ Initializes one ATN test from oracle DB:
        - ( TR.NAME,TR.TNAME,TR.Ecode,TR.CODE,TR.RES,TR.NAMELN,TR.WDIRLN )
        EXAMPLE:
        ('TriggerTest_TestConfiguration#AthenaTrigRDO_L2EFMerging_merge', 'AthenaTrigRDO_L2EFMerging_merge', 40, 2, 3, '<a href="http://cern.ch/atlas-computing/links/distDirectory/nightlies/developmentWebArea/nicos_web_area18X0VAL64BS6G47TrgOpt/NICOS_TestLog_rel_1/Trigger_TrigValidation_TriggerTest_60__TriggerTest_TestConfiguration__AthenaTrigRDO_L2EFMerging_merge__x.html">TriggerTest_TestConfiguration#AthenaTrigRDO_L2EFMerging_merge</a>', 'http://cern.ch/atlas-computing/links/buildDirectory/nightlies/devval/AtlasTrigger/rel_1/NICOS_area/NICOS_atntest18X0VAL64BS6G47TrgOpt/triggertest_testconfiguration_work')
        """
        import BeautifulSoup
        s.name = row[1]
        soup = BeautifulSoup.BeautifulSoup(row[5])
        try:
            x = soup.find("a")['href']
            s.lnicos = str(x)
        except:
            pass
        tpair = row[0].split('#')
        assert len(tpair)==2, 'ERROR: unepxected PROJNAME. Expected something like [%s] but found [%s], which is missing a hashtag'%('TrigP1Test_TestConfiguration#AllMT_physicsV4_run_stop_run',row[0])
        s.lextract = row[-1]+'/%s__%s.log'%(tpair[0],tpair[1])
        s.ldir = wdir = row[-1]+'/'+s.name+'/'
        s.lerror = wdir+'checklog.log'
        s.ltail = wdir+'atn_tail.log'
        s.llog = wdir+'atn_test.log'
        # populate result codes
        ecode,res = row[2],row[4]
        s.overall = 'OK' if res != 3 else 'ERROR'
        s.exit = 'OK' if ecode==0 else 'ERROR'
        s.error = 'OK' if res==0 else 'ERROR'
        s.warn = res in (1,2)
        s.exitcode = ecode
        s.nicoswarn = res in (1,2)
        s.nicoserr = res in (3,)
        print s.name,ecode,res
        pass
    def __str__(s):
        return '%s\t %s %s %s'%(s.name,s.overall,s.exit,s.error)
    def is_error_athena_nonicos(s):
        nafail = (s.error == 'N/A') and (s.exit=='FAIL') and (s.overall=='ERROR')
        timeout = (s.exit=='TIMEOUT')
        return True if (re.match('FAIL',s.error) or nafail or timeout) else False
    def is_error_athena_nicos(s):
        """ this is tricky: we only want to accept nicos errors IF the test is totally fine in ATN """
        if s.is_error_athena_nonicos(): return False
        if re.match('FAIL',s.exit): return False
        if re.match('ERROR',s.overall): return False
        nicoserr = s.CHECK_NICOS and s.nicoserr
        return True if nicoserr else False
    def is_error_athena(s):
        return True if ( s.is_error_athena_nonicos() or s.is_error_athena_nicos() ) else False
    def is_error_exit(s):
        if s.is_error_athena(): return False
        return True if re.match('FAIL',s.exit) else False
    def is_error_post(s):
        if s.is_error_athena(): return False
        if s.is_error_exit(): return False
        #print 'is_error_post',s.name,s.overall  #FIXMEAK
        return True if re.match('ERROR',s.overall) else False
    def is_warning(s):
        """ Only report warnings if it is not also an athena error, exit error, or log parse error """
        if s.is_error_athena(): return False
        if s.is_error_exit(): return False
        if s.is_error_post(): return False
        return s.warn or s.nicoswarn
    def samebug(s,t):
        if t.name == s.name and t.overall==s.overall and t.exit==s.exit and t.error==s.error and t.exitcode==s.exitcode:
            return True
        return False
    def fixedbug(s,t):
        """ s = older nightly; t = current nightly"""
        if t.name != s.name: return False
        assert s.is_error_exit() or s.is_error_athena() or s.is_warning(),'This function should only be called from buggy tests'
        if t.is_error_athena(): return False
        if t.is_error_exit(): return False
        if t.is_error_post(): return False  # let's keep this as a failure category, too
        if s.is_warning():
            if t.is_warning(): return False     # don't report a test as fixed until all warnings are gone
        return True if t.overall == 'OK' else False
    def match(s,last=[]):
        """ Match this test to a bug in local BugTracker using a variety of test logs.
        last is an optional list of tests from yesterday, and can be used to label some bugs as NEW
        """
        status = '' if any([l.samebug(s) for l in last]) else constants.NEWSTATUS
        bug = None
        bugid=00000
        bugurl = "none"
        bugtitle = '<font style="BACKGROUND-COLOR: yellow">FIXME</font>'
        ref_mismatch = s.is_warning()  # if True, only match using the NICOS log (ignoring all other logs)
        if True:
            if re.match('AllPT_physicsV4_magField_on_off_on',s.name) and not ref_mismatch:
                smlink = os.path.dirname(s.llog)+'/'+'warn.log'
                try:
                    bug = s.bugs.match(urllib2.urlopen(smlink,timeout=s.URLTIMEOUT).read())
                except (urllib2.HTTPError,urllib2.URLError) as e :
                    print 'WARNING: the following error-grep link leads to "404 page not found":'
                    print '   ',s.lerror
                    bug = None                
            if re.search('Upload',s.name) and not ref_mismatch:
                smlink = os.path.dirname(s.llog)+'/'+'uploadSMK.log'
                try:
                    bug = s.bugs.match(urllib2.urlopen(smlink,timeout=s.URLTIMEOUT).read())
                except (urllib2.HTTPError,urllib2.URLError) as e :
                    print 'WARNING: the following error-grep link leads to "404 page not found":'
                    print '   ',s.lerror
                    bug = None
            if not bug and s.lerror and not ref_mismatch:
                try:
                    bug = s.bugs.match(urllib2.urlopen(s.lerror,timeout=s.URLTIMEOUT).read())
                    if bug: s.uerror = True
                except (urllib2.HTTPError,urllib2.URLError) as e :
                    print 'WARNING: the following error-grep link leads to "404 page not found":'
                    print '   ',s.lerror
                    bug = None
            if not bug and s.lextract and not ref_mismatch:
                try:
                    bug = s.bugs.match(urllib2.urlopen(s.lextract,timeout=s.URLTIMEOUT).read())
                    if bug: s.uextract = True
                except (urllib2.HTTPError,urllib2.URLError) as e :
                    print 'WARNING: the following error-summary link leads to "404 page not found":'
                    print '   ',s.lextract
                    if ref_mismatch:
                        print '   ','THIS BUG CANNOT BE MATCHED'
                    bug = None
            if not bug and s.ltail and not ref_mismatch:
                try:
                    bug = s.bugs.match(urllib2.urlopen(s.ltail,timeout=s.URLTIMEOUT).read())
                    if bug: s.utail = True
                except (urllib2.HTTPError,urllib2.URLError) as e :
                    print 'WARNING: the following tail link leads to "404 page not found":'
                    print '   ',s.ltail
                    bug = None
            if not bug and s.lnicos:
                try:
                    bug = s.bugs.match(urllib2.urlopen(s.lnicos,timeout=s.URLTIMEOUT).read(),ref_mismatch=ref_mismatch)
                    if bug: s.unicos = True
                except (urllib2.HTTPError,urllib2.URLError) as e :
                    print '%s: the following NICOS link leads to "404 page not found":'%('WARNING' if Test.full_enable else 'ERROR')
                    print '   ',s.lnicos
                    if not ( s.llog and Test.full_enable ):
                        print '   ','THIS BUG CANNOT BE MATCHED'
                    bug = None
                # special fake bug number for unmatched NICOS-only bugs
                if not bug and s.is_error_athena_nicos():
                    bugid=1
            if not bug and s.llog and Test.full_enable  and not ref_mismatch:
                try:
                    # only check full logs if they are under 50 MB in size
                    site = urllib2.urlopen(s.llog,timeout=s.URLTIMEOUT)
                    meta = site.info()
                    nmbX = meta.getheaders("Content-Length")[0]
                    nmb = int(nmbX)/1024/1024
                    if nmb < Test.full_maxsize:
                        Test.full_counter += 1
                        bug = s.bugs.match(site.read())
                        if bug: s.ulog = True
                except (urllib2.HTTPError,urllib2.URLError) as e :
                    print 'ERROR: the following test log link leads to "404 page not found":'
                    print '   ',s.llog
                    print '   ','THIS BUG CANNOT BE MATCHED'
                    bug = None
                # if we exceeded the maximum number of times to download a full log, disable further attempts
                # this is here to prevent cases where a build failure causes a gazillion ATN test crashes,
                # in which case checking full log for each of them would take forever. So limit it to full_nmax attempts.
                if Test.full_counter>=Test.full_nmax:
                    print 'WARNING: disabling full-log matching because maximum number of full-log downloads has been reached:',Test.full_nmax
                    Test.full_enable = False
            if bug:
                bugid=bug.id
                bugurl = bug.url()
                bugtitle = bug.fetch_metadata()
            else:
                s.bugs.add_unknown()
        return status,bug,bugid,bugurl,bugtitle
