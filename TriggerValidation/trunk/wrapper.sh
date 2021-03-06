#!/bin/bash

# a wrapper around run.py that runs automatically via crontab
# To schedule for every 30 minutes edit cron.tab and then run:
# "crontab cron.tab"

MYEMAIL="$USER@localhost"
DEST=$PWD
SCPADDR=""
DBYS="0"

if [ "$HOSTNAME" == "kapliy" ]; then
    echo "Running on Anton's machine!"
    MYEMAIL="kapliy@gmail.com"
    DEST=/hep/public_html/VAL
fi

if [ "$HOSTNAME" == "Jordan-Websters-MacBook-Pro.local" ]; then
    echo "Running on Jordan's machine!"
    MYEMAIL="jwebste2@gmail.com"
    SCPADDR="jswebster@cdf.uchicago.edu:public_html/VAL/"
fi

rel=`date '+%w'`
part=0

# adjust for chicago-CERN time
# choose which PART to run
hour=`echo $(date '+%k')`
if [ "$hour" -gt "18" ]; then
    part=1
    rel=`expr $rel + 1`
    if [ "$rel" -ge "7" ]; then
	rel=0
    fi
elif [ "$hour" -lt "4" ]; then
    part=1
elif [ "$hour" -lt "10" ]; then
    part=2
else
    part=3
fi

verbose=0
if [ "$#" == "2" ]; then
    rel=$1
    part=$2
    verbose=1
    echo "Over-riding rel and part from command line: ${rel} and ${part}"
fi

# get the latest version of the code:
svn update

echo "PWD = $PWD"
echo "DEST = ${DEST}"
echo "REL = ${rel}   PART = ${part}"

# Prepare the shift report
for dby in ${DBYS}; do
    if [ "${verbose}" == "1" ]; then
	./run.py ${rel} ${part} ${dby} index2_dby${dby}.html
    else
	./run.py ${rel} ${part} ${dby} index2_dby${dby}.html &> ${DEST}/log_dby${dby}_part${part}.txt &
    fi;
done
wait
# Back up a copy of the output
for dby in ${DBYS}; do
    cp ${DEST}/index2_dby${dby}.html ${DEST}/index_dby${dby}_part${part}.html
    if [ "${SCPADDR}" != "" ]; then
	scp ${DEST}/index_dby${dby}_part${part}.html ${SCPADDR}
    fi
done

# RTT tests
DO_RTT=1
if [ "$#" -gt "0" ];then
    echo "Disabling rtt.py"
    DO_RTT=0
fi
if [ "${DO_RTT}" -eq "1" ]; then
    echo "RTT TESTS:" > ${DEST}/rtt.txt
    echo "" >> ${DEST}/rtt.txt
    echo "" >> ${DEST}/rtt.txt
    ./rtt.py 0 1.1 ${rel} >> ${DEST}/rtt.txt
    echo "" >> ${DEST}/rtt.txt
    echo "" >> ${DEST}/rtt.txt
    ./rtt.py 1 1.1 ${rel} >> ${DEST}/rtt.txt
    echo "" >> ${DEST}/rtt.txt
    echo "" >> ${DEST}/rtt.txt
    ./rtt.py 2 1.1 ${rel} >> ${DEST}/rtt.txt
fi

nskip=`grep -c 'skipping release' ${DEST}/log_dby0_part${part}.txt`
if [ "${nskip}" == "0" ]; then
    echo "All nightlies finished successfully on `date`" >> ${DEST}/log_dby0_part${part}.txt
    echo "Top link:  http://hep.uchicago.edu/~antonk/VAL" >> ${DEST}/log_dby0_part${part}.txt
    echo "This test: http://hep.uchicago.edu/~antonk/VAL/index_dby0_part${part}.html" >> ${DEST}/log_dby0_part${part}.txt
    echo "" >> ${DEST}/log_dby0_part${part}.txt
    echo "Cheers," >> ${DEST}/log_dby0_part${part}.txt
    echo "Your faithful AutoShifter" >> ${DEST}/log_dby0_part${part}.txt
    cat ${DEST}/log_dby0_part${part}.txt | mail -s "`date +%D`: TrigVal shifts: REL = ${rel} PART = ${part}" ${MYEMAIL}
fi
echo "DONE"
