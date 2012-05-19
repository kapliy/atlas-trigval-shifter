#!/bin/bash

# a wrapper around run.py that runs automatically via crontab
# To schedule for every 30 minutes edit cron.tab and then run:
# "crontab cron.tab"

MYEMAIL="$USER@localhost"
DEST=$PWD

if [ "$HOSTNAME" == "kapliy" ]; then
    echo "Running on Anton's machine!"
    MYEMAIL="kapliy@gmail.com"
    DEST=/hep/public_html/VAL
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
cp ${DEST}/index2.html ${DEST}/index_stable.html

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

nskip=`grep -c 'skipping release' ${DEST}/log.txt`
if [ "${nskip}" == "0" ]; then
    echo "All nightlies finished successfully on `date`" >> ${DEST}/log.txt
    echo 'LINK: http://hep.uchicago.edu/~antonk/VAL' >> ${DEST}/log.txt
    cat ${DEST}/log.txt | mail -s "`date +%D`: TrigVal shifts: REL = ${rel} PART = ${part}" ${MYEMAIL}
fi
echo "DONE"
