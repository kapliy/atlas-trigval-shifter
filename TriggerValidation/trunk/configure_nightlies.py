#!/usr/bin/env python

# ATTENTION: make sure to replace the release string with rel_%d
# so that the script can automatically substitute the correct value!

"""
# TEMPLATE TO ADD A NIGHTLY:
N = Nightly('','')
N.add(Project('TrigP1Test',''))
N.add(Project('TriggerTest',''))
N.add(Project('TrigAnalysisTest',''))
X.append(N)
"""

# allow the user to select a subset of nightlies to be processed
# ALL - run over all enabled nightliers
# PART1 - CAFHLT and P1HLT that finished at 11 PM Chicago time
# PART2 - the largest fraction of the report; nightlies that finish by morning Chicago time
# PART3 - VAL2 releases that finish by noon Chicago time
ALL,PART1,PART2,PART3,PART4,TEST = range(6)
import sys
nightly_sel = ALL
if len(sys.argv)>=3:
    v = sys.argv[2]
    if v=='ALL': nightly_sel = ALL
    elif v in ('PART1','HLT','VAL'): nightly_sel = PART1
    elif v=='PART2': nightly_sel = PART2
    elif v in ('PART3','VAL2'): nightly_sel = PART3
    elif v in ('PART4'): nightly_sel = PART4
    elif v in ('PART5','TEST'): nightly_sel = TEST
    else:
        try:
            nightly_sel = int(v)
        except:
            nightly_sel = ALL
    if nightly_sel < ALL or nightly_sel > TEST:
        nightly_sel = ALL
print 'Nighlies selector =',nightly_sel

from Nightly import Nightly
from Project import Project

X = []

# high priority releases
N = Nightly('17.1.X.Y-VAL-P1HLT',' (32-bit)')
N.add(Project('TrigP1Test','http://atlas-computing.web.cern.ch/atlas-computing/links/buildDirectory/nightlies/17.1.X.Y-VAL/AtlasP1HLT/rel_%d/NICOS_area/NICOS_atntest171XYVALP1HLT32BS5G4P1HLTOpt/trigp1test_testconfiguration_work/'))
N.add(Project('TriggerTest','http://atlas-computing.web.cern.ch/atlas-computing/links/buildDirectory/nightlies/17.1.X.Y-VAL/AtlasP1HLT/rel_%d/NICOS_area/NICOS_atntest171XYVALP1HLT32BS5G4P1HLTOpt/triggertest_testconfiguration_work/'))
if nightly_sel in (PART1,ALL):
    pass # 10/25/2013 - disabling 17.1.X.Y-VAL-P1HLT
    #X.append(N)

N = Nightly('18.1.X.Y-VAL-P1HLT',' (32-bit)')
N.add(Project('TrigP1Test','http://atlas-computing.web.cern.ch/atlas-computing/links/buildDirectory/nightlies/18.1.X.Y-VAL/AtlasP1HLT/rel_%d/NICOS_area/NICOS_atntest181XYVALP1HLT64BS6G47P1HLTOpt/trigp1test_testconfiguration_work/'))
N.add(Project('TriggerTest','http://atlas-computing.web.cern.ch/atlas-computing/links/buildDirectory/nightlies/18.1.X.Y-VAL/AtlasP1HLT/rel_%d/NICOS_area/NICOS_atntest181XYVALP1HLT64BS6G47P1HLTOpt/triggertest_testconfiguration_work/'))
if nightly_sel in (PART1,ALL):
    pass
    #X.append(N)


N = Nightly('17.2.X.Y-VAL-Prod',' (64-bit)')
N.add(Project('TrigP1Test','http://atlas-computing.web.cern.ch/atlas-computing/links/buildDirectory/nightlies/17.2.X.Y-VAL/AtlasProduction/rel_%d/NICOS_area/NICOS_atntest172XYVALProd64BS5G4ProdOpt/trigp1test_testconfiguration_work/'))
N.add(Project('TriggerTest','http://atlas-computing.web.cern.ch/atlas-computing/links/buildDirectory/nightlies/17.2.X.Y-VAL/AtlasProduction/rel_%d/NICOS_area/NICOS_atntest172XYVALProd64BS5G4ProdOpt/triggertest_testconfiguration_work/'))
N.add(Project('TrigAnalysisTest','http://atlas-computing.web.cern.ch/atlas-computing/links/buildDirectory/nightlies/17.2.X.Y-VAL/AtlasProduction/rel_%d/NICOS_area/NICOS_atntest172XYVALProd64BS5G4ProdOpt/triganalysistest_testconfiguration_work/'))
if nightly_sel in (PART2,ALL): # this nightly sometimes finishes rather late
    X.append(N)
    
