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
        s.seen = False
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
                if s.comment[0:2]==': ':
                    s.comment = s.comment[2:]
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
        """ Require that all patterns match. Matching is done bottom-up (i.e. newest bugs are matched first) """
        #print log
        for bug in reversed(s.bugs):
            nmatches = 0
            for pattern in bug.patterns:
                if re.search(pattern,log):
                    nmatches += 1
            if nmatches == len(bug.patterns):
                bug.seen = True
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
    def add(s,bugid,pattern,comment=None):
        """ Use this function to add pre-filled (aka known) bugs """
        s.bugs.append( Bug(bugid,pattern,comment) )
    def add_new(s,bugid,pattern,comment=None):
        """ Use this function to add new bugs in run.py - these will be reported separately at the top of the shift report """
        s.add(bugid,pattern,comment)
        s.bugs[-1].new = True
    def prefill_genpurpose(s):
        s.add(-1, 'CRITICAL stopped by user interrupt','User interrupt')
        s.add(-1, 'KeyboardInterrupt','User interrupt')
        s.add(-2, 'APPLICATION_DIED_UNEXPECTEDLY','Worker process failed')
        s.add(-3, 'received fatal signal 15','Job recieved SIGTERM signal')
        s.add(-3, ['Signal handler: Killing','with 15'],'Job recieved SIGTERM signal')
        #s.add(-4,"Signal handler: athCode=8","Job Segfaulted, please check cause '<font style=\"BACKGROUND-COLOR: yellow\">FIXME</font>'")
    def prefill(s):
        """ 
        Note that bugs will be matched bottom-up. That is, newer bugs should be put at the bottom and will get matched first
        s.add(,'')
        s.add(,['',''])
        """
        s.prefill_genpurpose()
        s.add(86562,['ERROR preLoadFolder failed for folder /Digitization/Parameters','FATAL DetectorStore service not found'])
        s.add(87109,"No such file or directory: '/afs/cern.ch/user/t/tbold/public/TDTtest/attila.AOD.pool.root'",comment='AthenaTrigAOD_TDT_fixedAOD fails with missing input file. According the the bug report, this has been fixed in TrigAnalysistest-00-03-24.')
        s.add(88042,"OH repository 'Histogramming-L2-Segment-1-1-iss' does not exist") # 87601 is also appropriate, but closed as duplicate
        s.add(88042,["IS repository 'Histogramming-EF-Segment-1-1-iss' does not exist"]) # not sure if this is indeed the same bug
        s.add(88042,["IS repository 'Histogramming-L2-Segment-1-1-iss' does not exist",'is::repository_var is::server::resolve'])
        s.add(88554,['Moving to AthenaTrigRDO_chainOrder_compare','differences in tests with ordered HLT chain execution','TrigSteer_EF.TrigChainMoniValidation'],comment='Bugtracker says this bug reports small changes in HLT chain execution, which are expected.')
        s.add(88602,['TDTExampleARA.py','ReferenceError: attempt to access a null-pointer'])
        s.add(89464,'ERROR Upload of SMKey failed')
        s.add(90593,'ERROR ServiceLocatorHelper::createService: wrong interface id IID_3596816672 for service JobIDSvc','Root+python problem when reading ESDs')
        s.add(90638,["if not ':' in connection:","argument of type 'NoneType' is not iterable","JobProperties.Rec.Trigger.triggerDbConnection which has not been set"],'TypeError at AthenaDBConfigRDO. Note that the bug report suggests the problem is due to conflict in TMXML build (bug 90665)') # tricky
        s.add(90677,['differences found in XML and DB trigger configuration tests','REGTEST events accepted by chain'],'Differences between DB and XML jobs because the job from the DB did not run, because of the missing/corrupted sqlite file.') # tricky
        s.add(91283,"IOError: \[Errno 2\] No such file or directory: '../BackCompAthenaTrigBStoESDAOD/AOD.pool.root' ")
        s.add(91264,['MissingETOutputESDList_jobOptions.py',"NameError: name 'StreamAOD' is not defined"])
        s.add(91299,['trigtest.pl: FAILURE at end','<component alias="ToolSvc.CaloCompactCellTool" name="CaloCompactCellTool"'])
        s.add(91681,['None is not the expected type for: JobProperties.Global.DetDescrVersion',"Auto-configured ConditionsTag '' from inputFileSummary"])
        s.add(91845,'HLTJobLib: crash ERROR intermediate file has no events')
        s.add(91903,['FATAL Folder /TRIGGER/LVL1/BunchGroupContent does not exist','ERROR Unable to initialize service "DetectorStore"'])
        s.add(91916,"Sequence 'L2_muon_standalone_mu24_tight_l2muonSA' got error back while executing first algorithm")
        s.add(92097,'xml file does not exist: prescales1000.xml')
        s.add(92140,["\[Errno 2\] No such file or directory: 'AOD.pool.root'","has_key\('/TRIGGER/HLT/Prescales'\)"])
        s.add(92163,['RpcLv1SLRawMonManager','Py:RAWtoESD','ERROR Athena received signal 11. Exit code reset to Athena exit code 139'])
        s.add(92163,'attempt to redefine type of "RPC_DCSConditionsTool" \(was: RPC_DCSConditionsTool, new: RPC_DCSConditionsTool\)',comment='This is similar to bug 92163 in that it occurs in RPC monitoring, but this time the error is with "RPC_DCSConditionsTool"')
        s.add(92165,["No such file or directory: '../AllPT_physicsV4_rerun/ef_Default_setup.txt'"],"CheckKeysV4 test failing because previous test (AllPT_physicsV4_rerun) has no output")
        s.add(92166,['No valid proxy for object TauRecContainer','HLTMonManager','ManagedMonitorToolBase::fillHists'])
        s.add(92206,['FATAL: Failed to start local PMG server',"RunManager instance has no attribute 'root_controller'"])
        s.add(92206,['FATAL: Failed to start RM server',"RunManager instance has no attribute 'root_controller'"])
        s.add(92208,["CaloMonManager INFO Retrieved tool PublicToolHandle\('CaloCellVecMon/CaloCellMon'\)","boost::spirit::nil_t"])
        s.add(92209,'TauSliceAthenaTrigRDO__v4_top.reference: No such file or directory')
        s.add(92213,'could not bind handle to CondAttrListCollection to key: /TRT/Onl/ROD/Compress','InDetTRTRodDecoder callback registration failed, but Athena job completes successfully')
        s.add(92222,'ERROR Upload of key 1 failed')
        s.add(92225,['Core dump from CoreDumpSvc','inlined at ../src/HLTBjetMonTool.cxx','HLTBjetMonTool::fill()'],'Segfault in HLTBjetMonTool, submitted to open bug, but may be a new problem')
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
        s.add(92273,['Last incident: EFEventLoopMgr:EndRun','FATAL Unchecked StatusCode in exit from lib /lib/libc.so.6']) # may be too general
        s.add(92273,['Last incident: EFEventLoopMgr:EndRun','FATAL Unchecked StatusCode in exit from lib /lib64/libc.so.6']) # may be too general
        s.add(92298,["No such file or directory: 'ESD.pool.root'",'testAthenaP1ESD_TrigEDMCheck_data.py'], "Upstream test failed or timed out")
        s.add(92298,["No such file or directory: 'ESD.pool.root'",'testAthenaP1ESD_TrigDecTool.py'], "Upstream test failed or timed out")
        s.add(92397,'RuntimeError: Conditions database identifier RPC_OFL is not defined',comment='Conditions database identifier RPC_OFL is not defined for standalone_cosmic test. Note that this was originally assigned to bug [91848]')
        s.add(92407,['CRITICAL stopped by user interrupt','BackCompAthenaTrigBStoESDAOD'])
        s.add(92413,['Start of HLT Processing in EF','Current algorithm: TrigSteer_EF','Segmentation fault'])
        s.add(92435,['include file MissingET/MissingETOutputAODList_jobOptions.py can not be found'])
        s.add(92436,['AntiKt6TowerJets','fastjet::ClusterSequenceArea::initialize_and_run_cswa'])
        s.add(92437,["'D3PDMakerFlags' object has no attribute 'CompressionLevel'"])
        s.add(92449,['DataHeader_p','object has no attribute','File "./TDTExampleARA.py"'])
        s.add(92501,['invalid next size','libTrigTauDiscriminant.so'],"Invalid read in TrigTauDiscriBuilder")
        s.add(92516,['AthMasterSeq', 'AthAlgSeq','TrigSteer_EF','EFBMuMuFex_DiMu_noOS','stack trace'],"Segfault in EFBMuMuFex_DiMu_noOS--fix to be in TrigBphysHypo-00-03-07")
        s.add(92532,"ERROR FATAL No input BS file could be found matching '../AthenaTrigRDOtoBS")
        s.add(92536,"HLTJobLib:       crash ERROR HLTProcess: could not find any files starting")
        s.add(92551,["NameError: name 'L2PhotonHypo_g12_loose' is not defined"])
        s.add(92595,["WARNING Chain L2_mu4T_j75_c4cchad aborting with error code ABORT_CHAIN"])
        s.add(92596,["CSCHackL2ROBListWriter_j10_empty_larcalib","ERROR Could not find RoI descriptor"])
        s.add(92598,["corrupted unsorted chunks:"])
        s.add(92615,["WARNING Chain L2_2mu4T_DiMu_l2muonSA aborting with error code ABORT_CHAIN UNKNOWN"])
        s.add(92632,"message=inputBSFile=link_to_file_from_P1HLT.data: link_to_file_from_P1HLT.data not found")
        s.add(92662,["Current algorithm: Kt5TopoJets","\(floating point invalid operation\)"])
        #s.add(92675,["Algorithm stack:","EFMissingET_Fex_noiseSupp"]) #DELETEME
        #s.add(92675,["FATAL Unchecked StatusCode","EFMissingET_Fex_noiseSupp"]) #DELETEME
        #s.add(92675,["Algorithm stack:","EFMissingET_Fex_2sidednoiseSupp"]) #DELETEME
        #s.add(92675,["FATAL Unchecked StatusCode","EFMissingET_Fex_2sidednoiseSupp"]) #DELETEME
        s.add(92680,['ERROR IN CHAIN: EF Chain counter 414 used 2 times while can only once, will print them all'])
        s.add(92699,["Current algorithm: TrigDiMuon_FS","Algorithm stack: "])
        s.add(92719,["Trigger menu inconsistent, aborting","Available HLT counter","TrigSteering/pureSteering_menu.py"])
        s.add(92734,["TrigConfConsistencyChecker","ERROR SAX error while parsing exceptions xml file, line 43, column 13"],'SAX error while parsing exceptions xml file')
        #s.add(92746,["HLTBjetMon",'Unknown exception caught, while filling histograms'],'Error in HLTBjetMon. This bug is already assigned to a b-slice expert.')   # REMOVE ME!
        s.add(92757,["chain L2_g100_etcut_g50_etcut with has no matching LVL1 item L1_2EM14L1_2EM14",'Trigger menu inconsistent, aborting'])
        s.add(92814,["Unable to initialize Algorithm TrigSteer_L2",'ERROR Configuration error','T2IDTauHypo_tau',])
        s.add(92830,["Non identical keys found. See diff_smk_","l2_diff.txt and ef_diff.txt","TrigL2MuonSA::RpcDataPreparator"])
        s.add(92881,["Failed in LArFebRodMap::set",'barrel_ec out of range ,pos_neg out of range ,em_hec_fcal out of range'])
        #s.add(92901,["HLT/HLTTestApps/i686-slc5-gcc43-opt/libhlttestapps_ers_streams.so",'lib/libhistmon.so','\[stack\]']) # may be too general
        #s.add(92938,["TrigSteer_EF","FATAL Errors were too severe in this event will abort the job"]) # REMOVE ME
        s.add(91772,["Floating point exception",'InDetSiSpTrackFinder','RAWtoESD has completed running of Athena with exit code -8','InDet::SiCombinatorialTrackFinder_xk::initialize'],comment='FPE in InDetSiSpTrackFinder::initialize with vector<double> as properties')
        s.add(92952,["following input TEs don't appear as output TE: EM"])
        s.add(92952,["ERROR the element: \['tau20_medium_bdt', 'tau20_medium1_bdt', 'tau29_medium_bdt', 'tau29_medium1_bdt'\] is not allowed"])
        s.add(92952,["AttributeError: When merging chains: \['EF_e20vhT_tight1', 'EF_g6T_etcut'\] this were missing: \['EF_g6T_etcut'\]"])
        s.add(92994,["Py:LArCalibMenu",'ERROR template chain with sig_id=g15_loose is not defined at level EF'])
        s.add(92449,["Can't find branch EventInfo_p3_McEventInfo in tree MetaData","'name=Segmentation fault \(invalid memory reference\)' 'signum=11' "])
        s.add(93048,["AttributeError: 'MboySvcConfig' object has no attribute 'DoAlignementFit'"])
        s.add(93049,["Chain L2_j30_c4ccem_L1TAU_HVtrk_LOF aborting with error code ABORT_CHAIN UNKNOWN BAD_JOB_SETUP at step"])
        s.add(93061,["L2MuonJetHypo","ERROR The number of Muons attached to the TE is not 1"])
        s.add(93195,["ERROR","No conversion CscRDO to stream","Could not create Rep for DataObject"])
        s.add(93231,["AttributeError: JobPropertyContainer:: JobProperties.MuonDQAFlagsCont does not have property doMuonTrkPhysMon"])
        s.add(93239,["decodeCreateSvcNameList: Cannot create service AGDD2GeoSvc/AGDD2GeoSvc"])
        s.add(93292,["ImportError: cannot import name T2CaloFastJet_a4TT_MultipleOutput_TEs","ERROR Error in configuration of JetSlice"])
        s.add(93294,["CRITICAL Trigger connection alias 'None' is not defined","You are attempting to access the jobproperty JobProperties.Rec.Trigger.triggerDbConnection which has not been set","KeyError: 'techno'",'leaving with code 8: "an unknown exception occurred"'])
        s.add(93305,["INFO Creating event stream from file list \['root://eosatlas//eos/atlas/atlascerngroupdisk/trig-daq/validation/test_data/data11_7TeV.00191628.physics_eb_zee_zmumu._0001.data'\]","Parameters = 'name=Segmentation fault \(invalid memory reference\)' 'signum=11'"])
        s.add(93307,["trigtest.pl --cleardir --test AllPT_physicsV4_run_stop_run --rundir AllPT_physicsV4_run_stop_run --conf TrigP1Test.conf","Algorithm stack: <EMPTY>","FATAL Unchecked StatusCode in exit from lib /lib/libc.so.6"]) # careful: may be too general
        return

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
    
