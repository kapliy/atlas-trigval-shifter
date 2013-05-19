#!/bin/bash

dest=$HOME/oracle_bin
payload=payload.tar.bz2

export ORACLE_ENV_ALREADY_SET=0
function set_oracle_env() {
    if [ "${ORACLE_ENV_ALREADY_SET}" == "0" ]; then
	export LD_LIBRARY_PATH=${LD_LIBRARY_PATH}:${dest}
	export PATH=${PATH}:${dest}
	export ORACLE_HOME=${dest}
	export NLS_LANG=AMERICAN_AMERICA.US7ASCII
	export ORACLE_ENV_ALREADY_SET=1
    fi
}

if [ ! -f ${dest}/libclntsh.so ]; then
    ROOTDIR=$PWD
    mkdir -p ${dest}
    echo "Please wait: installing Oracle bindings ..."
    tar xfj ${payload}
    cp -a payload/* ${dest}
    rm -rf payload
    cd ${dest}
    ln -s libocci.so.11.1 libocci.so
    ln -s libclntsh.so.11.1 libclntsh.so
    set_oracle_env
    # build and install the python library
    cd cx_oracle_source
    python setup.py build && python setup.py install --prefix=${dest}/cx_oracle
    st=$?
    cd ${dest}
    rm -rf cx_oracle_source
    cd $ROOTDIR
    if [ "$st" != "0" ]; then
	echo """
        ERROR: INSTALLATION FAILED.
        Please examine the error messages above.
        If you see complaints about libaio, install it from repositories. E.g., on Ubuntu:
        > sudo aptitude install libaio1
        """
	rm -rf ${dest}
	return 1 2>/dev/null
	exit 1
    else
	echo "Compilation succeeded"
    fi
fi

set_oracle_env

nfind=`find ${dest}/cx_oracle -type f -name cx_Oracle.so | wc -l`
if [ "${nfind}" == "1" ]; then
    oraclib=`find ${dest}/cx_oracle -type f -name cx_Oracle.so`
    export PYTHONPATH=${PYTHONPATH}:`dirname ${oraclib}`
    cp ../tnsnames.ora ${ORACLE_HOME}
    echo "cx_Oracle installed in: ${oraclib}"
    python -c "import cx_Oracle" &> /dev/null
    st=$?
    if [ "$st" == "0" ]; then
	echo "GOOD: Oracle bindings are ready!"
    else
	echo "ERROR: cannot use Oracle bindings. Try to run again after 'rm -rf ${dest}'"
    fi
else
    echo "ERROR: unable to find cx_Oracle.so under: ${dest}/cx_oracle"
    return 1 2>/dev/null
    exit 1
fi