# lower-priority releases
N = Nightly('17.1.X',' (32-bit)')
N.add(Project('TrigP1Test','http://atlas-computing.web.cern.ch/atlas-computing/links/buildDirectory/nightlies/17.1.X/AtlasHLT/rel_%d/NICOS_area/NICOS_atntest171X32BS5G4AtlasHLTOpt/trigp1test_testconfiguration_work/'))
N.add(Project('TriggerTest','http://atlas-computing.web.cern.ch/atlas-computing/links/buildDirectory/nightlies/17.1.X/AtlasTrigger/rel_%d/NICOS_area/NICOS_atntest171X32BS5G4TrgOpt/triggertest_testconfiguration_work/'))
N.add(Project('TrigAnalysisTest','http://atlas-computing.web.cern.ch/atlas-computing/links/buildDirectory/nightlies/17.1.X/AtlasAnalysis/rel_%d/NICOS_area/NICOS_atntest171X32BS5G4AnlOpt/triganalysistest_testconfiguration_work/'))
if nightly_sel in (PART2,ALL):
    pass  # 07/28/2013 - disabling 17.1.X
    #X.append(N)

N = Nightly('17.1.X-VAL',' (32-bit)')
N.add(Project('TrigP1Test','http://atlas-computing.web.cern.ch/atlas-computing/links/buildDirectory/nightlies/17.1.X-VAL/AtlasHLT/rel_%d/NICOS_area/NICOS_atntest171XVAL32BS5G4AtlasHLTOpt/trigp1test_testconfiguration_work/'))
N.add(Project('TriggerTest','http://atlas-computing.web.cern.ch/atlas-computing/links/buildDirectory/nightlies/17.1.X-VAL/AtlasTrigger/rel_%d/NICOS_area/NICOS_atntest171XVAL32BS5G4TrgOpt/triggertest_testconfiguration_work/'))
N.add(Project('TrigAnalysisTest','http://atlas-computing.web.cern.ch/atlas-computing/links/buildDirectory/nightlies/17.1.X-VAL/AtlasAnalysis/rel_%d/NICOS_area/NICOS_atntest171XVAL32BS5G4AnlOpt/triganalysistest_testconfiguration_work/'))
if nightly_sel in (PART2,ALL): 
    pass
    #X.append(N) # 9/9 disabling 

N = Nightly('17.2.X',' (64-bit)')
#N.add(Project('TrigP1Test','http://atlas-computing.web.cern.ch/atlas-computing/links/buildDirectory/nightlies/17.2.X/AtlasHLT/rel_%d/NICOS_area/NICOS_atntest172X64BS5G4AtlasHLTOpt/trigp1test_testconfiguration_work/'))
N.add(Project('TriggerTest','http://atlas-computing.web.cern.ch/atlas-computing/links/buildDirectory/nightlies/17.2.X/AtlasTrigger/rel_%d/NICOS_area/NICOS_atntest172X64BS5G4TrgOpt/triggertest_testconfiguration_work/'))
N.add(Project('TrigAnalysisTest','http://atlas-computing.web.cern.ch/atlas-computing/links/buildDirectory/nightlies/17.2.X/AtlasAnalysis/rel_%d/NICOS_area/NICOS_atntest172X64BS5G4AnlOpt/triganalysistest_testconfiguration_work/'))
if nightly_sel in (PART2,ALL):
    X.append(N)
    
N = Nightly('17.2.X-VAL',' (64-bit)')
#N.add(Project('TrigP1Test','http://atlas-computing.web.cern.ch/atlas-computing/links/buildDirectory/nightlies/17.2.X-VAL/AtlasHLT/rel_%d/NICOS_area/NICOS_atntest172XVAL64BS5G4AtlasHLTOpt/trigp1test_testconfiguration_work/'))
N.add(Project('TriggerTest','http://atlas-computing.web.cern.ch/atlas-computing/links/buildDirectory/nightlies/17.2.X-VAL/AtlasTrigger/rel_%d/NICOS_area/NICOS_atntest172XVAL64BS5G4TrgOpt/triggertest_testconfiguration_work/'))
N.add(Project('TrigAnalysisTest','http://atlas-computing.web.cern.ch/atlas-computing/links/buildDirectory/nightlies/17.2.X-VAL/AtlasAnalysis/rel_%d/NICOS_area/NICOS_atntest172XVAL64BS5G4AnlOpt/triganalysistest_testconfiguration_work/'))
if nightly_sel in (PART2,ALL):
    X.append(N)
    
N = Nightly('19.X.0',' (64-bit)')
N.add(Project('TriggerTest','http://atlas-computing.web.cern.ch/atlas-computing/links/buildDirectory/nightlies/dev/AtlasTrigger/rel_%d/NICOS_area/NICOS_atntest19X064BS6G47TrgOpt/triggertest_testconfiguration_work/'))
N.add(Project('TrigAnalysisTest','http://atlas-computing.web.cern.ch/atlas-computing/links/buildDirectory/nightlies/dev/AtlasAnalysis/rel_%d/NICOS_area/NICOS_atntest19X064BS6G47AnlOpt/triganalysistest_testconfiguration_work/'))
N.add(Project('TrigP1Test','http://atlas-computing.web.cern.ch/atlas-computing/links/buildDirectory/nightlies/dev/AtlasHLT/rel_%d/NICOS_area/NICOS_atntest19X064BS6G47AtlasHLTOpt/trigp1test_testconfiguration_work/'))
if nightly_sel in (PART2,ALL):
    X.append(N)
    
