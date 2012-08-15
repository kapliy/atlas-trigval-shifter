#!/usr/bin/env python

import re,time,datetime
import BeautifulSoup as bs
import urllib2

_URLTIMEOUT = 20

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
        if len(sbugs)>0:
            print ''
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
        #s.add(-4, 'ATN_TIME_LIMIT','Job timed out',cat=2)
    def prefill_nicos(s):
        """ Special bugs that are only picked up by NICOS - and are not present in the ATN summary page """
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
            s.add(-96332,["nightlies/17.1.X.Y-VAL-P1HLT/","ATHENA_REGTEST_FAILED \(64\) ROOTCOMP_MISMATCH \(4\)"],title = "WARNING Output differs from reference: don't report in Savannah or Roger would freak out", cat=1)
            s.add(-96332,["nightlies/17.1.X.Y-VAL-P1HLT/","WARNING Output differs from reference for","If this change is understood, please update"],title = "WARNING Output differs from reference: don't report in Savannah or Roger would freak out",cat=1)
            s.add(-96333,["nightlies/17.1.X.Y.Z-VAL-AtlasCAFHLT/","ATHENA_REGTEST_FAILED \(64\) ROOTCOMP_MISMATCH \(4\)"],title = "WARNING Output differs from reference: don't report in Savannah or Roger would freak out",cat=1)
            s.add(-96333,["nightlies/17.1.X.Y.Z-VAL-AtlasCAFHLT/","WARNING Output differs from reference for","If this change is understood, please update"],title = "WARNING Output differs from reference: don't report in Savannah or Roger would freak out",cat=1)
            s.add(-96334,["nightlies/17.2.X.Y-VAL-Prod/","ATHENA_REGTEST_FAILED \(64\) ROOTCOMP_MISMATCH \(4\)"],title = "WARNING Output differs from reference: don't report in Savannah or Roger would freak out",cat=1)
            s.add(-96334,["nightlies/17.2.X.Y-VAL-Prod/","WARNING Output differs from reference for","If this change is understood, please update"],title = "WARNING Output differs from reference: don't report in Savannah or Roger would freak out",cat=1)
            s.add(96335,["nightlies/17.1.X/","ATHENA_REGTEST_FAILED \(64\) ROOTCOMP_MISMATCH \(4\)"],cat=1)
            s.add(96335,["nightlies/17.1.X/","WARNING Output differs from reference for","If this change is understood, please update"],cat=1)
            s.add(-96336,["nightlies/17.1.X-VAL/","ATHENA_REGTEST_FAILED \(64\) ROOTCOMP_MISMATCH \(4\)"],title = "WARNING Output differs from reference: don't report in Savannah or Roger would freak out",cat=1)
            s.add(-96336,["nightlies/17.1.X-VAL/","WARNING Output differs from reference for","If this change is understood, please update"],title = "WARNING Output differs from reference: don't report in Savannah or Roger would freak out",cat=1)
            s.add(96337,["nightlies/17.2.X/","ATHENA_REGTEST_FAILED \(64\) ROOTCOMP_MISMATCH \(4\)"],cat=1)
            s.add(96337,["nightlies/17.2.X/","WARNING Output differs from reference for","If this change is understood, please update"],cat=1)
            s.add(-96338,["nightlies/17.2.X-VAL/","ATHENA_REGTEST_FAILED \(64\) ROOTCOMP_MISMATCH \(4\)"],title = "WARNING Output differs from reference: don't report in Savannah or Roger would freak out",cat=1)
            s.add(-96338,["nightlies/17.2.X-VAL/","WARNING Output differs from reference for","If this change is understood, please update"],title = "WARNING Output differs from reference: don't report in Savannah or Roger would freak out",cat=1)
            s.add(96339,["nightlies/18.X.0/","ATHENA_REGTEST_FAILED \(64\) ROOTCOMP_MISMATCH \(4\)"],cat=1)
            s.add(96339,["nightlies/18.X.0/","WARNING Output differs from reference for","If this change is understood, please update"],cat=1)
            s.add(-96340,["nightlies/18.X.0-VAL/","ATHENA_REGTEST_FAILED \(64\) ROOTCOMP_MISMATCH \(4\)"],title = "WARNING Output differs from reference: don't report in Savannah or Roger would freak out",cat=1)
            s.add(-96340,["nightlies/18.X.0-VAL/","WARNING Output differs from reference for","If this change is understood, please update"],title = "WARNING Output differs from reference: don't report in Savannah or Roger would freak out",cat=1)
            s.add(-96341,["nightlies/17.1.X.Y-VAL2-P1HLT/","ATHENA_REGTEST_FAILED \(64\) ROOTCOMP_MISMATCH \(4\)"],title = "WARNING Output differs from reference: don't report in Savannah or Roger would freak out",cat=1)
            s.add(-96341,["nightlies/17.1.X.Y-VAL2-P1HLT/","WARNING Output differs from reference for","If this change is understood, please update"],title = "WARNING Output differs from reference: don't report in Savannah or Roger would freak out",cat=1)
            s.add(-96342,["nightlies/17.1.X.Y.Z-VAL2-AtlasCAFHLT/","ATHENA_REGTEST_FAILED \(64\) ROOTCOMP_MISMATCH \(4\)"],title = "WARNING Output differs from reference: don't report in Savannah or Roger would freak out",cat=1)
            s.add(-96342,["nightlies/17.1.X.Y.Z-VAL2-AtlasCAFHLT/","WARNING Output differs from reference for","If this change is understood, please update"],title = "WARNING Output differs from reference: don't report in Savannah or Roger would freak out",cat=1)
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
            s.add(96714,["AthenaTrigRDO_MC_pp_v4_loose_mc_prescale","nightlies/17.1.X.Y.Z-VAL-AtlasCAFHLT/","test killed as time quota spent, test warning is issued"],cat=2)
            # TOLERANCE BUGS
            s.add(-8,"checkcounts test warning : trigger counts outside tolerance:",title="ATTENTION: add a TOLERANCE BUG match string in Bug.py::prefill_nicos for this release",cat=1) #HAS to be above other tolerance  strings - this is a "catch-all" case
            s.add(-96368,["checkcounts test warning : trigger counts outside tolerance:","nightlies/17.1.X.Y-VAL-P1HLT/"],title="count mismatch warnings:bona fide bugs but don't report in Savannah per Roger's request",cat=1) #FIXME wrong bug number!!!
            s.add(-96399,["checkcounts test warning : trigger counts outside tolerance:","nightlies/17.1.X.Y.Z-VAL-AtlasCAFHLT/"],title="count mismatch warnings:bona fide bugs but don't report in Savannah per Roger's request",cat=1)
            s.add(-96401,["checkcounts test warning : trigger counts outside tolerance:","nightlies/17.2.X.Y-VAL-Prod/"],title="count mismatch warnings:bona fide bugs but don't report in Savannah per Roger's request",cat=1)
            s.add(-96402,["checkcounts test warning : trigger counts outside tolerance:","nightlies/17.1.X/"],title="count mismatch warnings:bona fide bugs but don't report in Savannah per Roger's request",cat=1)
            s.add(-96403,["checkcounts test warning : trigger counts outside tolerance:","nightlies/17.1.X-VAL/"],title="count mismatch warnings:bona fide bugs but don't report in Savannah per Roger's request",cat=1)
            s.add(-96404,["checkcounts test warning : trigger counts outside tolerance:","nightlies/17.2.X-VAL/"],title="count mismatch warnings:bona fide bugs but don't report in Savannah per Roger's request",cat=1)
            s.add(-96405,["checkcounts test warning : trigger counts outside tolerance:","nightlies/18.X.0/"],title="count mismatch warnings:bona fide bugs but don't report in Savannah per Roger's request",cat=1)
            s.add(-96406,["checkcounts test warning : trigger counts outside tolerance:","nightlies/18.X.0-VAL/"],title="count mismatch warnings:bona fide bugs but don't report in Savannah per Roger's request",cat=2)
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
        s.add(86562,['ERROR preLoadFolder failed for folder /Digitization/Parameters','FATAL DetectorStore service not found'])
        # At some point, someone asked for a new bug report for the above bug -- if they complain again, you could use the line below
        #s.add(95595,['ERROR preLoadFolder failed for folder /Digitization/Parameters','FATAL DetectorStore service not found'])
        s.add(88042,["\[is::repository_var is::server::resolve\(...\) at is/src/server.cc:31\] IS repository 'Histogramming-EF-Segment-1-1-iss' does not exist"])
        s.add(88042,["\[is::repository_var is::server::resolve\(...\) at is/src/server.cc:31\] IS repository 'Histogramming-L2-Segment-1-1-iss' does not exist"])
        s.add(88042,['\[ipc::_objref_partition\* ipc::util::getPartition\(...\) at ipc/src/util.cc:273\] Partition "athena_mon" does not exist'])
        s.add(88042,["IS repository 'Histogramming-EF-Segment-1-1-iss' does not exist",'Partition "athena_mon" does not exist'])
        s.add(88554,['Moving to AthenaTrigRDO_chainOrder_compare','differences in tests with ordered HLT chain execution','TrigSteer_EF.TrigChainMoniValidation'])
        s.add(90593,['ERROR ServiceLocatorHelper::createService: wrong interface id IID_3596816672 for service JobIDSvc','Root+python problem when reading ESDs'])
        s.add(91065,['Error: When merging chains:','EF_mu4T','EF_j10_a4tc_EFFS','these were missing'])
        s.add(92206,['FATAL: Failed to start local PMG server',"RunManager instance has no attribute 'root_controller'"])
        s.add(92206,['FATAL: Failed to start RM server',"RunManager instance has no attribute 'root_controller'"])
        s.add(92213,'could not bind handle to CondAttrListCollection to key: /TRT/Onl/ROD/Compress','InDetTRTRodDecoder callback registration failed, but Athena job completes successfully')
        if True: # consider deleting bug 92260 soon
            s.add(92260,"IOError: \[Errno 2\] No such file or directory: '../AthenaTrigAODtoAOD_TrigNavSlimming/AOD_RSegamma.pool.root'" )
            s.add(92260,"IOError: \[Errno 2\] No such file or directory: '../AthenaTrigRDOtoESDAOD/AOD.pool.root'" )
            s.add(92260,"IOError: \[Errno 2\] No such file or directory: '../AthenaTrigRDOtoESDAOD/ESD.pool.root'" )
            s.add(92260,"IOError: \[Errno 2\] No such file or directory: '../AthenaTrigAODtoAOD_TrigNavSqueeze/AOD_SqueezeRFTrigCaloCellMaker.pool.root'" )
            s.add(92260,"IOError: \[Errno 2\] No such file or directory: '../BackCompAthenaTrigBStoESDAOD/AOD.pool.root'" )
            s.add(92260,"No input AOD file could be found matching '../AthenaTrig\*toESDAOD\*/AOD\*.pool.root'" )
            s.add(92260,"AssertionError: problem picking a data reader for file","../AthenaTrigRDOtoBS/raw.data")
            s.add(92260,["Unable to fill inputFileSummary from file ../AthenaTrigRDOtoESDAOD/ESD.pool.root. File is probably empty"])
            s.add(92260,["Unable to fill inputFileSummary from file ../AthenaTrigRDOtoESDAOD/AOD.pool.root. File is probably empty"])
            s.add(92260,["Unable to fill inputFileSummary from file ../AthenaTrigRDOtoAOD/AOD.pool.root. File is probably empty"])
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
        s.add(93534,["RootController is in faulty state because: Application","has a problem that cannot be ignored","ERROR transition failed"])
        s.add(93633,["IncludeError: include file CaloRecEx/CaloRecOutputItemList_jobOptions.py can not be found"])
        s.add(93740,["IncludeError: include file InDetPriVxCBNT/InDetPriVxCBNT_jobOptions.py can not be found"])
        s.add(93741,["ERROR Unable to build inputFileSummary from any of the specified input files","TimeoutError","KeyError: 'eventdata_itemsDic'"])
        s.add(93886,'At least one of the jobs \(ascending/descending chain counter\) has not been completed\! Exit.')
        s.add(93897,['LArL2ROBListWriter_j10_empty_larcalib','L1CaloTileHackL2ROBListWriter_j10_empty_larcalib','ERROR Could not find RoI descriptor - labels checked : TrigT2CaloEgamma initialRoI'])
        s.add(93990,["TriggerMenuSQLiteFile","sqlite' file is NOT found in DATAPATH, exiting"])
        s.add(94033,["ATLAS_DBA.LOGON_AUDIT_TRIGGER' is invalid and failed re-validation"])
        s.add(94084,["LVL1CTP::CTPSLink::getCTPToRoIBWords","Current algorithm: RoIBuilder"])
        s.add(94627,["ToolSvc.TrigTSerializer","MuonFeatureContainer_p3","ERROR Errors while decoding"])
        s.add(94095,["ERROR no handler for tech","FileMgr"])
        s.add(94016,["No such file or directory:","'HLTconfig_MC_pp_v4_loose_mc_prescale","xml'"])
        s.add(94173,["Py:TriggerPythonConfig","ERROR Chain L2_je255 defined 2 times with 2 variants"])
        s.add(94185,"ImportError: No module named egammaD3PDAnalysisConf")
        s.add(95610,["ERROR poolToObject: Could not get object for Token","ConditionsContainerTRTCond::StrawStatusContainerTemplate"])
        s.add(94192,["Non identical keys found. See diff_smk_","l2_diff.txt and ef_diff.txt","L2SecVtx_JetB.TrigInDetVxInJetTool.VertexFitterTool"])
        s.add(94261,"IncludeError: include file MuonTrkPhysMonitoring/MuonTrkPhysDQA_options.py can not be found")
        s.add(94342,["TrigMuonEFTrackBuilderConfig_SeededFS","Core dump from CoreDumpSvc","Caught signal 11\(Segmentation fault\)"])
        s.add(94435,["ES_WrongFileFormat: file is of no know format. Abort.EventStorage reading problem: file is of no know format. Abort.","virtual EventStackLayer"])
        s.add(94542,["RuntimeError: key 'outputNTUP_TRIGFile' is not defined in ConfigDic"])
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
        s.add(95141,["RuntimeError: RootController is in faulty state because:"])
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
        s.add(95971,["Errors while decoding TrigInDetTrackCollection_tlp2"," any further ROOT messages for this class will be suppressed"])
        s.add(95986,["/src/rbmaga.F:82","/src/setmagfield.F:52"])
        s.add(95995,["Trigger menu inconsistent, aborting","L2 Chain counter 454 used 2 times while can only once, will print them all"])
        s.add(96093,["ByteStreamAttListMetadataSvc","not locate service"])
        s.add(96094,["ConversionSvc::makeCall","ConversionSvc::createRep","THashTable::FindObject"])
        s.add(96097,["SEVERE: Caught SQL error: ORA-02290: check constraint \(ATLAS_TRIGGER_ATN.TW_ID_NN\) violated","SEVERE:  Database is already locked by ATLAS_TRIGGER_ATN_W"]) # the bug is found in uploadSMK.log
        #s.add(96098,"free\(\): corrupted unsorted chunks: 0x1ac14178")
        s.add(96098,["free\(\): corrupted unsorted chunks","Python/2.6.5/i686-slc5-gcc43-opt/bin/python"])
        s.add(96112,"ImportError: No module named AthenaServicesConf")
        s.add(96117,"JobTransform completed for RAWtoESD with error code 11000 \(exit code 10\)") # the matching statements can be found in log/nicos, but the exact error msg is found in RAWtoESD.log. TODO: if this shows up again, modify Project.py match_bugs to parse RAWtoESD.log
        #s.add(96137,["TFile::Init:0: RuntimeWarning: file expert-monitoring.root probably not closed, trying to recover","WARNING: no directory and/or release sturucture found","ERROR: cound not cd to directory:  TrigSteer_L2"])
        s.add(96142,["OBSOLETE WARNING please use RecExCond/RecExCommon_flags.py","Py:AutoConfiguration WARNING Unable to import PrimaryDPDFlags","Py:AutoConfiguration WARNING Primary DPDMake does not support the old naming convention"])
        s.add(96165,["from MuonIsolationTools.MuonIsolationToolsConf import","ImportError: No module named MuonIsolationTools.MuonIsolationToolsConf"])
        s.add(96215,"ImportError: cannot import name CBNTAA_L1CaloPPM")
        s.add(96216,["farmelements.py","if ret != 0 and ret != 5: raise PropagationException\(ret,output\)","PropagationException: return code: 1280"])
        s.add(96245,["is::repository_var is::server::resolve\(...\) at is/src/server.cc:31","CORBA::Object\* ipc::util::resolve\(...\) at ipc/src/util.cc:369"])
        s.add(96251,["WARNING Unable to retrieve the cell container  AllCalo","WARNING retrieve\(const\): No valid proxy for object AllCalo  of type CaloCellContainer\(CLID 2802\)"])
        s.add(96273,["raise IncludeError\( 'include file %s can not be found' % fn \)","IncludeError: include file TrigT1CaloCalibTools/CBNT_L1Calo_jobOptions.py can not be found"])
        s.add(96545,["Errors while decoding TrigL2BphysContainer_tlp1","Can't instantiate precompiled template SG::ELVRef"])
        s.add(96563,["lib/libc.so.6\(cfree\+0x59\)","glibc detected"])
        s.add(96581,["could not bind handle to CondAttrListCollection","/FWD/ALFA/position_calibration"])
        s.add(96583,["Python/2.6.5/i686-slc5-gcc43-opt/bin/python"," double free or corruption","glibc detected"])
        #s.add(94628,["LOGFILE LARGE and TRUNCATED"])
        s.add(96639,["Trigger menu inconsistent","Chain counter 4152 used 2 times while can only once"])
        s.add(90993,["Py:GenerateMenu.py","Error in configuration of EgammaSlice"])
        s.add(96660,["test -e ../AllMT_HIV2/AllMT_HIV2-1._0001.data","pre-conditions failed"])
        s.add(96675,["Errors while decoding egammaContainer_p2"])
        s.add(95732,["HLTMenu_frontier.xml: No such file or directory"])
        s.add(94869,["FSMTransitionError","Cannot execute configure()"])
        s.add(92536,["ERROR HLTProcess","could not find any files starting 'data11_hi.00193211.express_express.AthenaMTout_1.RAW._lb0717._CAF_999999_000001'"])
        s.add(96683,["ERROR HLTProcess","could not find any files starting 'data12_8TeV.00202798.physics_EnhancedBias.AthenaMTout_1.RAW._lb0000._CAF_999999_000001'"])
        s.add(96704,["Errors while decoding MuonFeatureDetailsContainer_p2"])
        s.add(96712,["'InDetGlobalTrackMonTool' object has no attribute 'TrackCollection'"])
        s.add(96718,["ToolSvc","Cannot create tool JetBTaggerTool"])
        s.add(96719,["ToolSvc","Cannot create tool JetTowerNoiseTool"])
        s.add(95812,["TrigTSerializer::serialize","at ../src/TrigTSerializer.cxx:223"])
        s.add(96756,["No module named JetEventAthenaPool","JetEventAthenaPoolConf"])
        s.add(96720,["ERROR CallBack function","GeoModelSvc","cannot be registered"])
        s.add(96760,["'Histogramming-EF-Segment-0-iss' does not exist"])
        return

if __name__ == '__main__':
    import sys
    assert len(sys.argv)==2,'USAGE: %s http://url.to.logfile'
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
