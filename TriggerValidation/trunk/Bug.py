#!/usr/bin/env python

import re,time,datetime
import BeautifulSoup as bs
import urllib2

_URLTIMEOUT = 20

def test_one_log():
    """ A function invoked when Bug.py is run on command line to test
    whether a particular log matches any of the bugs """
    import sys
    assert len(sys.argv)==2,'USAGE: %s http://url/to/logfile.dat'%sys.argv[0]
    bugs = BugTracker()
    bugs.prefill()
    m = None
    m =  bugs.match(urllib2.urlopen(sys.argv[1]).read(),ref_mismatch=False)
    if not m:
        m =  bugs.match(urllib2.urlopen(sys.argv[1]).read(),ref_mismatch=True)
    if m:
        print 'Matched: ',m.id,m.url()
        print 'Title:',m.fetch_metadata()
        print 'Metadata:',m.author,m.date,m.status,m.open,m.assigned
        print 'Metadata:',m.category,m.severity,m.priority
    else:
        print 'No match!'

class Bug:
    """ One bug """
    _urlpat = 'https://savannah.cern.ch/bugs/index.php?%d'
    def __init__(s,id):
        s.id = int(id)
        s.patterngroups = []
        s.fetched = False
        s.title = None
        s.author = None
        s.date = None
        s.status = None
        s.open = None
        s.assigned = None
        s.category = None
        s.severity = None
        s.priority = None
        s.seen = False
        s.nseen = 0    # counter
        s.new = False
        s.cat = 0  # 0 = only match errors, 1 = only match warnings, 2 = match both
    def _urlopen(s,url):
        """ Since Savannah is sometimes unstable, we sometimes need to try several times """
        for itry in xrange(5):
            try:
                b = urllib2.urlopen(url,timeout=_URLTIMEOUT)
                return b
            except:
                print 'WARNING: cannot access Savannah url:\n  %s'%(url)
                time.sleep(itry*2+1)
                continue
        return None
    def is_closed(s):
        """ True if the bug metadata shows the bug has been marked as Closed on Savannah (may wanna reopen it!)"""
        if not s.fetched:
            s.fetch_metadata()
        return s.open == 'Closed'
    def is_wontfix(s):
        """ True if the bug metadata shows the bug has been marked as Wont fix on Savannah"""
        if not s.fetched:
            s.fetch_metadata()
        return s.status == 'Wont Fix'
    def fetch_metadata(s):
        """ Do on-the-fly lookup of the bug title and other metadata from the bug tracker """
        NOTITLE = 'CANNOT FETCH TITLE FOR BUG %d'%(s.id)
        if not s.fetched and s.id>0:
            b = s._urlopen(s.url())
            soup = bs.BeautifulSoup(b) if b else None
            # get bug title
            if not s.title:
                title = NOTITLE
                try:
                    title = str((soup.findAll('h2')[1]).contents[1])
                    if title[0:2]==': ':
                        title = title[2:]
                except:
                    title = NOTITLE
            s.title = title if s.title==None else s.title
            # try to get bug status, author, date etc.
            # CAREFUL: this parsing code may need to be updated if anything changes with Savannah!
            try:
                meta = soup.findAll('table')[0]
                for itr in meta.findAll("tr"):
                    if len(itr)==7:    # header - bug author and date
                        if itr.find("a"):
                            s.author = str(itr.find("a").contents[0])   #Jordan S Webster &lt;jwebster&gt;
                        elif len(itr.findAll("td"))==3:
                            dt = str(itr.findAll("td")[1].contents[0])  #2012-06-27 20:19
                            s.date = datetime.datetime.strptime(dt, "%Y-%m-%d %H:%M")
                        pass
                    elif len(itr)==5 and len(itr.findAll("td"))==4:     # meat of the table
                        tds = itr.findAll("td")
                        for itd in (0,2):   # loop over two super-columns of attributes
                            if len(tds[itd].findAll("span"))==2:
                                att = str(tds[itd].span.span.contents[0])
                                val = str(tds[itd+1].contents[0]) if len(tds[itd+1].contents)>0 else None
                                if att == 'Status:':
                                    s.status = val
                                elif att == 'Open/Closed:':
                                    s.open = val
                                elif att == 'Category:':
                                    s.category = val
                                elif att == 'Assigned to:':
                                    if len(tds[itd+1].findAll("a"))>0: # remove <a href>, if bug is actually assigned
                                        s.assigned = str(tds[itd+1].contents[0].contents[0]) if len(tds[itd+1].contents)>0 else None
                                    else:
                                        s.category = val
                                elif att == 'Severity:':
                                    s.severity = val
                                elif att == 'Priority:':
                                    s.priority = val
                    else:
                        continue
            except:
                print 'WARNING: unable to retrieve detailed metadata from Savannah for bug',s.id
                pass
            s.fetched = True
        return s.title
    def match(s,log):
        """ Returns True if the patterns for this bug match a given log 
        Each pattern group offers an alternative way to match a bug (logical-OR)
        Within a group, all patterns must match simultaneously (logical-AND)
        """
        for patterns in s.patterngroups:
            nmatches = 0
            for pattern in patterns:
                if re.search(pattern,log):
                    nmatches += 1
            if nmatches == len(patterns):
                s.seen = True
                s.nseen += 1
                return True
        return False
    def add_patterngroup(s,pattern):
        """ Adds a pattern or a list of patterns to a pattern group
        Each group offers an alternative way to match a bug (logical-OR)
        Within a group, all patterns must match simultaneously (logical-AND)
        """
        if isinstance(pattern,list):
            s.patterngroups.append(pattern)
        else:
            s.patterngroups.append([pattern,])
    def set_title(s,title=None):
        if title:
            s.title = title
    def url(s):
        return s._urlpat%s.id