N = Nightly('19.X.0-VAL',' (64-bit)')
N.add(Project('TriggerTest','http://atlas-computing.web.cern.ch/atlas-computing/links/buildDirectory/nightlies/devval/AtlasTrigger/rel_%d/NICOS_area/NICOS_atntest19X0VAL64BS6G47TrgOpt/triggertest_testconfiguration_work/'))
N.add(Project('TrigAnalysisTest','http://atlas-computing.web.cern.ch/atlas-computing/links/buildDirectory/nightlies/devval/AtlasAnalysis/rel_%d/NICOS_area/NICOS_atntest19X0VAL64BS6G47AnlOpt/triganalysistest_testconfiguration_work/'))
#N.add(Project('TrigP1Test','http://atlas-computing.web.cern.ch/atlas-computing/links/buildDirectory/nightlies/devval/AtlasHLT/rel_%d/NICOS_area/NICOS_atntest18X0VAL32BS6G47AtlasHLTOpt/trigp1test_testconfiguration_work/'))
if nightly_sel in (PART2,ALL):
    X.append(N)
    
# VAL2 nightlies finish around 11:30 AM Chicago time:

# Part 3 nightlies are not necessary currently (at least until the end of summer 2013)
N = Nightly('17.1.X.Y-VAL2-P1HLT',' (32-bit)')
N.add(Project('TrigP1Test','http://atlas-computing.web.cern.ch/atlas-computing/links/buildDirectory/nightlies/17.1.X.Y-VAL2/AtlasP1HLT/rel_%d/NICOS_area/NICOS_atntest171XYVAL2P1HLT32BS5G4P1HLTOpt/trigp1test_testconfiguration_work/'))
N.add(Project('TriggerTest','http://atlas-computing.web.cern.ch/atlas-computing/links/buildDirectory/nightlies/17.1.X.Y-VAL2/AtlasP1HLT/rel_%d/NICOS_area/NICOS_atntest171XYVAL2P1HLT32BS5G4P1HLTOpt/triggertest_testconfiguration_work/'))
if nightly_sel in (PART3,ALL):
    pass # 10/25/2013 - disabling 17.1.X.Y-VAL-P1HLT
    #print "NOTE: Part 3 nightlies are not necessary currently (at least until the end of summer 2013)"
    #X.append(N)

N = Nightly('18.1.X.Y-VAL2-P1HLT',' (32-bit)')
N.add(Project('TrigP1Test','http://atlas-computing.web.cern.ch/atlas-computing/links/buildDirectory/nightlies/18.1.X.Y-VAL2/AtlasP1HLT/rel_%d/NICOS_area/NICOS_atntest181XYVAL2P1HLT32BS5G4P1HLTOpt/trigp1test_testconfiguration_work/'))
N.add(Project('TriggerTest','http://atlas-computing.web.cern.ch/atlas-computing/links/buildDirectory/nightlies/18.1.X.Y-VAL2/AtlasP1HLT/rel_%d/NICOS_area/NICOS_atntest181XYVAL2P1HLT32BS5G4P1HLTOpt/triggertest_testconfiguration_work/'))
if nightly_sel in (PART3,ALL):
    print "NOTE: Part 3 nightlies are not necessary currently (at least until the end of summer 2013)"
    X.append(N)


# 17.1.X.Y.Z-VAL2-AtlasCAFHLT is obsolete (https://twiki.cern.ch/twiki/bin/viewauth/Atlas/TriggerValidation)
#N = Nightly('17.1.X.Y.Z-VAL2-AtlasCAFHLT',' (32-bit)')
#N.add(Project('TrigP1Test','http://atlas-computing.web.cern.ch/atlas-computing/links/buildDirectory/nightlies/17.1.X.Y.Z-VAL2/AtlasCAFHLT/rel_%d/NICOS_area/NICOS_atntest171XYZVAL2AtlasCAFHLT32BS5G4AtlasCAFHLTOpt/trigp1test_testconfiguration_work/'))
# the following may need to be commented out because TriggerTest is not always present in this nightly.
#N.add(Project('TriggerTest','http://atlas-computing.web.cern.ch/atlas-computing/links/buildDirectory/nightlies/17.1.X.Y.Z-VAL2/AtlasCAFHLT/rel_%d/NICOS_area/NICOS_atntest171XYZVAL2AtlasCAFHLT32BS5G4AtlasCAFHLTOpt/triggertest_testconfiguration_work/'))
#if nightly_sel in (PART3,ALL):
#    X.append(N)

# testing
N = Nightly('19.X.0',' (64-bit) TESTING')
N.add(Project('TrigP1Test','http://atlas-computing.web.cern.ch/atlas-computing/links/buildDirectory/nightlies/dev/AtlasHLT/rel_%d/NICOS_area/NICOS_atntest19X064BS6G47AtlasHLTOpt/trigp1test_testconfiguration_work/'))
if nightly_sel in (PART4,):
    X.append(N)
