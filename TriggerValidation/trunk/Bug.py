#!/usr/bin/env python

import re,time
import BeautifulSoup as bs
import urllib2

_URLTIMEOUT = 20

class Bug:
    """ One bug """
    _urlpat = 'https://savannah.cern.ch/bugs/index.php?%d'
    def __init__(s,id,pattern=None,comment=None):
        s.id = int(id)
        s.patterns = []
        if pattern:
            if isinstance(pattern,list):
                s.patterns += pattern
            else:
                s.patterns.append(pattern)
        s.comment = comment
        s.new = False
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
    def fetch_comment(s):
        """ Do on-the-fly lookup of the bug title from the bug tracker """
        NOCOMMENT = 'CANNOT FETCH COMMENT FOR BUG %d'%(s.id)
        if not s.comment:
            b = s._urlopen(s.url())
            try:
                soup = bs.BeautifulSoup(b)
                s.comment = str((soup.findAll('h2')[1]).contents[1])
            except:
                s.comment = NOCOMMENT
        return s.comment
    def add_pattern(s,pattern):
        s.patterns.append(pattern)
    def url(s):
        return s._urlpat%s.id

class BugTracker:
    """ A local mini bugtracker to quickly look up common bugs """
    def __init__(s):
        s.bugs = []
    def match(s,log):
        """ Require that all patterns match """
        #print log
        for bug in s.bugs:
            nmatches = 0
            for pattern in bug.patterns:
                if re.search(pattern,log):
                    nmatches += 1
            if nmatches == len(bug.patterns):
                return bug
        return None
    def new_bugs(s):
        """ Returns all bugs labeled as 'new' - i.e., newly created bug reports """
        return [bug for bug in s.bugs if bug.new==True]
    def add(s,bugid,pattern,comment=None):
        """ Use this function to add pre-filled (aka known) bugs """
        s.bugs.append( Bug(bugid,pattern,comment) )
    def add_new(s,bugid,pattern,comment=None):
        """ Use this function to add new bugs in run.py - these will be reported separately at the top of the shift report """
        s.add(bugid,pattern,comment)
        s.bugs[-1].new = True
    def prefill(s):
        """ 
        s.add(,'')
        s.add(,['',''])
        """
        s.add(86562,['ERROR preLoadFolder failed for folder /Digitization/Parameters','FATAL DetectorStore service not found'])
        s.add(87109,"No such file or directory: '/afs/cern.ch/user/t/tbold/public/TDTtest/attila.AOD.pool.root'",comment='AthenaTrigAOD_TDT_fixedAOD fails with missing input file. According the the bug report, this has been fixed in TrigAnalysistest-00-03-24.')
        s.add(88042,"OH repository 'Histogramming-L2-Segment-1-1-iss' does not exist") # 87601 is also appropriate, but closed as duplicate
        s.add(88042,["IS repository 'Histogramming-EF-Segment-1-1-iss' does not exist"]) # not sure if this is indeed the same bug
        s.add(88042,["IS repository 'Histogramming-L2-Segment-1-1-iss' does not exist",'is::repository_var is::server::resolve'])
        s.add(88554,['Moving to AthenaTrigRDO_chainOrder_compare','differences in tests with ordered HLT chain execution','TrigSteer_EF.TrigChainMoniValidation'],comment='Bugtracker says this bug reports small changes in HLT chain execution, which are expected.')
        s.add(88602,['TDTExampleARA.py','ReferenceError: attempt to access a null-pointer'])
        s.add(89464,'ERROR Upload of SMKey failed')
        s.add(91283,"IOError: \[Errno 2\] No such file or directory: '../BackCompAthenaTrigBStoESDAOD/AOD.pool.root' ")
        s.add(91264,['MissingETOutputESDList_jobOptions.py',"NameError: name 'StreamAOD' is not defined"])
        s.add(91299,['trigtest.pl: FAILURE at end','<component alias="ToolSvc.CaloCompactCellTool" name="CaloCompactCellTool"'])
        s.add(91681,['None is not the expected type for: JobProperties.Global.DetDescrVersion',"Auto-configured ConditionsTag '' from inputFileSummary"])
        s.add(91845,'HLTJobLib: crash ERROR intermediate file has no events')
        s.add(91845,['HLTJobLib:','crash ERROR intermediate file has no events'])
        s.add(91903,['FATAL Folder /TRIGGER/LVL1/BunchGroupContent does not exist','ERROR Unable to initialize service "DetectorStore"'])
        s.add(91916,"Sequence 'L2_muon_standalone_mu24_tight_l2muonSA' got error back while executing first algorithm")
        s.add(92097,'xml file does not exist: prescales1000.xml')
        s.add(92140,["\[Errno 2\] No such file or directory: 'AOD.pool.root'","has_key\('/TRIGGER/HLT/Prescales'\)"])
        s.add(92163,['RpcLv1SLRawMonManager','Py:RAWtoESD','ERROR Athena received signal 11. Exit code reset to Athena exit code 139'])
        s.add(92163,'attempt to redefine type of "RPC_DCSConditionsTool" \(was: RPC_DCSConditionsTool, new: RPC_DCSConditionsTool\)',comment='This is similar to bug 92163 in that it occurs in RPC monitoring, but this time the error is with "RPC_DCSConditionsTool"')
        s.add(92166,['No valid proxy for object TauRecContainer','HLTMonManager','ManagedMonitorToolBase::fillHists'])
        s.add(92206,['FATAL: Failed to start local PMG server',"RunManager instance has no attribute 'root_controller'"])
        s.add(92206,['FATAL: Failed to start RM server',"RunManager instance has no attribute 'root_controller'"])
        s.add(92208,["CaloMonManager INFO Retrieved tool PublicToolHandle\('CaloCellVecMon/CaloCellMon'\)","boost::spirit::nil_t"])
        s.add(92209,'TauSliceAthenaTrigRDO__v4_top.reference: No such file or directory')
        s.add(92213,'could not bind handle to CondAttrListCollection to key: /TRT/Onl/ROD/Compress')
        s.add(92221,['EFPhotonHypo_g120_loose','TrigSteer_EF','Algorithm stack:'])
        s.add(92221,['EFPhotonHypo_g120_loose','cound not cd to directory:  TrigSteer_EF'])
        s.add(92222,'ERROR Upload of key 1 failed')
        s.add(92260,"IOError: \[Errno 2\] No such file or directory: '../AthenaTrigAODtoAOD_TrigNavSlimming/AOD_RSegamma.pool.root'" )
        s.add(92260,"IOError: \[Errno 2\] No such file or directory: '../AthenaTrigRDOtoESDAOD/AOD.pool.root'" )
        s.add(92260,"IOError: \[Errno 2\] No such file or directory: '../AthenaTrigRDOtoESDAOD/ESD.pool.root'" )
        s.add(92260,"IOError: \[Errno 2\] No such file or directory: '../AthenaTrigAODtoAOD_TrigNavSqueeze/AOD_SqueezeRFTrigCaloCellMaker.pool.root'" )
        s.add(92260,"IOError: \[Errno 2\] No such file or directory: '../BackCompAthenaTrigBStoESDAOD/AOD.pool.root'" )
        s.add(92260,"No input AOD file could be found matching '../AthenaTrig\*toESDAOD\*/AOD\*.pool.root'" )
        s.add(92264,'ImportError: cannot import name T2CaloFastJet_a4TT_JESCalib_MultipleOutput_TEs')
        s.add(92265,'ERROR Failed to find jet chain with name EF_j145_a4tchad')
        s.add(92267,['CharybdisJimmy.digit.RDO','Py:inputFilePeeker WARNING caught','raise convert_to_error\(kind, result\)'])
        s.add(92272,['L2PhotonHypo_g15_loose','carcore size is 10 but needs 9'])
        s.add(92273,['Last incident: EFEventLoopMgr:EndRun','FATAL Unchecked StatusCode in exit from lib /lib/libc.so.6'])
        s.add(92298,["No such file or directory: 'ESD.pool.root'",'TrigEDMCheck'])
        s.add(92397,'RuntimeError: Conditions database identifier RPC_OFL is not defined',comment='Conditions database identifier RPC_OFL is not defined for standalone_cosmic test. Note that this was originally assigned to bug [91848]')
        s.add(92407,['CRITICAL stopped by user interrupt','CRITICAL stopped by user interrupt','CRITICAL stopped by user interrupt','BackCompAthenaTrigBStoESDAOD'])
        s.add(92413,['Start of HLT Processing in EF','Current algorithm: TrigSteer_EF','Segmentation fault'])
        s.add(92435,['include file MissingET/MissingETOutputAODList_jobOptions.py can not be found'])
        s.add(92436,['AntiKt6TowerJets','fastjet::ClusterSequenceArea::initialize_and_run_cswa'])
        s.add(92437,["'D3PDMakerFlags' object has no attribute 'CompressionLevel'"])
        
if __name__ == '__main__':
    import sys
    assert len(sys.argv)==2,'USAGE: %s http://url.to.logfile'
    bugs = BugTracker()
    bugs.prefill()
    m =  bugs.match(urllib2.urlopen(sys.argv[1]).read())
    if m:
        print 'Matched: ',m.id,m.url()
        print m.fetch_comment()
    else:
        print 'No match!'
    
