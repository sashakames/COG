'''
Class responsible for listing and serving federation-wide projects.
'''

from django.contrib.sites.models import Site
from cog.models import Project, ProjectTag
import urllib2
import json

TIMEOUT = 5

class ProjectManager(object):
  
    def reload(self):
        '''Updates the list of remote projects from all peer sites.'''
        
        # list of peer sites
        sites = ["http://localhost:8001/share/projects/"]
        
        for site in sites:
            self._harvest(site)
        return sites
        
    def _associateProjects(self, objList, apDictList):
        
        # empty list of parents/peers/children
        objList.clear()
        for apdict in apDictList:
            short_name=apdict['short_name']
            site_domain=apdict['site_domain']
            try:
                aproject = Project.objects.get(short_name=short_name, 
                                               site__domain=site_domain)
                objList.add(aproject)
            except Project.DoesNotExist: # correct short name, wrong site ?
                print 'Associated project does not exist in local database: short_name=%s site_domain=%s, will ignore' % (apdict['short_name'], apdict['site_domain'])
                pass 
        
    def _getJson(self, url):
        '''Retrieves and parses a JSON document at some URL.'''
        
        try:
            opener = urllib2.build_opener()
            request = urllib2.Request(url)
            response = opener.open(request, timeout=TIMEOUT)
            jdoc = response.read()
            return json.loads(jdoc)
            
        except Exception as e:
            print 'Error retrieving url=%s' % url
            print e
            return None

            
        
    def _harvest(self, url):
        '''Harvests all information from a remote CoG instance.'''
        
        # use current site to prevent overriding local objects
        local_site = Site.objects.get_current()
        
        jobj = self._getJson(url)
        if jobj is not None:
            
            # load/create remote site by domain
            sdict = jobj["site"]
            
            # DO NOT OVERRIDE LOCAL OBJECTS
            if sdict['domain'] != local_site.domain: 
                
                remote_site, created = Site.objects.get_or_create(domain=sdict['domain'])
                if created:
                    print 'Created remote site: %s' % remote_site
                else:
                    print 'Remote site %s already existing' % remote_site
                remote_site.name = sdict["name"]
                remote_site.save()
                            
                # first loop to create ALL projects first
                for key, pdict in jobj["projects"].items():
                                  
                    short_name = pdict['short_name']
                    long_name = pdict['long_name']
                    site_domain = pdict['site_domain']
                    
                    # check site
                    if site_domain==remote_site.domain: # check project belongs to remote site
                        
                        if not Project.objects.filter(short_name=short_name).exists(): # avoid conflicts with existing projects, from ANY site
                            # create new project
                            Project.objects.create(short_name=short_name, long_name=long_name, site=remote_site, active=True)
                            print 'Created project=%s for site=%s in local database' % (short_name, remote_site)
                        else:
                            print 'Project with name:%s already exists' % short_name
                
                # second loop to update project attributes and associations
                for key, pdict in jobj["projects"].items():
                    
                    short_name = pdict['short_name']
                    long_name = pdict['long_name']
                    site_domain = pdict['site_domain']
                    
                    # check site
                    if site_domain==remote_site.domain: # check project belongs to remote site
                    
                        try:
                            # load existing project from remote site
                            project = Project.objects.get(short_name=short_name, site=remote_site)
                            print 'Loaded project: %s from site: %s' % (short_name, site_domain)
                            
                            # update project attributes
                            project.long_name = long_name
                            
                            # update project tags
                            project.tags.clear()
                            for tagname in pdict['tags']:
                                ptag, created = ProjectTag.objects.get_or_create(name=tagname)
                                project.tags.add(ptag)
                            
                            # update project associations
                            self._associateProjects(project.peers, pdict['peers'])
                            print 'Updated project peers=%s' % project.peers.all()
                            self._associateProjects(project.parents, pdict['parents'])
                            print 'Updated project parents=%s' % project.parents.all()                    
                            
                            project.save()
                            
                        except Project.DoesNotExist:
                            pass # correct name, wrong site
    
                # remove unused tags
                for tag in ProjectTag.objects.all():
                    if len(tag.projects.all()) == 0:
                        tag.delete()    
        
    def listAllProjects(self):
        '''List all projects.'''
                    
        return Project.objects.filter(active=True).order_by('short_name')
    
    def listAssociatedProjects(self, project, ptype):
        
        if ptype=='parents':
            return project.parents.all()
            
        elif ptype=='peers':
            return project.peers.all()
            
        elif ptype=='child':
            return project.children()
            
        else:
            return []
        
projectManager = ProjectManager()
