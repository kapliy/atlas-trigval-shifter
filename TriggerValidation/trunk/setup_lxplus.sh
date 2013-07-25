#!/bin/bash

# Sets up a 32-bit athena release

RELEASE=17.0.6.13
NEED_SETUP=1
uname -r | grep -q 'el6' && NEED_SETUP=0

# on SLC5, source a version of athena that comes with Python 2.6
# (not needed on SLC6)
if [ "${NEED_SETUP}" == "1" ]; then
    export AtlasSetup=/afs/cern.ch/atlas/software/dist/AtlasSetup
    source $AtlasSetup/scripts/asetup.sh ${RELEASE},32,here
    export CLFAGS=-m32
    export LDFLAGS=-m32
fi

# set ORACLE_HOME
source /afs/cern.ch/project/oracle/script/setoraenv.sh -s prod
