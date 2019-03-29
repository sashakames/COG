
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

from cog.plugins.esgf.security import esgfDatabaseManager

@login_required
def subscribe(request):

	if request.method=='GET':

		return render(request, 'cog/subscription/subscribe.html')
	else:
		email = request.user.email

		subs_count = 0

		error_cond = ""
		for i in range(1,4):

			keystr = 'subscription_key{}'.format(i)
			keyres = request.POST.get(keystr, '')

			valstr = 'subscription_value{}'.format(i)
			valres = request.POST.get(valstr, '')

#			print "{},{},{},{},{}".format(i,keystr, valstr, keyres, valres)

			if len(keyres) < 2 or len(valres) < 2:
				continue

			try:
				esgfDatabaseManager.addUserSubscription(email, keyres, valres )
			except Exception as e:
				# log error
				error_cond = str(e)
				return render(request, 'cog/subscription/subscribe_done.html', { 'email' : email ,  'error' : "An Error Has Occurred While Processing Your Request. <p> {}".format(error_cond), })

			subs_count = subs_count + 1

		if subs_count > 0:
			return render(request, 'cog/subscription/subscribe_done.html', { 'email' : email , 'count' : subs_count })
		else:
			return render(request, 'cog/subscription/subscribe.html')			
	
