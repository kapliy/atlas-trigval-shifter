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

from Nightly import Nightly
from Project import Project

X = []

# high priority releases
N = Nightly('17.1.X.Y-VAL-P1HLT (32-bit)')
N.add(Project('TrigP1Test','http://atlas-computing.web.cern.ch/atlas-computing/links/buildDirectory/nightlies/17.1.X.Y-VAL/AtlasP1HLT/rel_%d/NICOS_area/NICOS_atntest171XYVALP1HLT32BS5G4P1HLTOpt/trigp1test_testconfiguration_work/'))
N.add(Project('TriggerTest','http://atlas-computing.web.cern.ch/atlas-computing/links/buildDirectory/nightlies/17.1.X.Y-VAL/AtlasP1HLT/rel_%d/NICOS_area/NICOS_atntest171XYVALP1HLT32BS5G4P1HLTOpt/triggertest_testconfiguration_work/'))
X.append(N)

N = Nightly('17.1.X.Y.Z-VAL-AtlasCAFHLT (32-bit)')
N.add(Project('TrigP1Test','http://atlas-computing.web.cern.ch/atlas-computing/links/buildDirectory/nightlies/17.1.X.Y.Z-VAL/AtlasCAFHLT/rel_%d/NICOS_area/NICOS_atntest171XYZVALAtlasCAFHLT32BS5G4AtlasCAFHLTOpt/trigp1test_testconfiguration_work/'))
N.add(Project('TriggerTest','http://atlas-computing.web.cern.ch/atlas-computing/links/buildDirectory/nightlies/17.1.X.Y.Z-VAL/AtlasCAFHLT/rel_%d/NICOS_area/NICOS_atntest171XYZVALAtlasCAFHLT32BS5G4AtlasCAFHLTOpt/triggertest_testconfiguration_work/'))
X.append(N)

N = Nightly('17.1.X.Y-VAL2-P1HLT (32-bit)')
N.add(Project('TrigP1Test','http://atlas-computing.web.cern.ch/atlas-computing/links/buildDirectory/nightlies/17.1.X.Y-VAL2/AtlasP1HLT/rel_%d/NICOS_area/NICOS_atntest171XYVAL2P1HLT32BS5G4P1HLTOpt/trigp1test_testconfiguration_work/'))
N.add(Project('TriggerTest','http://atlas-computing.web.cern.ch/atlas-computing/links/buildDirectory/nightlies/17.1.X.Y-VAL2/AtlasP1HLT/rel_%d/NICOS_area/NICOS_atntest171XYVAL2P1HLT32BS5G4P1HLTOpt/triggertest_testconfiguration_work/'))
X.append(N)

N = Nightly('17.1.X.Y.Z-VAL2-AtlasCAFHLT (32-bit)')
N.add(Project('TrigP1Test','http://atlas-computing.web.cern.ch/atlas-computing/links/buildDirectory/nightlies/17.1.X.Y.Z-VAL2/AtlasCAFHLT/rel_%d/NICOS_area/NICOS_atntest171XYZVAL2AtlasCAFHLT32BS5G4AtlasCAFHLTOpt/trigp1test_testconfiguration_work/'))
# the following may need to be commented out because TriggerTest is not always present in this nightly.
N.add(Project('TriggerTest','http://atlas-computing.web.cern.ch/atlas-computing/links/buildDirectory/nightlies/17.1.X.Y.Z-VAL2/AtlasCAFHLT/rel_%d/NICOS_area/NICOS_atntest171XYZVAL2AtlasCAFHLT32BS5G4AtlasCAFHLTOpt/triggertest_testconfiguration_work/'))
X.append(N)

N = Nightly('17.1.X.Y-VAL-Prod (32-bit)')
N.add(Project('TrigP1Test','http://atlas-computing.web.cern.ch/atlas-computing/links/buildDirectory/nightlies/17.1.X.Y-VAL/AtlasProduction/rel_%d/NICOS_area/NICOS_atntest171XYVALProd32BS5G4ProdOpt/trigp1test_testconfiguration_work/'))
N.add(Project('TriggerTest','http://atlas-computing.web.cern.ch/atlas-computing/links/buildDirectory/nightlies/17.1.X.Y-VAL/AtlasProduction/rel_%d/NICOS_area/NICOS_atntest171XYVALProd32BS5G4ProdOpt/triggertest_testconfiguration_work/'))
N.add(Project('TrigAnalysisTest','http://atlas-computing.web.cern.ch/atlas-computing/links/buildDirectory/nightlies/17.1.X.Y-VAL/AtlasProduction/rel_%d/NICOS_area/NICOS_atntest171XYVALProd32BS5G4ProdOpt/triganalysistest_testconfiguration_work/'))
#X.append(N)  # I was asked to only check the 64-bit cache

N = Nightly('17.1.X.Y-VAL-Prod (64-bit)')
N.add(Project('TrigP1Test','http://atlas-computing.web.cern.ch/atlas-computing/links/buildDirectory/nightlies/17.1.X.Y-VAL/AtlasProduction/rel_%d/NICOS_area/NICOS_atntest171XYVALProd64BS5G4ProdOpt/trigp1test_testconfiguration_work/'))
N.add(Project('TriggerTest','http://atlas-computing.web.cern.ch/atlas-computing/links/buildDirectory/nightlies/17.1.X.Y-VAL/AtlasProduction/rel_%d/NICOS_area/NICOS_atntest171XYVALProd64BS5G4ProdOpt/triggertest_testconfiguration_work/'))
N.add(Project('TrigAnalysisTest','http://atlas-computing.web.cern.ch/atlas-computing/links/buildDirectory/nightlies/17.1.X.Y-VAL/AtlasProduction/rel_%d/NICOS_area/NICOS_atntest171XYVALProd64BS5G4ProdOpt/triganalysistest_testconfiguration_work/'))
X.append(N)

