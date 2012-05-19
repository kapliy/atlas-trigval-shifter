#!/usr/bin/env python

import urllib2
import BeautifulSoup
import re,os

class Nightly:
    """ One nightly cache along with a URL to its NICOS path
    name = 17.1.X.Y-VAL-P1HLT 
    nicos = URL_TO_NICOS_PAGE (make sure to substitute release number with %d)
    PS - nicos URL is optional
    """
    rel = 0
    def __init__(s,name):
        s.name = name
        s.projects = []
        # link and contents of the NICOS *build* page
        s.nicoslinks = None
        s.errorpackages = []
        s.errorlinks    = []
        # keep track of new bug reports
        s.new_bugs = []
    def add(s,project):
        s.projects.append(project)
    def load(s):
        assert len(s.projects)>0,'Detected empty nightly without any projects associated with it'
        print 'Working on nightly:',s.name,'rel_%d'%s.rel
        status = [p.load() for p in s.projects]
        # extract a NICOS link to be able to detect build errors.
        # If this throws errors, you'll have to check for build errors manually
        try:
            nicoslinks = []
            for p in s.projects:
                nicos = str(p.pres_soup.findAll('script')[-2].string.split(',')[1].replace('"','').replace(')',''))
                nicoslinks.append(nicos)
            nicoslinks = list(set(nicoslinks))
            # this also acts as a validation for user's input of ATN links for this nightly:
            assert len(nicoslinks)>0,'Unable to locate a link to NICOS build summary table'
            s.nicoslinks = nicoslinks
            for nicoslink in s.nicoslinks:
                # now check nicos page for any build errors (those don't get reported by ATN!)
                data = urllib2.urlopen(nicoslink)
                # fix some buggy html (align tag outside of parent tag) before parsing
                soup = BeautifulSoup.BeautifulSoup(data.read().replace('<align=center >',''))
                table = soup.find('table',{'cellspacing':'10%'})
                rows = table.findAll('tr')
                assert len(rows)>0,'Cannot find any records in NICOS build summary table'
                errorpackages = []
                errorlinks = []
                for row in rows[1:]:
                    if row.find('img',src='cross_red.gif'):
                        errorpackages.append( row.contents[0].a.string )
                        nicosdir = os.path.dirname(nicoslink)
                        errorlinks.append( nicosdir + '/' + row.contents[0].a['href'] )
                s.errorpackages += errorpackages
                s.errorlinks += errorlinks
        except:
            print 'WARNING: unable to parse the NICOS build page. Build errors will NOT be detected!'
            #raise # enable for debugging
    def report(s):
        res = []
        res.append('')
        res.append('')
        # provide links to build summary
        if len(s.nicoslinks)>0:
            rel = '(rel_%d)'%s.rel + ' | build links: ' + ' '.join( ['<a href="%s">%d</a>'%(nicoslink,i+1) for i,nicoslink in enumerate(s.nicoslinks)] )
        else:
            rel = '(rel_%d)'
        res.append('%s %s'%(s.name,rel))
        res.append( '' + '='*len(s.name) )
        if len(s.errorpackages)>0:
            res.append('<font color="#FF6666">Build errors:</font>')
            iprinted=0
            for package,blink in zip(s.errorpackages,s.errorlinks):
                res.append('<a href="%s">%s</a>'%(blink,package))
                iprinted += 1
                if iprinted>=10:
                    res.append( '... and more (please check the build links above)' )
                    break
        for p in s.projects:
            res += p.report()
            s.new_bugs += p.new_bugs
        s.new_bugs = list(set(s.new_bugs))
        return res
