from cog.forms import *
from cog.models import *
from django.contrib.auth.decorators import login_required, user_passes_test
from django.core.urlresolvers import reverse
from django.http import HttpResponseRedirect
from django.shortcuts import get_object_or_404, render_to_response
from django.template import RequestContext
import ast
from django.contrib.sites.models import Site  
from cog.models import PeerSite
from django.forms.models import modelformset_factory
from cog.views.utils import getUsersThatMatch, get_projects_by_name, paginate


def site_home(request):
    
    # redirect to HOME_PROJECT home
    return HttpResponseRedirect(reverse('project_home', args=[settings.HOME_PROJECT]))
        
    # redirect to 'cog' project hone page
    #return HttpResponseRedirect()
            
    # redirect to independent splash page
    #return render_to_response('cog/index.html', 
    #                          {'title':'Welcome to COG' }, 
    #                          context_instance=RequestContext(request))


# admin page for managing projects
@user_passes_test(lambda u: u.is_staff)
def admin_projects(request):
    """
    Lists local projects in a table with links to edit or delete
    """
    site = Site.objects.get_current()

    # optional active=True|False filter
    active = request.GET.get('active', None)
    if active != None:
        project_list = Project.objects.filter(site=Site.objects.get_current()).filter(active=ast.literal_eval(active))\
            .order_by('short_name')
    else:
        if request.method == 'GET':
            project_list = Project.objects.filter(site=Site.objects.get_current()).order_by('short_name')
        else:
            # list project by search criteria. Search function located in utils.py
            # get list of all projects
            project_list = get_projects_by_name(request.POST['match'])
            # filter projects to include local site only
            project_list = project_list.filter(site=Site.objects.get_current()).order_by('short_name')

    # retrieve top-level projects, ordered alphabetically by short name. Only list those on the current site.
    return render_to_response('cog/admin/admin_projects.html',
                              {'project_list': paginate(project_list, request),
                               'title': '%s Projects Administration' % site.name,
                               }, context_instance=RequestContext(request))


# admin page for listing all system users
@user_passes_test(lambda u: u.is_staff)
def admin_users(request):

    # get sort command if it exists
    sortby = request.GET.get('sortby', 'title')

    # load all users
    if request.method == 'GET':

        # display and sort based on lower case last name

        # TODO: This works locally but causes a YSD on cu-dev when passed to the order by
        # users = User.objects.all().extra(select={'last_name': 'lower(last_name)'})
        # users = users.extra(select={'first_name': 'lower(first_name)'})

        if sortby == 'last_login':
            results = User.objects.all().order_by('last_login')
        elif sortby == 'last_name':
            results = User.objects.all().order_by('last_name')
        elif sortby == 'email':
            results = User.objects.all().order_by('email')
        else:
            results = User.objects.all().order_by('last_name')  # default

    else:  # lookup specific user
        results = getUsersThatMatch(request.POST['match'])

    title = 'List Node Users'
    return render_to_response('cog/admin/admin_users.html',
                              {'users': paginate(results, request, max_counts_per_page=50), 'title': title},
                              context_instance=RequestContext(request))

    
# admin page for managing peers
@user_passes_test(lambda u: u.is_staff)
def admin_peers(request):
    
    PeerSiteFormSet = modelformset_factory(PeerSite, extra=0, can_delete=False, fields="__all__")
    
    if request.method == 'GET':
        
        formset = PeerSiteFormSet(queryset=PeerSite.objects.exclude(site=Site.objects.get_current()))
        return render_to_response('cog/admin/admin_peers.html', {'formset': formset},
                                  context_instance=RequestContext(request))
        
    else:
        
        formset = PeerSiteFormSet(request.POST)
        
        if formset.is_valid():
            instances = formset.save()
            return HttpResponseRedirect(reverse('admin_peers')+"?status=success")
        
        else:
            print formset.errors
            return render_to_response('cog/admin/admin_peers.html', {'formset': formset},
                                      context_instance=RequestContext(request))