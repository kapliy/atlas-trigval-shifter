#!/usr/bin/env python

# enable tab completion
try:
    import readline
except ImportError:
    print "Module readline not available."
else:
    import rlcompleter
    readline.parse_and_bind("tab: complete")

import sys,re
import urllib2,httplib
import BeautifulSoup as bs

rel = 2
rtt = 0
THRESHOLD=1.10
useMax=False

urls = []
urls.append(['TrigP1Test','http://atlas-project-trigger-release-validation.web.cern.ch/atlas-project-trigger-release-validation/www/perfmonrtt/TrigP1Test.html'])
urls.append(['TriggerTest','http://atlas-project-trigger-release-validation.web.cern.ch/atlas-project-trigger-release-validation/www/perfmonrtt/TriggerTest.html'])
urls.append(['TrigAnalysisTest','http://atlas-project-trigger-release-validation.web.cern.ch/atlas-project-trigger-release-validation/www/perfmonrtt/TrigAnalysisTest.html'])


if len(sys.argv)>=2:
    rtt = int(sys.argv[1])
    assert rtt<len(urls),'rtt index has a maximum value of %d'%len(urls)
    print 'Changed rtt index to:',rtt
if len(sys.argv)>=3:
    THRESHOLD = float(sys.argv[2])
    assert THRESHOLD>=1.0 and THRESHOLD<=2.0,'THRESHOLD must be between 1.0 and 2.0'
    print 'Changed threshold to: %.1f%%'%((THRESHOLD-1.0)*100.0)
if len(sys.argv)>=4:
    rel = int(sys.argv[3])
    assert rel>=0 and rel<=6,'Release must be an integer between 0 and 6'
    print 'Changed release to:',rel
if len(sys.argv)>=5:
    useMax = bool(sys.argv[4])
    if useMax:
        print "Using maximum of last week for comparison"
    else:
        print "Using minimum of last week for comparison"

url = urls[rtt]

print 'Downloading RTT table for:',url[0]
soup = bs.BeautifulSoup( urllib2.urlopen(url[1]) if url[1][0:4]=='http' else open(url[1]) )
table = soup.table
rows = table.findAll('tr')

print 'Parsing RTT table for:',url[0]
testName='UNKNOWN'
stats = {}

def mems_to_tuple(m):
    """ Parses a string 2035M/35.0k into two tuples 
    Total is returned in megabytes; per/event is returned in kilobytes
    """
    pair = m.split('/')
    tot=-1
    per=-1
    if len(pair)==2 and pair[0]!='n':
        tot = float(pair[0][:-1])
        if pair[0][-1]=='M': tot*=1E6
        if pair[0][-1]=='k': tot*=1E3
        per = float(pair[1][:-1])
        if pair[1][-1]=='M': per*=1E6
        if pair[1][-1]=='k': per*=1E3
    return (tot/1E6,per/1E3)
        
for row in rows[1:]:
    elm = row.find('td',{ "class" : "testName" })
    if elm:
        testName = str(elm.string)
        continue
    try:
        build = str(row['id'])
    except:
        print 'Finished test',testName
        continue
    if not build:
        print 'WARNING: skipping row:',row
        continue
    td = row.findAll('td')
    mems = [ (str(cell.span.string) if cell.string not in ('?','n/a') else 'NONE') for cell in td[1:8]]
    if testName not in stats:
        stats[testName] = {}
    stats[testName][build] = [mems_to_tuple(z) for z in mems]

def avg(L):
    if len(L)>0:
        return float(sum(L)) / len(L)
    else: return -1
def prel(r):
    """ A simple function to return previous release """
    return r-1 if r>0 else 6

print '=================================================='
print 'REPORTING TESTS WITH >%.1f%% INCREASE IN MEMORY USAGE'%((THRESHOLD-1.0)*100.0)
print '=================================================='
print url[0]+':'
for testName in stats.keys():
    for build in stats[testName].keys():
        res = stats[testName][build]
        pres = res[rel]
        oldtot = max([data[0] for i,data in enumerate(res) if i!=rel])
        oldavg = avg([data[0] for i,data in enumerate(res) if i!=rel and data[0]>0])
        if len([data[0] for i,data in enumerate(res) if i!=rel and data[0]> 0]) > 0:
            oldmin = min([data[0] for i,data in enumerate(res) if i!=rel and data[0]> 0])
        else:
            #print "using average! %s" %oldavg
            oldmin = oldavg
        newtot = max([data[0] for i,data in enumerate(res) if i==rel])
        yestot = max([data[0] for i,data in enumerate(res) if i==prel(rel)])
        
        if useMax and newtot>0 and newtot/oldtot > THRESHOLD:
            print '- %s (%s):'%(testName,build)
            '{0:<4}'.format(999)
            print '   TODAY            = |{0:<4} MB|'.format(newtot)
            print '   YESTERDAY        = |{0:<4} MB|'.format(yestot if yestot>0 else 'N/A')
            print '   AVG_LAST_WEEK    = |{0:<4} MB|'.format(oldavg)
            print '   MAX_LAST_WEEK    = |{0:<4} MB|'.format(oldtot)
            print '   MIN_LAST_WEEK    = |{0:<4} MB|'.format(oldmin)
        if not useMax and newtot>0 and  newtot/oldmin > THRESHOLD:
            print '- %s (%s):'%(testName,build)
            '{0:<4}'.format(999)
            print '   TODAY            = |{0:<4} MB|'.format(newtot)
            print '   YESTERDAY        = |{0:<4} MB|'.format(yestot if yestot>0 else 'N/A')
            print '   AVG_LAST_WEEK    = |{0:<4} MB|'.format(oldavg)
            print '   MAX_LAST_WEEK    = |{0:<4} MB|'.format(oldtot)
            print '   MIN_LAST_WEEK    = |{0:<4} MB|'.format(oldmin)
print '=================================================='
print 'DONE'
print '=================================================='