class BugTracker:
    """ A local mini bugtracker to quickly look up common bugs """
    def __init__(s):
        s.bugs = []
        s.unknown = 0
    def add_unknown(s):
        s.unknown += 1
    def match(s,log,ref_mismatch=False):
        """ Require that all patterns match. Matching is done bottom-up (i.e. newest bugs are matched first) """
        #print log
        for bug in reversed(s.bugs):
            if ref_mismatch and bug.cat not in (1,2): continue
            if not ref_mismatch and not bug.cat in (0,2): continue
            if bug.match(log):
                return bug
        return None
    def new_bugs(s):
        """ Returns all bugs labeled as 'new' - i.e., newly created bug reports """
        return [bug for bug in s.bugs if bug.new==True]
    def seen_bugs(s):
        """ Returns all bugs labeled as 'new' - i.e., newly created bug reports """
        return [bug for bug in s.bugs if bug.seen==True]
    def new_seen_bugs(s):
        """ Returns all bugs labeled as 'new' - i.e., newly created bug reports """
        return [bug for bug in s.bugs if bug.new==True and bug.seen==True]
    def summarize_bugs(s):
        """ A raw-text summary of all triggered bugs in this invocation of the script """
        _LINEWIDTH = 70
        sbugs = sorted( [bug for bug in s.bugs if bug.seen==True], key=lambda bug: bug.nseen , reverse = True)
        print ''
        if s.unknown>0:
            print '='*_LINEWIDTH
            print 'NUMBER OF UNKNOWN BUGS THAT NEED ATTENTION:',s.unknown
        if len(sbugs)>0:
            print '='*_LINEWIDTH
            print 'QUICK SUMMARY OF ALL IDENTIFIED BUGS:'
            for bug in sbugs:
                com = bug.fetch_metadata()
                com2 = com[:_LINEWIDTH]
                print '(%d)'%bug.nseen,bug.id,com2 if len(com)==len(com2) else com2+'...'
            print '='*_LINEWIDTH
    def add(s,bugid,pattern,title=None,new=False,cat=0):
        """ Use this function to add pre-filled (aka known) bugs """
        old = [bug for bug in s.bugs if bug.id == bugid]
        bug = None
        if len(old)==0:
            bug = Bug(bugid)
            bug.add_patterngroup(pattern)
            bug.set_title(title)
            bug.new = new
            bug.cat = cat
            s.bugs.append( bug )
        elif len(old)==1:
            bug = old[0]
            bug.add_patterngroup(pattern)
            bug.new = new
            bug.cat = cat
            if bug.title != title:
                #print 'WARNING: encountered different bug titles for the same bug id = %d'%bugid
                pass
            bug.set_title(title)
        else:
            assert False,'Severe failure in bug grouping functionality; please contact a developer'
    def add_new(s,bugid,pattern,title=None,cat=0):
        """ Use this function to add new bugs in run.py - these will be reported separately at the top of the shift report """
        s.add(bugid,pattern,title,new=True,cat=cat)
    def prefill_genpurpose(s):
        """ General failure conditions """
        #s.add(-1, 'CRITICAL stopped by user interrupt','User interrupt',cat=2)
        #s.add(-1, 'KeyboardInterrupt','User interrupt',cat=2)
        s.add(-2, 'APPLICATION_DIED_UNEXPECTEDLY','Worker process failed',cat=2)
        s.add(-3, 'received fatal signal 15','Job recieved SIGTERM signal',cat=2)
        s.add(-3, ['Signal handler: Killing','with 15'],'Job recieved SIGTERM signal',cat=2)
        s.add(-4, ["No such file or directory", "Py:inputFilePeeker   ERROR Unable to build inputFileSummary from any of the specified input files"],'Input files not available, usually due to upstream job failure.',cat=2)
        s.add(-5,["Error accessing path/file for root://eosatlas//eos/atlas/atlascerngroupdisk/trig-daq/validation/test_data/"],"EOS problem OR file does not exist") 
        s.add(-5,["ERROR fail to open file root://eosatlas//eos/atlas/atlascerngroupdisk/"],"EOS problem OR file does not exist")
        s.add(-5,["ERROR Unable to open ROOT file \"root://eosatlas//eos/atlas/atlascerngroupdisk"],"EOS problem OR file does not exist")
        s.add(-5,["ESLOriginalFile reported: File end record not found in file"],"Failed to read end of file, most likely a transient problem, submit bug if persists. ")
        s.add(-5,["Error in <TXNetSystem::Connect>: some severe error occurred while opening the connection at root://eosatlas//eos/"],"Failed to open eos file, most likely a transient problem, submit bug if persists. ")

    def prefill_nicos(s):
        """ Special bugs that are only picked up by NICOS - and are not present in the ATN summary page """
        s.add(97313,["AllPT_physicsV4.reference.new: No such file or directory"]) #LT 9/6 PT/MT
        s.add(97313,["cat: ../AllMT_physicsV4/AllMT_physicsV4.reference.new: No such file or directory"])
        s.add(97356,["If this change is understood, please update the reference fileby typing:","cp AthenaRDO_MC_pp_v2_loose_mc_prescale_top_EF.TrigChainMoniValidation.reference.new /afs/cern.ch/atlas/project/trigger/pesa-sw/validation/references/ATN/REG/17.1.X.Y/20120808/AthenaRDO_MC_pp_v2_loose_mc_prescale_top_EF.TrigChainMoniValidation.reference"])#LT 9/8
        s.add(-6, ['NICOS NOTICE: POSSIBLE FAILURE \(ERROR\) : LOGFILE LARGE and TRUNCATED'],title='NICOS: LOGFILE TRUNCATED',cat=2) # this shows up often, so match if last
        s.add(94697,['href="#prblm"\>ls: \*rel_\[0-6\].data.xml: No such file or directory'],'NICOS HARMLESS WARNING: missing *rel_[0-6].data.xml')
        s.add(94970,['href="#prblm"\>python: can\'t open file \'checkFileTrigSize_RTT.py\''],'NICOS HARMLESS WARNING: cannot find checkFileTrigSize_RTT.py')
        s.add(94775,['href="#prblm"\>sh: voms-proxy-info: command not found'],'NICOS HARMLESS WARNING: voms-proxy-info command not found')
        if False: # missing references
            s.add(-5, ['\.reference: No such file or directory','wc:','old/reference'],'NICOS: MISSING REFERENCE FILE')
            s.add(-5, ['\.reference: No such file or directory\</A\>\<BR\>'],'NICOS: MISSING REFERENCE FILE')
            s.add(-5, ['\.reference: No such file or directory','wc:','checkcounts test warning: Unable to open reference'],'NICOS: MISSING REFERENCE FILE')
        else:
            s.add(96295,[".reference: No such file or directory","nightly 17.2.X.Y-VAL-Prod/"])
            s.add(96296,[".reference: No such file or directory","nightly 17.2.X/"])
            s.add(96297,[".reference: No such file or directory","nightly 17.2.X-VAL/"])
        if True: # reference count mismatch - only matched if a test is a WARNING but not an ERROR
            # REFERENCE BUGS
            s.add(-96332,["nightlies/17.1.X.Y-VAL-P1HLT/","ATHENA_REGTEST_FAILED \(64\) ROOTCOMP_MISMATCH \(4\)"],title = "WARNING Output differs from reference: don't report in Savannah per Roger's request", cat=1)
            s.add(-96332,["nightlies/17.1.X.Y-VAL-P1HLT/","WARNING Output differs from reference for","If this change is understood, please update"],title = "WARNING Output differs from reference: don't report in Savannah per Roger's request",cat=1)
            s.add(-96333,["nightlies/17.1.X.Y.Z-VAL-AtlasCAFHLT/","ATHENA_REGTEST_FAILED \(64\) ROOTCOMP_MISMATCH \(4\)"],title = "WARNING Output differs from reference: don't report in Savannah per Roger's request",cat=1)
            s.add(-96333,["nightlies/17.1.X.Y.Z-VAL-AtlasCAFHLT/","WARNING Output differs from reference for","If this change is understood, please update"],title = "WARNING Output differs from reference: don't report in Savannah per Roger's request",cat=1)
            s.add(-96334,["nightlies/17.2.X.Y-VAL-Prod/","ATHENA_REGTEST_FAILED \(64\) ROOTCOMP_MISMATCH \(4\)"],title = "WARNING Output differs from reference: don't report in Savannah per Roger's request",cat=1)
            s.add(-96334,["nightlies/17.2.X.Y-VAL-Prod/","WARNING Output differs from reference for","If this change is understood, please update"],title = "WARNING Output differs from reference: don't report in Savannah per Roger's request",cat=1)
            s.add(-96335,["nightlies/17.1.X/","ATHENA_REGTEST_FAILED \(64\) ROOTCOMP_MISMATCH \(4\)"],title = "WARNING Output differs from reference: don't report in Savannah per Roger's request",cat=1)
            s.add(-96335,["nightlies/17.1.X/","WARNING Output differs from reference for","If this change is understood, please update"],title = "WARNING Output differs from reference: don't report in Savannah per Roger's request",cat=1)
            s.add(-96336,["nightlies/17.1.X-VAL/","ATHENA_REGTEST_FAILED \(64\) ROOTCOMP_MISMATCH \(4\)"],title = "WARNING Output differs from reference: don't report in Savannah per Roger's request",cat=1)
            s.add(-96336,["nightlies/17.1.X-VAL/","WARNING Output differs from reference for","If this change is understood, please update"],title = "WARNING Output differs from reference: don't report in Savannah per Roger's request",cat=1)
            s.add(-96337,["nightlies/17.2.X/","ATHENA_REGTEST_FAILED \(64\) ROOTCOMP_MISMATCH \(4\)"],title = "WARNING Output differs from reference: don't report in Savannah per Roger's request",cat=1)
            s.add(-96337,["nightlies/17.2.X/","WARNING Output differs from reference for","If this change is understood, please update"],title = "WARNING Output differs from reference: don't report in Savannah per Roger's request",cat=1)
            s.add(-96338,["nightlies/17.2.X-VAL/","ATHENA_REGTEST_FAILED \(64\) ROOTCOMP_MISMATCH \(4\)"],title = "WARNING Output differs from reference: don't report in Savannah per Roger's request",cat=1)
            s.add(-96338,["nightlies/17.2.X-VAL/","WARNING Output differs from reference for","If this change is understood, please update"],title = "WARNING Output differs from reference: don't report in Savannah per Roger's request",cat=1)
            s.add(-96339,["nightlies/18.X.0/","ATHENA_REGTEST_FAILED \(64\) ROOTCOMP_MISMATCH \(4\)"],title = "WARNING Output differs from reference: don't report in Savannah per Roger's request",cat=1)
            s.add(-96339,["nightlies/18.X.0/","WARNING Output differs from reference for","If this change is understood, please update"],title = "WARNING Output differs from reference: don't report in Savannah per Roger's request",cat=1)
            s.add(-96340,["nightlies/18.X.0-VAL/","ATHENA_REGTEST_FAILED \(64\) ROOTCOMP_MISMATCH \(4\)"],title = "WARNING Output differs from reference: don't report in Savannah per Roger's request",cat=1)
            s.add(-96340,["nightlies/18.X.0-VAL/","WARNING Output differs from reference for","If this change is understood, please update"],title = "WARNING Output differs from reference: don't report in Savannah per Roger's request",cat=1)
            s.add(-96339,["nightlies/17.X.0/","ATHENA_REGTEST_FAILED \(64\) ROOTCOMP_MISMATCH \(4\)"],title = "WARNING Output differs from reference: don't report in Savannah per Roger's request",cat=1)
            s.add(-96339,["nightlies/17.X.0/","WARNING Output differs from reference for","If this change is understood, please update"],title = "WARNING Output differs from reference: don't report in Savannah per Roger's request",cat=1)
            s.add(-96340,["nightlies/17.X.0-VAL/","ATHENA_REGTEST_FAILED \(64\) ROOTCOMP_MISMATCH \(4\)"],title = "WARNING Output differs from reference: don't report in Savannah per Roger's request",cat=1)
            s.add(-96340,["nightlies/17.X.0-VAL/","WARNING Output differs from reference for","If this change is understood, please update"],title = "WARNING Output differs from reference: don't report in Savannah per Roger's request",cat=1)
            s.add(-96341,["nightlies/17.1.X.Y-VAL2-P1HLT/","ATHENA_REGTEST_FAILED \(64\) ROOTCOMP_MISMATCH \(4\)"],title = "WARNING Output differs from reference: don't report in Savannah per Roger's request",cat=1)
            s.add(-96341,["nightlies/17.1.X.Y-VAL2-P1HLT/","WARNING Output differs from reference for","If this change is understood, please update"],title = "WARNING Output differs from reference: don't report in Savannah per Roger's request",cat=2)
            s.add(-96342,["nightlies/17.1.X.Y.Z-VAL2-AtlasCAFHLT/","ATHENA_REGTEST_FAILED \(64\) ROOTCOMP_MISMATCH \(4\)"],title = "WARNING Output differs from reference: don't report in Savannah per Roger's request",cat=1)
            s.add(-96342,["nightlies/17.1.X.Y.Z-VAL2-AtlasCAFHLT/","WARNING Output differs from reference for","If this change is understood, please update"],title = "WARNING Output differs from reference: don't report in Savannah per Roger's request",cat=1)
            # TIME QUOTA BUGS
            s.add(-7,["test killed as time quota spent, test warning is issued"],title="ATTENTION: add a TIME QUOTA BUG match string in Bug.py::prefill_nicos for this test and release - but ONLY if it recurs",cat=2) # HAS to be above other time quota strings - this is a "catch-all" case
            s.add(96366,["AthenaTrigRDO_MC_pp_v2_loose_mc_prescale","nightlies/17.1.X.Y-VAL-P1HLT/","test killed as time quota spent, test warning is issued"],cat=2)
            s.add(96540,["AthenaTrigRDO_MC_pp_v4","mc_prescale","nightlies/17.1.X.Y-VAL-P1HLT/","test killed as time quota spent, test warning is issued"],cat=2)
            s.add(96542,["AthenaTrigRDO_MC_pp_v4","mc_prescale","nightlies/17.1.X/","test killed as time quota spent, test warning is issued"],cat=2)
            s.add(96543,["AthenaTrigRDO_MC_pp_v4","mc_prescale","nightlies/17.1.X-VAL/","test killed as time quota spent, test warning is issued"],cat=2)
            s.add(96546,["AllPT_MC_run_stop_run","nightlies/17.2.X/","test killed as time quota spent, test warning is issued"],cat=2)
            s.add(96547,["AllPT_MC_run_stop_run","nightlies/17.2.X-VAL/","test killed as time quota spent, test warning is issued"],cat=2)
            s.add(96568,["AllPT_HIV2_run_stop_run","nightlies/17.1.X.Y.Z-VAL-AtlasCAFHLT/","test killed as time quota spent, test warning is issued"],cat=2)
            s.add(96574,["AllPartition_physicsV4","nightlies/17.1.X.Y-VAL2-P1HLT/","test killed as time quota spent, test warning is issued"],cat=2)
            s.add(96575,["AthenaTrigRDO_MC_pp","_mc_prescale","nightlies/17.1.X.Y-VAL2-P1HLT/","test killed as time quota spent, test warning is issued"],cat=2)
            s.add(96576,["AllPT_HIV2_run_stop_run","nightlies/17.1.X.Y.Z-VAL2-AtlasCAFHLT/","test killed as time quota spent, test warning is issued"],cat=2)
            s.add(96602,["AllPartition_physicsV4","nightlies/17.1.X/","test killed as time quota spent, test warning is issued"],cat=2)
            s.add(96635,["AllPT_HIV2_run_stop_run","nightlies/17.1.X.Y-VAL2-P1HLT/","test killed as time quota spent, test warning is issued"],cat=2)
            s.add(96714,["AthenaTrigRDO_MC_pp_v4","mc_prescale","nightlies/17.1.X.Y.Z-VAL-AtlasCAFHLT/","test killed as time quota spent, test warning is issued"],cat=2)
            s.add(96882,["AthenaTrigRDO_MC_pp_v4_loose_mc_prescale","nightlies/17.1.X.Y.Z-VAL2-AtlasCAFHLT/","test killed as time quota spent, test warning is issued"],cat=2)
            s.add(97057,["AthenaTrigRDO_MC_pp_v2_loose_mc_prescale","nightlies/17.1.X.Y.Z-VAL2-AtlasCAFHLT/","test killed as time quota spent, test warning is issued"],cat=2)
            s.add(97531,["AthenaTrigRDO_blackholes","nightlies/17.2.X.Y-VAL-Prod/","test killed as time quota spent, test warning is issued"],cat=2)
            s.add(97532,["AllMT_HIV2","nightlies/17.2.X/","test killed as time quota spent, test warning is issued"],cat=2)
            s.add(97532,["AllMT_HIV2","nightlies/17.2.X-VAL/","test killed as time quota spent, test warning is issued"],cat=2)
            s.add(97532,["AllMT_HIV2_menu","nightlies/17.2.X/","test killed as time quota spent, test warning is issued"],cat=2) 
            s.add(97532,["AllMT_HIV2_menu","nightlies/17.2.X-VAL/","test killed as time quota spent, test warning is issued"],cat=2) 
            s.add(97547,["AthenaTrigRDO_MC_pp_v4_tight_mc_prescale","nightlies/17.1.X.Y.Z-VAL2-AtlasCAFHLT/","test killed as time quota spent, test warning is issued"],cat=2)
            s.add(97654,["BackCompAthenaTrigBStoESDAOD","nightlies/17.2.X.Y-VAL-Prod/","test killed as time quota spent, test warning is issued"],cat=2)
            s.add(98691,["AllPT_mcV4","nightlies/17.1.X/","test killed as time quota spent, test warning is issued"],cat=2)
            s.add(98691,["AllPT_mcV4","nightlies/17.1.X-VAL/","test killed as time quota spent, test warning is issued"],cat=2)
            s.add(98771,["AthenaTrigAOD_TrigEDMCheck_fixedAOD","nightlies/17.1.X-VAL/","test killed as time quota spent, test warning is issued"],cat=2)
            # TOLERANCE BUGS
            s.add(-8,"checkcounts test warning : trigger counts outside tolerance:",title="ATTENTION: add a TOLERANCE BUG match string in Bug.py::prefill_nicos for this release",cat=1) #HAS to be above other tolerance  strings - this is a "catch-all" case
            s.add(-96368,["checkcounts test warning : trigger counts outside tolerance:","nightlies/17.1.X.Y-VAL-P1HLT/"],title="count mismatch warnings:bona fide bugs but don't report in Savannah per Roger's request",cat=1)
            s.add(-96399,["checkcounts test warning : trigger counts outside tolerance:","nightlies/17.1.X.Y.Z-VAL-AtlasCAFHLT/"],title="count mismatch warnings:bona fide bugs but don't report in Savannah per Roger's request",cat=1)
            s.add(-96401,["checkcounts test warning : trigger counts outside tolerance:","nightlies/17.2.X.Y-VAL-Prod/"],title="count mismatch warnings:bona fide bugs but don't report in Savannah per Roger's request",cat=1)
            s.add(-96402,["checkcounts test warning : trigger counts outside tolerance:","nightlies/17.1.X/"],title="count mismatch warnings:bona fide bugs but don't report in Savannah per Roger's request",cat=1)
            s.add(-96403,["checkcounts test warning : trigger counts outside tolerance:","nightlies/17.1.X-VAL/"],title="count mismatch warnings:bona fide bugs but don't report in Savannah per Roger's request",cat=1)
            s.add(-96404,["checkcounts test warning : trigger counts outside tolerance:","nightlies/17.2.X-VAL/"],title="count mismatch warnings:bona fide bugs but don't report in Savannah per Roger's request",cat=1)
            s.add(-96405,["checkcounts test warning : trigger counts outside tolerance:","nightlies/18.X.0/"],title="count mismatch warnings:bona fide bugs but don't report in Savannah per Roger's request",cat=1)
            s.add(-96406,["checkcounts test warning : trigger counts outside tolerance:","nightlies/18.X.0-VAL/"],title="count mismatch warnings:bona fide bugs but don't report in Savannah per Roger's request",cat=2)
            s.add(-96405,["checkcounts test warning : trigger counts outside tolerance:","nightlies/17.X.0/"],title="count mismatch warnings:bona fide bugs but don't report in Savannah per Roger's request",cat=1)
            s.add(-96406,["checkcounts test warning : trigger counts outside tolerance:","nightlies/17.X.0-VAL/"],title="count mismatch warnings:bona fide bugs but don't report in Savannah per Roger's request",cat=2)
            s.add(-96407,["checkcounts test warning : trigger counts outside tolerance:","nightlies/17.1.X.Y-VAL2-P1HLT/"],title="count mismatch warnings:bona fide bugs but don't report in Savannah per Roger's request",cat=1)
            s.add(-96408,["checkcounts test warning : trigger counts outside tolerance:","nightlies/17.1.X.Y.Z-VAL2-AtlasCAFHLT/"],title="count mismatch warnings:bona fide bugs but don't report in Savannah per Roger's request",cat=1)
            s.add(-96420,["checkcounts test warning : trigger counts outside tolerance:","nightlies/17.2.X/"],title="count mismatch warnings:bona fide bugs but don't report in Savannah per Roger's request",cat=1)
            # CHECKCOUNT MISSING REFERENCE BUGS
            s.add(-9,["checkcounts test warning: Unable to open reference file",".root"],title='ATTENTION: add a CHECKCOUNTS BUG match string in Bug.py::prefill_nicos for this release',cat=1) #HAS to be above other checkcounts strings - this is a "catch-all" case
            s.add(96372,["checkcounts test warning: Unable to open reference file","nightlies/17.1.X.Y.Z-VAL-AtlasCAFHLT/",".root"],cat=1)
            s.add(96392,["checkcounts test warning: Unable to open reference file","nightlies/17.2.X-VAL/",".root"],cat=1)
            s.add(96393,["checkcounts test warning: Unable to open reference file","nightlies/17.2.X/",".root"],cat=1)
            s.add(96397,["checkcounts test warning: Unable to open reference file","nightlies/17.1.X/",".root"],cat=1)
            s.add(96398,["checkcounts test warning: Unable to open reference file","nightlies/17.1.X.Y.Z-VAL2-AtlasCAFHLT/",".root"],cat=1)
            s.add(96494,["checkcounts test warning: Unable to open reference file","nightlies/17.1.X-VAL/",".root"],cat=1)
            s.add(96496,["checkcounts test warning: Unable to open reference file","nightlies/17.1.X.Y-VAL2-P1HLT/",".root"],cat=1)
            s.add(96715,["checkcounts test warning: Unable to open reference file","nightlies/17.1.X.Y-VAL-P1HLT/",".root"],cat=1)

    def prefill(s):
        """ 
        Note that bugs will be matched bottom-up. That is, newer bugs should be put at the bottom and will get matched first
        s.add(,'')
        s.add(,['',''])
        """
        s.prefill_nicos()
        s.prefill_genpurpose()
        s.add(86562,['ERROR preLoadFolder failed for folder /Digitization/Parameters','FATAL DetectorStore service not found']) #note from LT on Sept 6--still a valid bug, although very old.
        # At some point, someone asked for a new bug report for the above bug -- if they complain again, you could use the line below
        #s.add(95595,['ERROR preLoadFolder failed for folder /Digitization/Parameters','FATAL DetectorStore service not found'])
        s.add(88042,["\[is::repository_var is::server::resolve\(...\) at is/src/server.cc:31\] IS repository 'Histogramming-EF-Segment-1-1-iss' does not exist"])
        s.add(88042,["\[is::repository_var is::server::resolve\(...\) at is/src/server.cc:31\] IS repository 'Histogramming-L2-Segment-1-1-iss' does not exist"])
        s.add(88042,['\[ipc::_objref_partition\* ipc::util::getPartition\(...\) at ipc/src/util.cc:273\] Partition "athena_mon" does not exist'])
        s.add(88042,["IS repository 'Histogramming-EF-Segment-1-1-iss' does not exist",'Partition "athena_mon" does not exist'])
        s.add(88554,['Moving to AthenaTrigRDO_chainOrder_compare','differences in tests with ordered HLT chain execution','TrigSteer_EF.TrigChainMoniValidation'])
        s.add(90593,['ERROR ServiceLocatorHelper::createService: wrong interface id IID_3596816672 for service JobIDSvc','Root+python problem when reading ESDs'])
        s.add(92206,['FATAL: Failed to start local PMG server',"RunManager instance has no attribute 'root_controller'"])
        s.add(92206,['FATAL: Failed to start RM server',"RunManager instance has no attribute 'root_controller'"])
        s.add(92213,'could not bind handle to CondAttrListCollection to key: /TRT/Onl/ROD/Compress','InDetTRTRodDecoder callback registration failed, but Athena job completes successfully')
        s.add(94142,"/src/MeasuredAtaStraightLine.cxx:108")
        s.add(92615,["WARNING Chain L2_2mu4T_DiMu_l2muonSA aborting with error code ABORT_CHAIN UNKNOWN"])
        s.add(92632,"message=inputBSFile=link_to_file_from_P1HLT.data: link_to_file_from_P1HLT.data not found")
        s.add(92680,['ERROR IN CHAIN: EF Chain counter 414 used 2 times while can only once, will print them all'])
        s.add(95540,['ERROR IN CHAIN: EF Chain counter 2001 used 2 times while can only once, will print them all'])
        s.add(92719,["Trigger menu inconsistent, aborting","Available HLT counter","TrigSteering/pureSteering_menu.py"])
        s.add(92734,["TrigConfConsistencyChecker","ERROR SAX error while parsing exceptions xml file, line 43, column 13"],'SAX error while parsing exceptions xml file')
        s.add(92757,["chain L2_g100_etcut_g50_etcut with has no matching LVL1 item L1_2EM14L1_2EM14",'Trigger menu inconsistent, aborting'])
        s.add(92814,["Unable to initialize Algorithm TrigSteer_L2",'ERROR Configuration error','T2IDTauHypo_tau',])
        s.add(92994,["Py:LArCalibMenu",'ERROR template chain with sig_id=g15_loose is not defined at level EF'])
        s.add(93195,["ERROR","No conversion CscRDO to stream","Could not create Rep for DataObject"])
        s.add(93505,["ERROR Problems calling Blob2ToolConstants"])
        s.add(93534,["RootController is in faulty state because: Application","ROS","has a problem that cannot be ignored","ERROR transition failed"])
        s.add(93633,["IncludeError: include file CaloRecEx/CaloRecOutputItemList_jobOptions.py can not be found"])
        s.add(93740,["IncludeError: include file InDetPriVxCBNT/InDetPriVxCBNT_jobOptions.py can not be found"])
        s.add(93741,["ERROR Unable to build inputFileSummary from any of the specified input files","TimeoutError","KeyError: 'eventdata_itemsDic'"])
        s.add(93886,'At least one of the jobs \(ascending/descending chain counter\) has not been completed\! Exit.')
        s.add(93897,['LArL2ROBListWriter_j10_empty_larcalib','L1CaloTileHackL2ROBListWriter_j10_empty_larcalib','ERROR Could not find RoI descriptor - labels checked : TrigT2CaloEgamma initialRoI'])
        s.add(93990,["TriggerMenuSQLite","sqlite' file is NOT found in DATAPATH, exiting"],"NB: This is usually due to a build error in Trigger XML")
        s.add(94033,["ATLAS_DBA.LOGON_AUDIT_TRIGGER' is invalid and failed re-validation"])
        s.add(94084,["LVL1CTP::CTPSLink::getCTPToRoIBWords","Current algorithm: RoIBuilder"])
        s.add(96606,["ToolSvc.TrigTSerializer","MuonFeatureContainer_p3","ERROR Errors while decoding"])
        s.add(94095,["ERROR no handler for tech","FileMgr"])
        s.add(94016,["No such file or directory:","'HLTconfig_MC_pp_v4_loose_mc_prescale","xml'"])
        s.add(94173,["Py:TriggerPythonConfig","ERROR Chain L2_je255 defined 2 times with 2 variants"])
        s.add(94185,"ImportError: No module named egammaD3PDAnalysisConf")
        s.add(95610,["ERROR poolToObject: Could not get object for Token","ConditionsContainerTRTCond::StrawStatusContainerTemplate"])
        s.add(94192,["Non identical keys found. See diff_smk_","l2_diff.txt and ef_diff.txt","L2SecVtx_JetB.TrigInDetVxInJetTool.VertexFitterTool"])
        s.add(94261,"IncludeError: include file MuonTrkPhysMonitoring/MuonTrkPhysDQA_options.py can not be found")
        s.add(94342,["TrigMuonEFTrackBuilderConfig_SeededFS","Core dump from CoreDumpSvc","Caught signal 11\(Segmentation fault\)"])
        s.add(94435,["ES_WrongFileFormat: file is of no know format. Abort.EventStorage reading problem: file is of no know format. Abort.","virtual EventStackLayer"])
        s.add(97056,["RuntimeError: key 'outputNTUP_TRIGFile' is not defined in ConfigDic"])
        s.add(94611,['Current algorithm: MuGirl','msFit ../src/GlobalFitTool.cxx:571'])
        s.add(94734,['\[TObject\* histmon::THistRegisterImpl::HInfo::get\(...\) at histmon/src/THistRegisterImpl.cxx:310\] Histograms registered with the id "/EXPERT/','CutCounter" are not compatible for the merge operation'])
        s.add(94873,['Last incident: AthenaEventLoopMgr:BeginEvent','Current algorithm: TrigEDMChecker','diff ../src/TrigPhoton.cxx:225'])
        s.add(94765,['Muonboy/digitu ERROR of MDT/CSC station Off','which has digits'])
        s.add(95024,['segmentation violation','TrigDiMuonFast::makeMDT\(Candidate'])
        s.add(95069,['Muonboy/digitu ERROR of MDT/CSC station Off','which has hits'])
        s.add(95115,['in TrigConfChain::TrigConfChain','TrigMonitoringEvent/TrigMonitoringEvent/TrigConfChain.h:28'])
        s.add(95115,['Trig::FillConf::FillLV1','TrigMonitoringEvent/TrigMonConfig.icc:163'])
        s.add(95116,['in TrigCostTool::\~TrigCostTool','in TrigMonConfig::\~TrigMonConfig'])
        s.add(95116,['TrigSteer_L2','FATAL in sysStart\(\): standard std::exception is caught','ERROR std::bad_alloc'])
        s.add(95141,["RuntimeError: RootController is in faulty state because:","Application 'L2-Segment-1:voatlas62' has a problem that cannot be ignored"])
        s.add(92598,['corrupted unsorted chunks','AllPT_HI_menu'])
        s.add(95281,["ToolSvc.InDetTrigPrdAssociationTool","ERROR track already found in cache"])
        s.add(95605,["ERROR could not get handle to TrigEgammaPhotonCutIDTool","ValueError:"])
        s.add(95607,["Reconstruction/egamma/egammaPIDTools/cmt/../src/egammaPhotonCutIDTool.cxx:591"])
        s.add(95622,["RuntimeError: RootController did not exit in 60 seconds","Timeout reached waiting for transition to BOOTED"])
        s.add(95623,["ERROR Errors while decoding TrigElectronContainer_p3","WARNING: no directory and/or release sturucture found"])
        s.add(95640,["IOVSvcTool::preLoadProxies \(this=0x1e486a00\) at ../src/IOVSvcTool.cxx:986"])
        s.add(95657,["ValueError:  Physics_HI_v2 is not the expected type and/or the value is not allowed for: JobProperties.Rec.Trigger.triggerMenuSetup"])
        s.add(95692,["Waiting for ManyPropagableCommand to finish:  99/100 seconds","if ret != 0 and ret != 5: raise PropagationException"])
        s.add(95732,["HLTMenu_frontier.xml: No such file or directory","HLT menus are not identical"])
        s.add(95855,"UploadHIV2MenuKeys/exportMenuKeys.sh: No such file or directory")
        s.add(95948,["in HistorySvc::listProperties","psc::Psc::pscStopRun","at ../src/Psc.cxx:692"])
        s.add(95965,["in TEmulatedCollectionProxy::InitializeEx","in TEmulatedMapProxy::TEmulatedMapProxy"])
        s.add(96606,["Errors while decoding TrigInDetTrackCollection_tlp2"," any further ROOT messages for this class will be suppressed"])
        s.add(95986,["/src/rbmaga.F:82","/src/setmagfield.F:52"])
        s.add(95995,["Trigger menu inconsistent, aborting","L2 Chain counter 454 used 2 times while can only once, will print them all"])
        s.add(96093,["ByteStreamAttListMetadataSvc","not locate service"])
        s.add(96097,["SEVERE: Caught SQL error: ORA-02290: check constraint \(ATLAS_TRIGGER_ATN.TW_ID_NN\) violated","SEVERE:  Database is already locked by ATLAS_TRIGGER_ATN_W"]) # the bug is found in uploadSMK.log
        s.add(96112,"ImportError: No module named AthenaServicesConf")
        #s.add(96117,"JobTransform completed for RAWtoESD with error code 11000 \(exit code 10\)") # the matching statements can be found in log/nicos, but the exact error msg is found in RAWtoESD.log. TODO: if this shows up again, modify Project.py match_bugs to parse RAWtoESD.log  #TOO GENERAL
        s.add(96142,["OBSOLETE WARNING please use RecExCond/RecExCommon_flags.py","Py:AutoConfiguration WARNING Unable to import PrimaryDPDFlags","Py:AutoConfiguration WARNING Primary DPDMake does not support the old naming convention"])
        s.add(96165,["from MuonIsolationTools.MuonIsolationToolsConf import","ImportError: No module named MuonIsolationTools.MuonIsolationToolsConf"])
        s.add(96215,"ImportError: cannot import name CBNTAA_L1CaloPPM")
        s.add(95692,["farmelements.py","if ret != 0 and ret != 5: raise PropagationException\(ret,output\)","PropagationException: return code: 1280"])
        #s.add(96245,["is::repository_var is::server::resolve\(...\) at is/src/server.cc:31","CORBA::Object\* ipc::util::resolve\(...\) at ipc/src/util.cc:369"])
        s.add(96273,["raise IncludeError\( 'include file %s can not be found' % fn \)","IncludeError: include file TrigT1CaloCalibTools/CBNT_L1Calo_jobOptions.py can not be found"])
        s.add(96545,["Errors while decoding TrigL2BphysContainer_tlp1","Can't instantiate precompiled template SG::ELVRef"])
        s.add(96581,["could not bind handle to CondAttrListCollection","/FWD/ALFA/position_calibration"])
        s.add(96639,["Trigger menu inconsistent","Chain counter 4152 used 2 times while can only once"])
        s.add(96660,["test -e ../AllMT_HIV2/AllMT_HIV2-1._0001.data","pre-conditions failed"])
        s.add(96675,["Errors while decoding egammaContainer_p2"])
        s.add(95732,["HLTMenu_frontier.xml: No such file or directory"])
        s.add(97671,["HLTJobLib","ERROR HLTProcess","could not find any files starting 'data1*"]) # was 96683. Duplicate and being folled in this bug report
        s.add(96704,["Errors while decoding MuonFeatureDetailsContainer_p2"])
        s.add(96712,["'InDetGlobalTrackMonTool' object has no attribute 'TrackCollection'"])
        s.add(96718,["ToolSvc","Cannot create tool JetBTaggerTool"])
        s.add(96719,["ToolSvc","Cannot create tool JetTowerNoiseTool"])
        s.add(95812,["TrigTSerializer::serialize","at ../src/TrigTSerializer.cxx:223"])
        s.add(96756,["No module named JetEventAthenaPool","JetEventAthenaPoolConf"],"NB: This bug is usually caused by a build failure in JetEventAthenaPool.  Check NICOS build logs \(see twiki for details\) to see if the build failed.  This BUG is only valid if the build failure is TRANSIENT.  Check if there are specific reasons for build failure.")
        s.add(96756,["WARNING Couldn't retrieve JetKeyDescriptor with key <JetKeyMap> in StoreGate \! Giving up \!"],"NB: This bug is usually caused by a build failure in JetEventAthenaPool.  Check NICOS build logs \(see twiki for details\) to see if the build failed. This BUG is only valid if the build failure is TRANSIENT.  Check if there are specific reasons for build failure.")
        s.add(96720,["ERROR CallBack function","GeoModelSvc","cannot be registered"])
        s.add(96760,["'Histogramming-EF-Segment-0-iss' does not exist"])
        s.add(96354,["Py:AllowedList","xe*","is not in the list of allowed values"])
        s.add(96912,["inputBSFile=data1*","not found","RAWtoESD"])
        s.add(96949,["IOError","No such file or directory","LVL1config_MC_pp_v4_17.1.5.xml"])
        s.add(96987,["Py:runHLT_standalone.py","No trigger menu specified"])
        s.add(96993,["There was a crash","Trk::AtaPlane"])
        s.add(97099,["There was a crash","Trk::TrackSegment"])
        s.add(97122,["Fatal Python error","GC object already tracked"])
        s.add(97165,["ImportError","No module named PanTauAnalysisConf"])
        s.add(97212,["FATAL Loading primary pi0 BDT file","TauDiscriminant.TauPi0BDT"])
        s.add(97303,["TypeError: defineHistogram\(\) got multiple values for keyword argument 'type'","self.AthenaMonTools \+\= \[ MbMbtsFexMonitoring\(\), time\]"]) # LT Sept 6
        s.add(97311,"ERROR  Cannot retrieve Mdt SegmentCollection ConvertedMBoySegments") # LT Sept 6
        s.add(97312,["TH2F::Add:0: RuntimeWarning: Attempt to add histograms with different labels","TrigEgammaRec_NoIDEF_eGamma","TrigSteer_EF","Current algorithm: \<NONE\>"])
        #s.add(96858,["at ../src/TrigLBNHist.cxx:92"])
        s.add(97312,["Current algorithm: TrigDiMuon_FS","Core dump"])
        s.add(97195,["ReferenceError: attempt to access a null-pointer","dh_tree \= handleTFile.Get\(dhTreeName\)"], "This is a transient error due to upstream failures.  Add exception if confirmed by validation coordinators")
        s.add(97314,["'Trig::TrigDecisionToolARA' object has no attribute 'getChainGroup'"]) #LT 9/6
        s.add(97261,"ERROR: ld.so: object '/afs/cern.ch/atlas/offline/external/tcmalloc/google-perftools-0.99.2c/i686-slc5-gcc43-opt/lib/libtcmalloc_minimal.so' from LD_PRELOAD cannot be preloaded: ignored")
        s.add(97298,["ImportError: No module named TrigSteeringTest.TrigSteeringTestConf"])
        s.add(97334,["ImportError: No module named pyAMIErrors"],"Reconstruction Project Error") #LT 9/7
        s.add(97333,["class MCTBEntryHandler\(CfgMgr.Muon__MCTBEntryHandler,ConfiguredBase\)","TypeError: Error when calling the metaclass bases","18.X.0-VAL"], "Reported by Reco SW Validation shifter")
        s.add(97339,["ERROR Errors while decoding TrigT2MbtsBitsContainer_p3 any further ROOT messages for this class"])
        s.add(97355,["getPublicTool\(\"MuonSegmentMerger\"\)","kwargs.setdefault\(\"TriggerHitAssociator\", getPublicToolClone\(\"TriggerHitAssociator\", \"DCMathSegmentMaker\",Redo2DFit=False\)","18.X.0-VAL"])
        s.add(97355,['Error: When merging chains:','EF_mu4T','EF_j10_a4tc_EFFS','these were missing','18.X.0-VAL'])
        s.add(97369,["HLT::TrigSteer::execute","at ../src/TrigSteer.cxx:617"])
        s.add(97374,["IS repository 'Histogramming-L2-Segment-1-1-iss' does not exist","double free or corruption"])
        s.add(97394,["at \.\./src/TrigDiMuonFast.cxx:1414","in TrigDiMuonFast::processTrack"])
        s.add(97685,["UploadHIMenuKeys FAILURE"]) # JK 17/10/12 was 97650 - Duplicate of 97685
        s.add(95848,["no ChainAcceptance_runsummary","AllPT_mcV3"],cat=2)
        s.add(97685,["CheckKeys FAILURE","Upload of key 1 failed"])
        s.add(97704,["Crash in TRTTrackExtAlg_Tau_EFID","FAILURE at end"])
        s.add(97705,["Crash on L2MbSpFex_SCTNoiseSup in AthenaTrigRDOtoTAG","Algorithm stack"])
        s.add(97713,["Tool BunchCrossingTool either does not implement the correct interface, or its version is incompatible"])
        s.add(97729,["Caught signal 11\(Segmentation fault\)","Current algorithm: LVL1::TrigT1TRT","Current trigger chain: \<NONE\>"])
        s.add(97708,["Caught signal 11\(Segmentation fault\)","Current trigger chain: L2_mbSpTrk_noiseSup","Current algorithm: L2MbSpFex_SCTNoiseSup"])
        s.add(97734,["Caught signal 11\(Segmentation fault\)","Current trigger chain: L2_VdM_mbSpTrk","Current algorithm: L2MbSpFex"])
        s.add(97735,["Caught signal 11\(Segmentation fault\)","Current trigger chain: L2_CosmicsAllTeTRTxK_TRTTrkHypo_Pixel","Current algorithm: CosmicCosmicsAllTeTRTxK_TRTTrkHypo_PixelTrigTRTSegFinder"])
        s.add(97750,["Caught signal 11\(Segmentation fault\)","Current trigger chain: L2_mu10_Upsimumu_tight_FS","TrigDiMuon_FS"])
        s.add(97751,["Caught signal 11\(Segmentation fault\)","Last incident: Lvl2EventLoopMgr:EndRun","Current algorithm: \<NONE\>","Algorithm stack: \<EMPTY\>"])
        s.add(97784,["TCMalloc_ThreadCache::ReleaseToCentralCache"])
        s.add(97822,["IS repository 'RunCtrl' does not exist","The object \"RunCtrl\" of the \"is/repository\" type is not published in the \"initial\" partition"])
        s.add(94867,["Error in configuration of TauSlice","No module named TrigTauHypo.TrigTauHypoConfig"])
        s.add(97832,["TrigSteer_EF","ERROR  Error initializing one or several sub-algorithms"])
        s.add(97834,["MissingET/MissingETOutputAODList_jobOptions.py can not be found"])
        s.add(97835,["MissingET/MissingET_jobOptions.py can not be found"])
        s.add(98082,["ToolSvc","ERROR Cannot create tool InDetTrigTrackSummaryTool"])
        s.add(98132,['WARNING IPC partition \"part_lhl2ef_AtlasCAFHLT_rel_nightly\" is not valid','ipc::_objref_partition\* ipc::util::getPartition\(...\) at ipc/src/util.cc:273'])
        s.add(98277,["Errors while decoding TrigL2BphysContainer_tlp1"])   
        s.add(98377,["FATAL Failed to retrieve tool TrackSummaryTool = PublicToolHandle\('Trk::TrackSummaryTool'\)"])
        s.add(98397,["ImportError: No module named L1CaloSliceFlags"])
        s.add(91921,["RuntimeError: RootController is in faulty state because: Application 'EBEF-Segment-1:voatlas","has a problem that cannot be ignored."])
        s.add(98401,["RuntimeError: RootController did not get up/publish to IS in 60 seconds \(or it did and then got in an error state\)"])
        s.add(98406,["Core dump from CoreDumpSvc on","Current algorithm: StreamBS","Last incident: AthenaEventLoopMgr:BeginEvent"])
        s.add(94730,["efd::CoreEIssue ERROR EFD core problem","Failed terminating monitorThread"])
        s.add(98452,["ERROR Errors while decoding Trk::VxContainer_tlp2 any further ROOT messages for this class will be suppressed"])
        s.add(98453,["ImportError: No module named TrkExRungeKuttaPropagator.TrkExRungeKuttaPropagatorConf"])
        s.add(98490,["ImportError: No module named TrkExSTEP_Propagator.TrkExSTEP_PropagatorConf"])
        s.add(98531,["ERROR Errors while decoding Rec::TrackParticleContainer_tlp1 any further ROOT messages for this class will be suppressed "]) 
        s.add(98577,["ERROR Algorithm of type TrigJetFeaturesUnpacker is unknown"])
        s.add(98618,["FATAL Unchecked StatusCode in ByteStreamEventStorageOutputSvc::initDataWriter"])
        s.add(98619,["RootController is in faulty state because: Application 'ROS-Segment-1:voatlas62' has a problem that cannot be ignored"])
        s.add(98629,["ImportError: No module named DBReplicaSvc.DBReplicaSvcConf"])
        s.add(98631,["RootController is in faulty state"])
        if True: # these are dangerous bugs since this particular error printout also often appears when there are other problems
            s.add(98640,["OH repository 'Histogramming-L2-Segment-1-1-iss' does not exist"])
            s.add(98640,["IS repository 'Histogramming-L2-Segment-1-1-iss' does not exist"])
        s.add(98688,["IS infomation name 'Histogramming-L2-Segment-1-1-issL2PU-1/EXPERT/TrigSteer_L2/NumberOfLvl1TEs' is invalid"])
        s.add(98748,["IS repository 'DF-EF-Segment-0-iss' does not exist"])
        s.add(98768,["segmentation violation","Current trigger chain: EF_j50_a4tcem_eta25_xe50_empty","Current algorithm: CellMakerFullCalo_topo"])
        s.add(98786,["Error in opening muon calibration buffer"])
        s.add(98856,["No module named HLTTestApps.application"])
        s.add(98857,["T2CaloFastJet::hltExecute","Current algorithm: T2CaloFastJet_a4TT"])
        s.add(99135,["No such file or directory: 'LVL1config_","_rel_nightly.xml"])
        s.add(92097,["nothing found for TriggerCosts_1e33.xml","prescales1000.xml"])
        s.add(99337,["Unable to determine beamType","data12_hip"])
        s.add(99338,["ERROR updateAddress","Cannot translate clID"])
        s.add(99392,["Segmentation fault","runHLT_standalone.py"])
        s.add(99421,["No module named TrigT2CaloCommon.TrigT2CaloCommonConf"])
        s.add(99422,["ToolSvc.TileBeamInfoProvider","Error retrieving","from TDS"])
        s.add(99423,["testLVL1CTPMuonAthenaTrigRDO","Could not create Rep for DataObject"])
        s.add(99470,["No such file or directory", "LVL1config_MC_pp_v3_17.2.8.xml"])
        s.add(94152,["ERROR Upload of SMKey failed"])
        s.add(99993,["Segmentation fault","Trk::AtaStraightLineT<Trk::Charged>::~AtaStraightLineT"])
        s.add(99451,["Segmentation fault","in TrigMinimalEventLoopMgr::sysPrepareForRun"], "DB connection error, check for persistency")
        s.add(99451,["segmentation violation","Allocate \(size\=3768\) at src/tcmalloc.cc:2006","AtlasP1HLT"])
        s.add(99695,["ES_NoEndOfFileRecord","ESLOriginalFile reported: File end record not found in file"])
        s.add(99678,["ERROR  Cannot retrieve LayersInfo histogram","ToolSvc.JetFitterNNTool"])
        s.add(99712,["segmentation violation","in HLT::HLTResult::serialize","in TrigMinimalEventLoopMgr::HltResultROB"])
        s.add(99712,["Last incident: Lvl2EventLoopMgr:EndEvent","segmentation violation","TrigMinimalEventLoopMgr::HltResultROB"])
        s.add(99712,["Lvl2EventLoopMgr:EndEvent","TrigMinimalEventLoopMgr::HltResultROB","../src/TrigMinimalEventLoopMgr.cxx:2178","stack trace"])
        s.add(99751,["../src/PixelClusterCacheTool.cxx:34: error: invalid conversion","../src/SCT_ClusterCacheTool.cxx:35: error: invalid conversion"])
        s.add(99749,["error: SiClusterizationTool/SCT_ClusteringTool.h"])
        s.add(99765,["Current algorithm: CosmicCosmicsAllTeTRTxK_TRTTrkHypo_AllPhysicsTrigTRTSegFinder","TRT_DriftCircleOnTrack ../src/TRT_DriftCircleOnTrack.cxx"])
        s.add(99766,["JetRec/TrackSelectionForJets.py","DetFlags.detdescr.ID_on\(\)  and hasattr\(ToolSvc,\'InDetTrackSummaryTool\'\) "])
        s.add(99778,['Trig::TrigNtExecTool::ReadOPI','at ../src/TrigNtExecTool.cxx:354'])
        #s.add(99778,["StatusCodeSvc","FATAL Unchecked StatusCode in exit from lib /lib/libc.so.6 [Run,Evt,Lumi,Time,BunchCross,DetMask] ="])
        s.add(99802,['is bigger than my length','HLTJobLib: recoverable ERROR error processing EF_PROCESS'])
        s.add(99949,['Gaudi::Parsers::parse_real_vector<double','Caught signal 8\(Floating point exception\). Details']) # was: 99803
        s.add(99851,'error: VP1TrackSystems/TrackCollectionSettingsButton.h: No such file or directory')
        s.add(99852,["No rule to make target `install_tfs_jop'",'Trigger/TrigFTK/TrigFTKSim'])
        s.add(99853,['WARNING Chain EF_hadCalib_trk18_L1HA8 aborting with error code ABORT_CHAIN UNKNOWN UNKNOWN',"got error back while executing first algorithm"])
        s.add(99863,['ERROR Trying to define EF item more than once EF_e9_tight1_e5_etcut'])
        s.add(94873,['cmt/../src/TrigPhoton.cxx:225','diff\(TrigPhoton const']) #was: 99896
        s.add(99897,['cpp_any/MuonboyRecMaker.cxx:115','chicsc_','Current algorithm: MboyRec'])
        s.add(99898,['ERROR Error in configuration of EgammaSlice',"name 'L2ElectronHypo_e5_medium1_NoTrk' is not defined"])
        s.add(99903,['ERROR template chain with sig_id=g3_nocut is not defined at level EF'])
        s.add(99917,['ERROR Unknown error 2952715949','Algorithm of type  is unknown \(No factory available\)'])
        s.add(99920,['pyAMI.exceptions.AMI_Error','Authorisation: Restricted access, please login or create an account'])
        s.add(99930,['was caused by: ERROR TrigTRTHTHCounter'])
        s.add(100043,["NameError: name 'seed_VdM' is not defined", "ERROR Error in configuration of BeamSpotSlice"])
        s.add(100151,["RuntimeError: Unable to determine beamType from projectName 'data13_hip'"])
        s.add(100202, ["signal handler called","../src/root/OHRootProvider.cxx:84"])
        s.add(100224, ["signal handler called","IS repository 'RunParams' does not exist",'"is/repository" type is not published in the "athena_mon" partition'])
        s.add(100238, ["from AGDD2Geo.AGDD2GeoConf import AGDD2GeoSvc","No module named AGDD2Geo.AGDD2GeoConf"])
        s.add(100352,'IncludeError: include file LArCondAthenaPool/LArCondAthenaPool_joboptions.py can not be found')
        s.add(100426,['TypeError: Error when calling the metaclass bases','CfgMgr.Muon__MooSegmentCombinationFinder,ConfiguredBase'])
        #s.add(100426,['kwargs.setdefault\("TriggerHitAssociator", getPublicToolClone\("TriggerHitAssociator", "DCMathSegmentMaker",Redo2DFit=False\) \)'])
        s.add(100444,"AttributeError: 'TrigTestMonToolAC' object has no attribute 'SelectTruthPdgId'")
        s.add(100507,["No such file or directory","root://eosatlas//eos/atlas/atlascerngroupdisk/proj-sit/igrabows/TrigInDetValidation_electron/"])
        s.add(100558,["/build/atnight/localbuilds/nightlies/17.X.0-VAL/AtlasReconstruction/rel_nightly/InstallArea/jobOptions/MissingET/MissingET_jobOptions.py","ImportError: No module named MissingET.METRefGetter"]) #won't fix for rel_4
        s.add(100577,["Core dump from CoreDumpSvc","Current algorithm: TrigL2SiTrackFinder_FullScan_ZF_OnlyA"])
        s.add(100679,["ERROR Hypo algo should never be placed first in sequences with more than one input TE","FATAL Errors were too severe in this event will abort the job","ERROR Terminating event processing loop due to errors"])
        s.add(100680,["Moving to AthenaTrigRDO_chainOrder_compare","differences in tests with ordered HLT chain execution","TrigSteer_L2.TrigChainMoniValidation"])
        return


if __name__ == '__main__':
    test_one_log()
