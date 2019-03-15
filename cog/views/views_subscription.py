
from django.core.urlresolvers import reverse
from django.contrib.auth.decorators import login_required
from django.http import HttpResponse, HttpResponseRedirect, HttpResponseForbidden, HttpResponseServerError
from django.shortcuts import render
from django.template import RequestContext
import urllib
from cog.utils import getJson
from urlparse import urlparse
from cog.constants import SECTION_GLOBUS
from cog.site_manager import siteManager
import datetime

from functools import wraps
import os
import re
from cog.views.utils import getQueryDict


@login_required
def subscribe(request):

	if request.method=='GET':

		return render(request, 'cog/subscribe/subscribe.html')
	else:
		email = request.user.email

		
	