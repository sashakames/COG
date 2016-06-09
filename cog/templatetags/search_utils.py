from django import template
from cog.models.search import searchMappings
from cog.site_manager import siteManager
from string import replace
import json
if siteManager.isGlobusEnabled():    
    from cog.views.views_globus import GLOBUS_ENDPOINTS

register = template.Library()

# filter to access a dictionary value by key
@register.filter
def hash(h, key):
    return h.get(key,'')
    
# filter that returns the selection state of a given facet key
@register.filter
def getSelectedState(constraints, key):
    if constraints.get(key, None):
        return 'selected'
    else:
        return ''
        
# returns the list of constraints for a given facet key,
# or the empty array
@register.filter
def getConstraints(constraints, key):
    # example: Constraint key=realm value(s)=[u'atmos,ocean']
    try:
        values = str(constraints[key][0])
        return values.split(',')
    except KeyError:
        return []

@register.filter
def getFacetOptionLabel(facet_key, facet_value):
    """Return the label to be displayed for a given (facet key, facet value) combination, 
       or the facet_value itself if a mapping is not found."""
    label = searchMappings.getFacetOptionLabel(facet_key, facet_value)
    return label.replace("_"," ")

@register.filter 
def displayMetadataKey(key):
    """ Utility function to determine when a metadata field needs to be displayed """
    #return (key != 'score' and key != 'index_node' and key != 'data_node' \
    #        and key != 'dataset_id' and key != 'replica' and key!= 'latest')
    return (key != 'score' and key != 'description' and key != 'title' \
            and key != 'version' and key != '_version_' \
            and key != 'url' and key != 'type' and key!= 'replica' and key != 'latest')

 
@register.filter    
def formatMetadataKey(key):
    '''Utility method to format a metadata key before display.'''
    key = key.capitalize()
    return replace(key,'_',' ').title()

@register.filter 
def toJson(record):
    '''Serializes the record metadata fields to JSON format.'''
    
    jsondoc = json.dumps(record.fields)
    return jsondoc

# function to custom order the URLs
def url_order(mtype):
    if mtype=='application/html+thredds':
        return 1
    elif mtype=='application/wget':
        return 2
    elif mtype=='application/las':
        return 3
    else:
        return 4
    
@register.filter
def recordUrls(record):
    '''
    Returns an ordered list of URL endpoints for this record.
    Note: the URL parts must match the values used by _services_js.html.
    '''
    
    urls = []
    
    #record.printme()
        
    # add all existing URL endpoints (THREDDS, LAS etc...)
    if 'url' in record.fields:
        for value in record.fields['url']:
            urls.append(value)
        
    # add special WGET endpoint
    urls.append( ("javascript:wgetScript('%s','%s','%s')" % (record.fields['index_node'][0], record.fields.get('shard', [''])[0], record.id) , 
                  "application/wget", 
                  "WGET Script") )
    
    # add GridFTP endpoint
    if siteManager.isGlobusEnabled():  # only if this node has been registered with Globus
        if 'access' in record.fields and 'index_node' in record.fields and 'data_node' in record.fields:
            index_node = record.fields['index_node'][0]
            data_node = record.fields['data_node'][0]
            for value in record.fields['access']:
                if value.lower() == 'gridftp':
                    # data_node must appear in list of valid Globus endpoints (example: "esg-datanode.jpl.nasa.gov:2811")
                    for gridftp_url in GLOBUS_ENDPOINTS.endpointDict().keys():
                    	gurl = '/globus/download?dataset=%s@%s' %(record.id, index_node)
                    	if record.fields.get('shard', None):
                    		gurl += "&shard="+record.fields.get('shard')[0]
                        if data_node in gridftp_url:
                            urls.append( (gurl,
                                          'application/gridftp', # must match: var GRIDFTP = 'application/gridftp'
                                          'GridFTP') )
            
    return sorted(urls, key = lambda url: url_order(url[1]))

@register.filter
def showSearchConfigMessage(message, project):
    
    if message == "search_config_exported":
        return "The project search configuration has been exported to: " + _getProjectSearchConfigFilePath(project)
    
    elif message == "search_config_imported":
        return "The project search configuration has been imported from: " + _getProjectSearchConfigFilePath(project)
    
    elif message == "search_config_not_found":
        return "The project search configuration could not be imported from: " + _getProjectSearchConfigFilePath(project)

    else:
        raise Exception("Invalid Message")

def _getProjectSearchConfigFilePath(project):
    
    return "$MEDIA_ROOT/config/%s/search.cfg" % project.short_name.lower()