#!/bin/bash

# Sets up a 32-bit athena release

RELEASE=17.0.6.13

export AtlasSetup=/afs/cern.ch/atlas/software/dist/AtlasSetup
source $AtlasSetup/scripts/asetup.sh ${RELEASE},32,here
export CLFAGS=-m32
export LDFLAGS=-m32
