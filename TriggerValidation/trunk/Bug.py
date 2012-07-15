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
        """ General failure conditions """
        s.add(-1, 'CRITICAL stopped by user interrupt','User interrupt')
        s.add(-1, 'KeyboardInterrupt','User interrupt')
        s.add(-2, 'APPLICATION_DIED_UNEXPECTEDLY','Worker process failed')
        s.add(-3, 'received fatal signal 15','Job recieved SIGTERM signal')
        s.add(-3, ['Signal handler: Killing','with 15'],'Job recieved SIGTERM signal')
        s.add(-4, 'ATN_TIME_LIMIT','Job timed out')
        s.add(-4, ['test killed as time quota spent, test warning is issued','nicos_kill_fam'],'Job timed out')
    def prefill_nicos(s):
        """ Special bugs that are only picked up by NICOS - and are not present in the ATN summary page """
        s.add(94697,['href="#prblm"\>ls: \*rel_\[0-6\].data.xml: No such file or directory'],'NICOS HARMLESS WARNING: missing *rel_[0-6].data.xml')
        s.add(94970,['href="#prblm"\>python: can\'t open file \'checkFileTrigSize_RTT.py\''],'NICOS HARMLESS WARNING: cannot find checkFileTrigSize_RTT.py')
        s.add(94775,['href="#prblm"\>sh: voms-proxy-info: command not found'],'NICOS HARMLESS WARNING: voms-proxy-info command not found')
        s.add(-5, ['\.reference: No such file or directory','wc:','old/reference'],'NICOS: MISSING REFERENCE FILE')
        s.add(-5, ['\.reference: No such file or directory\</A\>\<BR\>'],'NICOS: MISSING REFERENCE FILE')
        s.add(-5, ['\.reference: No such file or directory','wc:','checkcounts test warning: Unable to open reference'],'NICOS: MISSING REFERENCE FILE')
        s.add(-6, ['These errors occured: ROOTCOMP_MISMATCH \(4\)','trigtest.pl: FAILURE at end'],'NICOS: ROOTCOMP MISMATCH')
        s.add(-7, ['NICOS NOTICE: POSSIBLE FAILURE \(ERROR\) : LOGFILE LARGE and TRUNCATED'],'NICOS: LOGFILE TRUNCATED')
    def prefill(s):
        """ 
        Note that bugs will be matched bottom-up. That is, newer bugs should be put at the bottom and will get matched first
        s.add(,'')
        s.add(,['',''])
        """
        s.prefill_genpurpose()
        s.prefill_nicos()
        s.add(86562,['ERROR preLoadFolder failed for folder /Digitization/Parameters','FATAL DetectorStore service not found'])
        # At some point, someone asked for a new bug report for the above bug -- if they complain again, you could uncomment line below
        #s.add(95595,['ERROR preLoadFolder failed for folder /Digitization/Parameters','FATAL DetectorStore service not found'])
        s.add(87109,"No such file or directory: '/afs/cern.ch/user/t/tbold/public/TDTtest/attila.AOD.pool.root'",comment='AthenaTrigAOD_TDT_fixedAOD fails with missing input file. According the the bug report, this has been fixed in TrigAnalysistest-00-03-24.')
        s.add(88042,["\[is::repository_var is::server::resolve\(...\) at is/src/server.cc:31\] IS repository 'Histogramming-EF-Segment-1-1-iss' does not exist"])
        s.add(88042,["\[is::repository_var is::server::resolve\(...\) at is/src/server.cc:31\] IS repository 'Histogramming-L2-Segment-1-1-iss' does not exist"])
        s.add(88042,['\[ipc::_objref_partition\* ipc::util::getPartition\(...\) at ipc/src/util.cc:273\] Partition "athena_mon" does not exist'])
        s.add(88554,['Moving to AthenaTrigRDO_chainOrder_compare','differences in tests with ordered HLT chain execution','TrigSteer_EF.TrigChainMoniValidation'])
        s.add(90593,['ERROR ServiceLocatorHelper::createService: wrong interface id IID_3596816672 for service JobIDSvc','Root+python problem when reading ESDs'])
        s.add(90638,["if not ':' in connection:","argument of type 'NoneType' is not iterable","JobProperties.Rec.Trigger.triggerDbConnection which has not been set"],'TypeError at AthenaDBConfigRDO. Note that the bug report suggests the problem is due to conflict in TMXML build (bug 90665)') # tricky
        s.add(90677,['differences found in XML and DB trigger configuration tests','REGTEST events accepted by chain'],'Differences between DB and XML jobs because the job from the DB did not run, because of the missing/corrupted sqlite file.') # tricky
        s.add(91065,['Error: When merging chains:','EF_mu4T','EF_j10_a4tc_EFFS','these were missing'])
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
        s.add(92213,'could not bind handle to CondAttrListCollection to key: /TRT/Onl/ROD/Compress','InDetTRTRodDecoder callback registration failed, but Athena job completes successfully')
        #s.add(92222,'ERROR Upload of key 1 failed') # too general
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
        s.add(92264,'ImportError: cannot import name T2CaloFastJet_a4TT_JESCalib_MultipleOutput_TEs')
        s.add(92265,'ERROR Failed to find jet chain with name EF_j145_a4tchad')
        s.add(92267,['CharybdisJimmy.digit.RDO','Py:inputFilePeeker WARNING caught','raise convert_to_error\(kind, result\)'])
        s.add(92272,['L2PhotonHypo_g15_loose','carcore size is 10 but needs 9'])
        s.add(94142,"/src/MeasuredAtaStraightLine.cxx:108")
        s.add(92298,["No such file or directory: 'ESD.pool.root'",'testAthenaP1ESD_TrigEDMCheck_data.py'], "Upstream test failed or timed out")
        s.add(92298,["No such file or directory: 'ESD.pool.root'",'testAthenaP1ESD_TrigDecTool.py'], "Upstream test failed or timed out")
        s.add(92397,'RuntimeError: Conditions database identifier RPC_OFL is not defined',comment='Conditions database identifier RPC_OFL is not defined for standalone_cosmic test. Note that this was originally assigned to bug [91848]')
        s.add(92435,['include file MissingET/MissingETOutputAODList_jobOptions.py can not be found'])
        s.add(92436,['AntiKt6TowerJets','fastjet::ClusterSequenceArea::initialize_and_run_cswa'])
        s.add(92437,["'D3PDMakerFlags' object has no attribute 'CompressionLevel'"])
        s.add(92449,['DataHeader_p','object has no attribute','File "./TDTExampleARA.py"'])
        s.add(92501,['invalid next size','libTrigTauDiscriminant.so'],"Invalid read in TrigTauDiscriBuilder")
        s.add(92532,"ERROR FATAL No input BS file could be found matching '../AthenaTrigRDOtoBS")
        s.add(92536,"HLTJobLib:       crash ERROR HLTProcess: could not find any files starting")
        s.add(92551,["NameError: name 'L2PhotonHypo_g12_loose' is not defined"])
        s.add(92595,["WARNING Chain L2_mu4T_j75_c4cchad aborting with error code ABORT_CHAIN"])
        s.add(92596,["CSCHackL2ROBListWriter_j10_empty_larcalib","ERROR Could not find RoI descriptor"])
        s.add(92615,["WARNING Chain L2_2mu4T_DiMu_l2muonSA aborting with error code ABORT_CHAIN UNKNOWN"])
        s.add(92632,"message=inputBSFile=link_to_file_from_P1HLT.data: link_to_file_from_P1HLT.data not found")
        s.add(92680,['ERROR IN CHAIN: EF Chain counter 414 used 2 times while can only once, will print them all'])
        s.add(95540,['ERROR IN CHAIN: EF Chain counter 2001 used 2 times while can only once, will print them all'])
        s.add(92719,["Trigger menu inconsistent, aborting","Available HLT counter","TrigSteering/pureSteering_menu.py"])
        s.add(92734,["TrigConfConsistencyChecker","ERROR SAX error while parsing exceptions xml file, line 43, column 13"],'SAX error while parsing exceptions xml file')
        s.add(92757,["chain L2_g100_etcut_g50_etcut with has no matching LVL1 item L1_2EM14L1_2EM14",'Trigger menu inconsistent, aborting'])
        s.add(92814,["Unable to initialize Algorithm TrigSteer_L2",'ERROR Configuration error','T2IDTauHypo_tau',])
        s.add(92830,["Non identical keys found. See diff_smk_","l2_diff.txt and ef_diff.txt","TrigL2MuonSA::RpcDataPreparator"])
        s.add(92881,["Failed in LArFebRodMap::set",'barrel_ec out of range ,pos_neg out of range ,em_hec_fcal out of range'])
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
        s.add(93342,"FATAL ../src/JetVtxTrackHelper.cxx:154")
        s.add(93348,["LArRawChannelBuilder","ERROR Can't retrieve LArDigitContainer with key FREEfrom StoreGate."])
        s.add(93375,["L2_j30_c4ccem_2L1MU4_HV_EMPTY", "'T2CaloJet_Jet_noise':ABORT_CHAIN UNKNOWN BAD_JOB_SETUP","got error back while executing first algorithm"])
        s.add(93444,["IncludeError: include file CBNT_Particle/CBNT_Particle_jobOptions.py can not be found","AthenaTrigRDO"])
        s.add(93461,["muFast_Mcal","Error in opening muon calibration buffer","MuonCalBufferSize"])
        s.add(93477,["EGammaStream_TagAndProbeForwardElectronFilter","ERROR Inconsistent configuration of the input container keys","ERROR Unable to initialize Algorithm EGammaStream_TagAndProbeForwardElectronFilter"])
        s.add(93495,["pure virtual method called","terminate called without an active exception","MagFieldAthenaSvc ../src/MagFieldAthenaSvc.cxx:109","MagFieldAthenaSvc ../src/MagFieldAthenaSvc.cxx:109"])
        s.add(93502,["No module named InDetVertexMonitoring.InDetVertexMonitoringConf","DataQualitySteering_jobOptions.py: exception when setting up inner detector monitoring"])
        s.add(93503,["AttributeError: 'DQMonFlagsCont' object has no attribute 'doMuonTrkPhysMon'"])
        s.add(93505,["ERROR Problems calling Blob2ToolConstants"])
        s.add(93520,["AttributeError: 'InDetGlobalTrackMonTool' object has no attribute 'checkRate'"])
        s.add(93534,["RootController is in faulty state because: Application","has a problem that cannot be ignored","ERROR transition failed"])
        s.add(93582,["At least one of the jobs \(XML or DB reading\) has not been completed! Exit.","RDO_test.log"])
        s.add(93605,["Error ORA-01017: invalid username/password; logon denied"])
        s.add(93605,["comparing L1 menus from oracle and from frontier download","diff: L1Menu_oracle.xml: No such file or directory"])
        s.add(93633,["IncludeError: include file CaloRecEx/CaloRecOutputItemList_jobOptions.py can not be found"])
        s.add(93634,["ImportError: No module named part_lhl2ef_opt"])
        s.add(93636,["OPEN ERROR  boost::_bi::bind_t","Io::FileAttr const"])
        s.add(93658,["ES_WrongFileFormat: file is of no know format", "IOError: Invalid file or format at '../AllMT_physicsV4_caf/AllMT_mcV4_caf-1._0001.data'"])
        #s.add(93735,["ERROR Upload of key 2 failed"]) # in reality, one needs to look inside <DIR>/uploadSMK.log
        s.add(93735,["ERROR Upload of key 1 failed"])
        s.add(93736,["ERROR attempt to add a duplicate \(TopAlg.BeamBackgroundFiller\) ... dupe ignored"])
        s.add(93740,["IncludeError: include file InDetPriVxCBNT/InDetPriVxCBNT_jobOptions.py can not be found"])
        s.add(93741,["ERROR Unable to build inputFileSummary from any of the specified input files","TimeoutError","KeyError: 'eventdata_itemsDic'"])
        s.add(93747,["ERROR CaloCondBlobBase::getObjVersion: Invalid Blob"])
        s.add(93833,["AttributeError: 'D3PD__VectorFillerTool' object has no attribute 'JetTag_SoftMuonInfoMuonAssoc_target'"])
        s.add(93886,'At least one of the jobs \(ascending/descending chain counter\) has not been completed\! Exit.')
        s.add(93887,['WARNING Unpacking  of L2 chains failed','Current algorithm: GlobalMonManager','pool::PersistencySvc::DatabaseHandler::readObject'])
        s.add(93888,"TypeError: interpretConnection\(\) got an unexpected keyword argument 'resolveAlias'")
        s.add(93889,"NameError: name 'StreamESD' is not defined")
        s.add(93897,['LArL2ROBListWriter_j10_empty_larcalib','L1CaloTileHackL2ROBListWriter_j10_empty_larcalib','ERROR Could not find RoI descriptor - labels checked : TrigT2CaloEgamma initialRoI'])
        s.add(93986,["AttributeError: 'FreeStore' object has no attribute 'l2_BjetFex_IDScan'"])
        s.add(93987,["No such file or directory: 'HLTconfig_MC_pp_v4_loose_mc_prescale_17.2.2.2.xml'",'ServiceMgr.HLTConfigSvc.getAlgorithmsByLevel\(\)','doc = ET.parse\(self.XMLMenuFile\)'])
        s.add(93990,["TriggerMenuSQLiteFile","sqlite' file is NOT found in DATAPATH, exiting"])
        s.add(94001,["AttributeError: 'TileDQFragMonTool' object has no attribute 'TileRawChannelContainer'"])
        s.add(94033,["ATLAS_DBA.LOGON_AUDIT_TRIGGER' is invalid and failed re-validation"])
        s.add(94049,["ERROR Can't retrieve offline RawChannel from TES"])
        s.add(94084,["LVL1CTP::CTPSLink::getCTPToRoIBWords","Current algorithm: RoIBuilder"])
        s.add(94627,["ToolSvc.TrigTSerializer","MuonFeatureContainer_p3","ERROR Errors while decoding"])
        #s.add(94120,["ERROR no handler for tech","FileMgr"]) # duplicate report
        s.add(94095,["ERROR no handler for tech","FileMgr"])
        s.add(92976,["ERROR EF chains that recursively call L2 sequences","TrigConfConsistencyChecker"])
        #s.add(41910,["ToolSvc.InDetTrigPrdAssociationTool","ERROR track already found in cache"])
        s.add(94016,["No such file or directory:","'HLTconfig_MC_pp_v4_loose_mc_prescale","xml'"])
        #s.add(94152,['TriggerTool.jar','ERROR Upload of SMKey failed']) # in reality, one needs to look inside <DIR>/uploadSMK.log  
        s.add(94173,["Py:TriggerPythonConfig","ERROR Chain L2_je255 defined 2 times with 2 variants"])
        s.add(94176,["L2EFChain_mu_EFFSonly","'TrigMuonEFCombinerDiMuonMassHypoConfig' is not defined"])
        s.add(94185,"ImportError: No module named egammaD3PDAnalysisConf")
        s.add(95610,["ERROR poolToObject: Could not get object for Token","ConditionsContainerTRTCond::StrawStatusContainerTemplate"])
        s.add(94192,["Non identical keys found. See diff_smk_","l2_diff.txt and ef_diff.txt","L2SecVtx_JetB.TrigInDetVxInJetTool.VertexFitterTool"])
        s.add(94261,"IncludeError: include file MuonTrkPhysMonitoring/MuonTrkPhysDQA_options.py can not be found")
        s.add(94273,["ERROR: Can't find branch EventInfo_p3_McEventInfo in tree MetaData","ERROR ServiceLocatorHelper::createService: wrong interface id IID"])
        s.add(94320,["HLTAutoKey_PrimVx","of type \[VxContainer\] is INCONSISTENT. The element does not seem to be in the container. This link can not be written"])
        #s.add(94339,["__libc_malloc","libMuonMDT_CnvTools.so","/bin/python: corrupted double-linked list"]) # this bug can only be found in full log file
        s.add(94342,["TrigMuonEFTrackBuilderConfig_SeededFS","Core dump from CoreDumpSvc","Caught signal 11\(Segmentation fault\)"])
        #s.add(94342,["EFTrigMissingETMuon_Fex","Core dump from CoreDumpSvc","Caught signal 11\(Segmentation fault\)"]) # another bug
        #s.add(94343,["SystemError: problem in C\+\+; program state has been reset"]) # too general?
        s.add(94349,["Py:GenerateMenu.py","ERROR Error in configuration of JetSlice","ImportError: No module named HIJetRec.HIJetRecConf"])
        s.add(94350,["Py:LArCalibMenu","ERROR template chain with sig_id=j","is not defined at level L2"])
        s.add(94362,"ImportError: No module named tauRec.tauRecFlags")
        s.add(94362,"ImportError: No module named TrigTauRec.TrigTauRecConfig")
        s.add(94387,"IOError: \[Errno 2\] No such file or directory: 'RDO.201489._000001.pool.root.1'")
        s.add(94394,"ToolSvc.EFTrigEgammaPhotonCutIDTool_ForcePhoConv  ERROR vector size is 9 but needs combined")
        s.add(94403,["RuntimeError: \[dynlibs\]daq::dynlibs::DynamicLibrary::DynamicLibrary","Dynamic library libTrigServices not found"])
        s.add(94428,["import D3PDMakerCoreCompsConf","ImportError: No module named D3PDMakerCoreCompsConf"])
        s.add(94429,"ImportError: No module named TrigBphysMonitoring.TrigBphysMonitoringConfig")
        s.add(94435,["ES_WrongFileFormat: file is of no know format. Abort.EventStorage reading problem: file is of no know format. Abort.","virtual EventStackLayer"])
        s.add(94443,"ERROR Running command `rc_sendcommand -ppart_lhl2ef_AtlasCAFHLT_rel_nightly -nRootController exit' has produced an error")
        s.add(94507,["TH1::Fill","../src/TrigLBNHist.cxx:92"])
        s.add(94507,["TrigLBNHist<TH1I>::Fill","../src/TrigLBNHist.cxx:92"])
        s.add(94542,["RuntimeError: key 'outputNTUP_TRIGFile' is not defined in ConfigDic"])
        #s.add(94543,"tech: ROOT  desc: HIST  flags: INVALID  i_flags: WRITE")
        s.add(94595,['THistSvc','ERROR already registered an object with identifier','EXPERT/TrigSteer_'])
        #s.add(94598,['EFTrigMissingETMuon_Fex_FEB','at ../src/TrigInDetTrack.cxx:67']) # uninformative stack trace
        #s.add(94598,'Current algorithm: EFTrigMissingETMuon_Fex_FEB') #too general
        #s.add(94598,['Current algorithm: EFTrigMissingETMuon_Fex']) # uninformative stack trace
        #s.add(94599,['corrupted double-linked list','cfree','libeformat.so']) # uninformative stack trace, full log only
        #s.add(94599,['double free or corruption','cfree','_ZN4Cint8Internal18G__BufferReservoirD1Ev']) # uninformative stack trace, full log only
        s.add(94610,['EventStorage::file_end_record ESLOriginalFile::currentFileFER','data10_7TeV.00152845.physics_MinBias.merge.RAW._lb0250._0003.1','GUID not present in BS file'])
        s.add(94611,['Current algorithm: MuGirl','msFit ../src/GlobalFitTool.cxx:571'])
        s.add(94654,['ImportError: cannot import name LVL1CTP__CBNTAA_CTP_RDO'])
        #s.add(94667,['in CoreDumpSvcHandler::action','at ../src/root/OHRootProvider.cxx:136'])
        s.add(94713,['LArRawConditionsDict2_gen_rflx.cpp:35473','Reflex::LiteralString::Remove'])
        s.add(94725,['THistSvc','ERROR already registered an object with identifier','EXPERT/TrigEFElectronHypo_'])
        s.add(94726,['in InDet::SiCluster::width','in InDet::SiTrajectoryElement_xk::patternCovariances'])
        s.add(94730,['efd::CoreEIssue ERROR EFD core problem','Failed terminating monitorThread'])
        s.add(94734,['\[TObject\* histmon::THistRegisterImpl::HInfo::get\(...\) at histmon/src/THistRegisterImpl.cxx:310\] Histograms registered with the id "/EXPERT/','CutCounter" are not compatible for the merge operation'])
        s.add(94738,'ImportError: No module named TrigL2CosmicMuon.TrigL2CosmicMuon_Config')
        s.add(94740,'ImportError: No module named METRefGetter_newplup')
        s.add(94787,['include file MissingETSig/MissingETSigOutputESDList_jobOptions.py can not be found'])
        s.add(94817,['can not locate service MuonTGC_CablingSvc'])
        s.add(92555,['Warning in <TEnvRec::ChangeValue>','attempt to access a null-pointer'])
        s.add(94825,['No module named TrigIDtrkMonitoring.TrigIDtrkMonitoringConfig'])
        s.add(94827,['FATAL Conditions database connection COOLOFL_INDET/COMP200 cannot be opened'])
        s.add(94866,"NameError: name 'isTier0Flag' is not defined")
        s.add(94867,['Error in configuration of TauSlice','AssertionError: unable to find L2 hypothesis algorithm \(l2calo_tau70_loose1\)'])
        s.add(94873,['Last incident: AthenaEventLoopMgr:BeginEvent','Current algorithm: TrigEDMChecker','diff ../src/TrigPhoton.cxx:225'])
        s.add(94874,['ERROR Trying to define EF item more than once EF_tauNoCut'])
        s.add(94877,['line 98, in setHltExtraPayloadWords','OverflowError: bad numeric conversion: positive overflow'])
        s.add(94765,['Muonboy/digitu ERROR of MDT/CSC station Off','which has digits'])
        s.add(94958,['Py:TriggerPythonConfig','ERROR IN CHAIN: EF Chain counter 801 used 2 times while can only once, will print them all'])
        s.add(95024,['segmentation violation','TrigDiMuonFast::makeMDT\(Candidate'])
        s.add(95026,['ImportError: cannot import name CBNTAA_CaloInfo'])
        s.add(95027,['Py:LArCalibMenu     ERROR template chain with sig_id=g.\* is not defined at level EF'])
        s.add(95028,['NameError: name \'L2ElectronHypo_e12_loose1_FTK\' is not defined'])
        s.add(95062,["include file CaloRec/CaloRec_CBNT_jobOptions.py can not be found"])
        s.add(95063,["AttributeError: \'module\' object has no attribute \'CaloSwGap_v3\'"])
        s.add(95069,['Muonboy/digitu ERROR of MDT/CSC station Off','which has hits'])
        s.add(95115,['in TrigConfChain::TrigConfChain','TrigMonitoringEvent/TrigMonitoringEvent/TrigConfChain.h:28'])
        s.add(95115,['Trig::FillConf::FillLV1','TrigMonitoringEvent/TrigMonConfig.icc:163'])
        s.add(95116,['in TrigCostTool::\~TrigCostTool','in TrigMonConfig::\~TrigMonConfig'])
        s.add(95116,['TrigSteer_L2','FATAL in sysStart\(\): standard std::exception is caught','ERROR std::bad_alloc'])
        #s.add(95141,["RuntimeError: RootController is in faulty state because: Application 'L2-Segment-1",'OnlRec::ExpertSystemDecision ERROR Raised Error state because of "L2PU'])
        s.add(95141,["RuntimeError: RootController is in faulty state because:"])
        s.add(95156,['ERROR ServiceLocatorHelper::service: can not locate service InDetBeamSpotOnline','ERROR  failed to retrieve Online BeamCondSvc','ToolSvc.TestMonToolAC'])
        s.add(95168,['Current algorithm: L2BjetFex_Jet_JetF','TrigBjetFex::hltExecute','src/FexAlgo.cxx:84'])
        s.add(95172,['L2SecVtx_JetB','ERROR Failed to get TrigVertexCollection from the trigger element'])
        s.add(95173,['RuntimeError: could not insert file','into PoolFileCatalog','line 37, in memoize'])
        s.add(95212,"RuntimeError: Don't know how to configure conditionsTag for file_type: None")
        s.add(95256,['ImportError: No module named DBReplicaSvc.DBReplicaSvcConf'])
        s.add(92598,['corrupted unsorted chunks','AllPT_HI_menu'])
        s.add(95281,["ToolSvc.InDetTrigPrdAssociationTool","ERROR track already found in cache"])
        s.add(95413,["ERROR Unable to retrieve EMAltTrackIsolationTool"])
        s.add(95430,["ImportError: No module named MuidStatistics.MuidStatisticsConf"])
        s.add(95135,["LArHVToolDB.cxx","received fatal signal 6"])
        s.add(95547,["failed to get an object of class \'Partition\' via relationship \'InitialPartition\'"])
        s.add(95547,["WARNING Problems retrieving relation \"InitialPartition\"","ERROR oks_dump reports status `5\'"])
        #s.add(95550,["[CORBA::Object* ipc::util::resolve(...) at ipc/src/util.cc:369]","\"RunParams\" of the \"is/repository\""])
        s.add(95605,["ERROR could not get handle to TrigEgammaPhotonCutIDTool","ValueError:"])
        s.add(95607,["Reconstruction/egamma/egammaPIDTools/cmt/../src/egammaPhotonCutIDTool.cxx:591"])
	s.add(95616,["ImportError: No module named TrigInDetAnalysisExample.TrigInDetAnalysisExampleConf"])
        s.add(95622,["RuntimeError: RootController did not exit in 60 seconds","Timeout reached waiting for transition to BOOTED"])
        s.add(95623,["ERROR Errors while decoding TrigElectronContainer_p3","WARNING: no directory and/or release sturucture found"])
        s.add(95640,["IOVSvcTool::preLoadProxies \(this=0x1e486a00\) at ../src/IOVSvcTool.cxx:986"])
        s.add(95657,["ValueError:  Physics_HI_v2 is not the expected type and/or the value is not allowed for: JobProperties.Rec.Trigger.triggerMenuSetup"])
        s.add(95658,["THistSvc","ERROR already registered an object with identifier \"/EXPERT/L2MetHypo","/Hypo"])
        s.add(95658,["THistSvc","ERROR already registered an object with identifier \"/EXPERT/EFMetHypo","/Hypo"])
        s.add(95661,["FATAL Failed to retrieve ConditionsSummaryTool = ServiceHandle\(\'TRT_ConditionsSummarySvc/InDetTRTConditionsSummaryService\'\)"])
        s.add(95661,["FATAL Failed to retrieve ConditionsSummaryTool = ServiceHandle\(\'TRT_ConditionsSummarySvc/InDetTrigInDetTRTConditionsSummaryService\'\)"])
        s.add(95680,["Error in <TCint::AutoLoadCallback>: failure loading library ARA_RecTPCnvDict.so for class CaloEnergyCnv_p2","\'CaloEnergyCnv_p2\' has no attribute \'registerStreamerConverter\'"])
        s.add(95686,["ERROR Tag OFLCOND-DR-BS7T-ANom","cannot be resolved for folder /TRT/Cond/StatusHT"])
        s.add(95692,["Waiting for ManyPropagableCommand to finish:  99/100 seconds","if ret != 0 and ret != 5: raise PropagationException"])
        s.add(95696,["histmon::THistRegisterImpl::HInfo::get","at ../src/THistRegisterImpl.cxx:82"])
        s.add(95696,["histmon::THistRegisterImpl::HInfo::get","at ../src/TConvertingBranchElement.cxx:943"])
        s.add(95732,["diff: HLTMenu_frontier.xml: No such file or directory","ERROR HLT menus are not identical"])
        s.add(95753,["Basic Python configuration failed","No such file or directory: \'LVL1config_Physics_HI_v2_17.1.5.xml\'"])
        s.add(95737,["FATAL Cannot locate MagField  from \$\{DATAPATH\}"])
        s.add(95737,["FATAL Cannot locate MagneticFieldMaps/bmagatlas_09_fullAsym20400.data.bz2 from \$\{DATAPATH\}"])
        s.add(95804,["ERROR Upload of SMKey failed","No such file or directory: \'../AllPT_HI_menu/ef_Default_setup.txt\'"])
        s.add(95812,["glibc detected","/afs/cern.ch/sw/lcg/external/Python/2.6.5/i686-slc5-gcc43-opt/bin/python: malloc\(\): memory corruption: 0x0cd76e08"])
        s.add(95855,"UploadHIV2MenuKeys/exportMenuKeys.sh: No such file or directory")
        s.add(95915,"Error initializing tool 'TrigTauRecMerged_Tau2012.TrigTau_EnergyCalibrationLC_onlyEnergy'")
        s.add(95915,"Error initializing tool 'TrigTauRecMerged_Tau.TrigTau_EnergyCalibrationLC_onlyEnergy'")
        s.add(95948,["in HistorySvc::listProperties","psc::Psc::pscStopRun","at ../src/Psc.cxx:692"])
        s.add(95965,["in TEmulatedCollectionProxy::InitializeEx","in TEmulatedMapProxy::TEmulatedMapProxy"])
        s.add(95970,["problem picking a data reader for file","testBphysicsSliceAthenaTrigRDO_Kstar"])
        s.add(95971,["Errors while decoding TrigInDetTrackCollection_tlp2"])
        s.add(95986,["/src/rbmaga.F:82","/src/setmagfield.F:52"])
        s.add(95995,["Trigger menu inconsistent, aborting","L2 Chain counter 454 used 2 times while can only once, will print them all"])
        s.add(96087,["No such file or directory","HLTconfig_MC_pp_v4_loose_mc_prescale_17.2.4.3.xml"])
        s.add(96092,["AthenaTrigBS_standalone_top_L2","TrigChainMoniValidation.reference: No such file or directory"])
        s.add(96093,["ByteStreamAttListMetadataSvc","not locate service"])
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
    
