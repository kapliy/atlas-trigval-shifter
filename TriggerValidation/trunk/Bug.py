#!/usr/bin/env python

import re
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
    def fetch_comment(s):
        """ Do on-the-fly lookup of the bug title from the bug tracker """
        if not s.comment:
            b = urllib2.urlopen(s.url(),timeout=_URLTIMEOUT)
            soup = bs.BeautifulSoup(b)
            try:
                s.comment = str((soup.findAll('h2')[1]).contents[1])
            except:
                s.comment = 'CANNOT FETCH COMMENT FOR BUG %d'%(s.id)
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
    def prefill(s):
        """ 
        s.bugs.append( Bug(,'') )
        s.bugs.append( Bug(,['','']) )
        """
        s.bugs.append( Bug(86562,['ERROR preLoadFolder failed for folder /Digitization/Parameters','FATAL DetectorStore service not found']) )
        s.bugs.append( Bug(87109,"No such file or directory: '/afs/cern.ch/user/t/tbold/public/TDTtest/attila.AOD.pool.root'") )
        s.bugs.append( Bug(87601,"OH repository 'Histogramming-L2-Segment-1-1-iss' does not exist") )
        s.bugs.append( Bug(88554,['Moving to AthenaTrigRDO_chainOrder_compare','differences in tests with ordered HLT chain execution','TrigSteer_EF.TrigChainMoniValidation'],comment='Bugtracker says this bug reports small changes in HLT chain execution, which are expected.') )
        s.bugs.append( Bug(88602,['TDTExampleARA.py','ReferenceError: attempt to access a null-pointer']) )
        s.bugs.append( Bug(89464,'ERROR Upload of SMKey failed') )
        s.bugs.append( Bug(91283,"IOError: \[Errno 2\] No such file or directory: '../BackCompAthenaTrigBStoESDAOD/AOD.pool.root' ") )
        s.bugs.append( Bug(91264,['MissingETOutputESDList_jobOptions.py',"NameError: name 'StreamAOD' is not defined"]) )
        s.bugs.append( Bug(91299,['trigtest.pl: FAILURE at end','<component alias="ToolSvc.CaloCompactCellTool" name="CaloCompactCellTool"']) )
        s.bugs.append( Bug(91681,['None is not the expected type for: JobProperties.Global.DetDescrVersion',"Auto-configured ConditionsTag '' from inputFileSummary"]) )
        s.bugs.append( Bug(91845,'HLTJobLib: crash ERROR intermediate file has no events') )
        s.bugs.append( Bug(91845,['HLTJobLib:','crash ERROR intermediate file has no events']) )
        s.bugs.append( Bug(91848,'RuntimeError: Conditions database identifier RPC_OFL is not defined') )
        s.bugs.append( Bug(91903,['FATAL Folder /TRIGGER/LVL1/BunchGroupContent does not exist','ERROR Unable to initialize service "DetectorStore"']) )
        s.bugs.append( Bug(91916,"Sequence 'L2_muon_standalone_mu24_tight_l2muonSA' got error back while executing first algorithm") )
        s.bugs.append( Bug(92097,'xml file does not exist: prescales1000.xml') )
        s.bugs.append( Bug(92140,["\[Errno 2\] No such file or directory: 'AOD.pool.root'","has_key\('/TRIGGER/HLT/Prescales'\)"]) )
        s.bugs.append( Bug(92206,['FATAL: Failed to start local PMG server',"RunManager instance has no attribute 'root_controller'"]) )
        s.bugs.append( Bug(92208,["CaloMonManager INFO Retrieved tool PublicToolHandle\('CaloCellVecMon/CaloCellMon'\)","boost::spirit::nil_t"]) )
        s.bugs.append( Bug(92209,'TauSliceAthenaTrigRDO__v4_top.reference: No such file or directory') )
        s.bugs.append( Bug(92213,'could not bind handle to CondAttrListCollection to key: /TRT/Onl/ROD/Compress') )
        s.bugs.append( Bug(92221,['EFPhotonHypo_g120_loose','TrigSteer_EF','Algorithm stack:']) )
        s.bugs.append( Bug(92221,['EFPhotonHypo_g120_loose','cound not cd to directory:  TrigSteer_EF']) )
        s.bugs.append( Bug(92222,'ERROR Upload of key 1 failed') )
        s.bugs.append( Bug(92260,"IOError: \[Errno 2\] No such file or directory: '../AthenaTrigAODtoAOD_TrigNavSlimming/AOD_RSegamma.pool.root'" ) )
        s.bugs.append( Bug(92260,"IOError: \[Errno 2\] No such file or directory: '../AthenaTrigRDOtoESDAOD/AOD.pool.root'" ) )
        s.bugs.append( Bug(92260,"IOError: \[Errno 2\] No such file or directory: '../AthenaTrigRDOtoESDAOD/ESD.pool.root'" ) )
        s.bugs.append( Bug(92260,"IOError: \[Errno 2\] No such file or directory: '../AthenaTrigAODtoAOD_TrigNavSqueeze/AOD_SqueezeRFTrigCaloCellMaker.pool.root'" ) )
        s.bugs.append( Bug(92264,'ImportError: cannot import name T2CaloFastJet_a4TT_JESCalib_MultipleOutput_TEs') )
        s.bugs.append( Bug(92265,'ERROR Failed to find jet chain with name EF_j145_a4tchad') )
        s.bugs.append( Bug(92267,['CharybdisJimmy.digit.RDO','Py:inputFilePeeker WARNING caught','raise convert_to_error\(kind, result\)']) )
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
    
