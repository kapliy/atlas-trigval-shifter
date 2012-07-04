#!/bin/bash

# A quick setup script for tier3 (uct3-s1/uct3-s3).
# This basically sets up a recent version of python.

#echo "Setting up voms-proxy. Please enter your grid password:"
#source /share/wlcg-client/setup.sh && voms-proxy-init -voms atlas -valid 999:0

atlasrepo=/cvmfs/atlas.cern.ch/repo/sw/software/x86_64-slc5-gcc43-opt/
export AtlasSetup=${atlasrepo}/17.1.4/AtlasSetup
echo "Please wait 20-30 seconds: setting up the tier3 computing environment"
source ${AtlasSetup}/scripts/asetup.sh --releasesarea=$atlasrepo 17.1.4.5,64

echo "You may start running the shift scripts now:)"
