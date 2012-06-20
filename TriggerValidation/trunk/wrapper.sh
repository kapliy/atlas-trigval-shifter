#!/bin/bash

# a wrapper around run.py that runs automatically via crontab
# To schedule for every 30 minutes edit cron.tab and then run:
# "crontab cron.tab"

MYEMAIL="$USER@localhost"
DEST=$PWD
SCPADDR=""

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
if [ "$hour" -gt "20" ]; then
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

# get the latest version of the code:
svn update

echo "PWD = $PWD"
echo "DEST = ${DEST}"
echo "REL = ${rel}   PART = ${part}"

# Prepare the shift report
./run.py ${rel} ${part} &> ${DEST}/log.txt
# Back up a copy of the output
cp ${DEST}/index2.html ${DEST}/index_part${part}.html
if [ "${SCPADDR}" != "" ]
then
    scp ${DEST}/index_part${part}.html ${SCPADDR}
fi

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

nskip=`grep -c 'skipping release' ${DEST}/log.txt`
if [ "${nskip}" == "0" ]; then
    echo "All nightlies finished successfully on `date`" >> ${DEST}/log.txt
    echo 'Top link:  http://hep.uchicago.edu/~jswebster/VAL' >> ${DEST}/log.txt
    echo "This test: http://hep.uchicago.edu/~jswebster/VAL/index_part${part}.html" >> ${DEST}/log.txt
    echo "" >> ${DEST}/log.txt
    echo "Cheers," >> ${DEST}/log.txt
    echo "Your faithful AutoShifter" >> ${DEST}/log.txt
    cat ${DEST}/log.txt | mail -s "`date +%D`: TrigVal shifts: REL = ${rel} PART = ${part}" ${MYEMAIL}
fi
echo "DONE"