# lower-priority releases
N = Nightly('17.1.X (32-bit)')
N.add(Project('TrigP1Test','http://atlas-computing.web.cern.ch/atlas-computing/links/buildDirectory/nightlies/17.1.X/AtlasHLT/rel_%d/NICOS_area/NICOS_atntest171X32BS5G4AtlasHLTOpt/trigp1test_testconfiguration_work/'))
N.add(Project('TriggerTest','http://atlas-computing.web.cern.ch/atlas-computing/links/buildDirectory/nightlies/17.1.X/AtlasTrigger/rel_%d/NICOS_area/NICOS_atntest171X32BS5G4TrgOpt/triggertest_testconfiguration_work/'))
N.add(Project('TrigAnalysisTest','http://atlas-computing.web.cern.ch/atlas-computing/links/buildDirectory/nightlies/17.1.X/AtlasAnalysis/rel_%d/NICOS_area/NICOS_atntest171X32BS5G4AnlOpt/triganalysistest_testconfiguration_work/'))
X.append(N)

N = Nightly('17.1.X-VAL (32-bit)')
N.add(Project('TrigP1Test','http://atlas-computing.web.cern.ch/atlas-computing/links/buildDirectory/nightlies/17.1.X-VAL/AtlasHLT/rel_%d/NICOS_area/NICOS_atntest171XVAL32BS5G4AtlasHLTOpt/trigp1test_testconfiguration_work/'))
N.add(Project('TriggerTest','http://atlas-computing.web.cern.ch/atlas-computing/links/buildDirectory/nightlies/17.1.X-VAL/AtlasTrigger/rel_%d/NICOS_area/NICOS_atntest171XVAL32BS5G4TrgOpt/triggertest_testconfiguration_work/'))
N.add(Project('TrigAnalysisTest','http://atlas-computing.web.cern.ch/atlas-computing/links/buildDirectory/nightlies/17.1.X-VAL/AtlasAnalysis/rel_%d/NICOS_area/NICOS_atntest171XVAL32BS5G4AnlOpt/triganalysistest_testconfiguration_work/'))
X.append(N)

N = Nightly('17.2.X (64-bit)')
N.add(Project('TrigP1Test','http://atlas-computing.web.cern.ch/atlas-computing/links/buildDirectory/nightlies/17.2.X/AtlasHLT/rel_%d/NICOS_area/NICOS_atntest172X64BS5G4AtlasHLTOpt/trigp1test_testconfiguration_work/'))
N.add(Project('TriggerTest','http://atlas-computing.web.cern.ch/atlas-computing/links/buildDirectory/nightlies/17.2.X/AtlasTrigger/rel_%d/NICOS_area/NICOS_atntest172X64BS5G4TrgOpt/triggertest_testconfiguration_work/'))
N.add(Project('TrigAnalysisTest','http://atlas-computing.web.cern.ch/atlas-computing/links/buildDirectory/nightlies/17.2.X/AtlasAnalysis/rel_%d/NICOS_area/NICOS_atntest172X64BS5G4AnlOpt/triganalysistest_testconfiguration_work/'))
X.append(N)

N = Nightly('17.2.X-VAL (64-bit)')
N.add(Project('TrigP1Test','http://atlas-computing.web.cern.ch/atlas-computing/links/buildDirectory/nightlies/17.2.X-VAL/AtlasHLT/rel_%d/NICOS_area/NICOS_atntest172XVAL64BS5G4AtlasHLTOpt/trigp1test_testconfiguration_work/'))
N.add(Project('TriggerTest','http://atlas-computing.web.cern.ch/atlas-computing/links/buildDirectory/nightlies/17.2.X-VAL/AtlasTrigger/rel_%d/NICOS_area/NICOS_atntest172XVAL64BS5G4TrgOpt/triggertest_testconfiguration_work/'))
N.add(Project('TrigAnalysisTest','http://atlas-computing.web.cern.ch/atlas-computing/links/buildDirectory/nightlies/17.2.X-VAL/AtlasAnalysis/rel_%d/NICOS_area/NICOS_atntest172XVAL64BS5G4AnlOpt/triganalysistest_testconfiguration_work/'))
X.append(N)

N = Nightly('17.X.0 (64-bit)')
N.add(Project('TriggerTest','http://atlas-computing.web.cern.ch/atlas-computing/links/buildDirectory/nightlies/dev/AtlasTrigger/rel_%d/NICOS_area/NICOS_atntest17X064BS5G4TrgOpt/triggertest_testconfiguration_work/'))
N.add(Project('TrigAnalysisTest','http://atlas-computing.web.cern.ch/atlas-computing/links/buildDirectory/nightlies/dev/AtlasAnalysis/rel_%d/NICOS_area/NICOS_atntest17X064BS5G4AnlOpt/triganalysistest_testconfiguration_work/'))
X.append(N)
