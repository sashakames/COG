
from django.core.urlresolvers import reverse
from django.contrib.auth.decorators import login_required
from django.http import HttpResponse, HttpResponseRedirect, HttpResponseForbidden, HttpResponseServerError
from django.shortcuts import render
from django.template import RequestContext

import datetime

import os
import re
from cog.views.utils import getQueryDict

from cog.plugins.esgf.security import esgfDatabaseManager


def lookup_and_render(request):

	email = request.user.email

	dbres = esgfDatabaseManager.getUserSubscriptions(email)

	render(request, 'cog/subscription/subscribe_list.html', { 'dbres' : str(dbres) } )

@login_required
def subscribe(request):

	if request.method=='GET':

		if request.GET.get('action') == "modify":
			return lookup_and_render(request)
		else:	
			return render(request, 'cog/subscription/subscribe.html')
	else:
	# result.inserted_primary_key

		email = request.user.email

		period = request.POST.get("period", -1)
		if period == -1:
			return render(request, 'cog/subscription/subscribe_done.html', { 'email' : email ,  'error' : "Invalid period" })

		subs_count = 0
		error_cond = ""
		keyarr = []
		valarr = []
		for i in range(1,4):

			keystr = 'subscription_key{}'.format(i)
			keyres = request.POST.get(keystr, '')

			valstr = 'subscription_value{}'.format(i)
			valres = request.POST.get(valstr, '')

#			print "{},{},{},{},{}".format(i,keystr, valstr, keyres, valres)

			if len(keyres) < 2 or len(valres) < 2:
				continue

			keyarr.append(keyres)
			valarr.append(valres)

			subs_count = subs_count + 1

		if subs_count > 0:

			try:
				
				esgfDatabaseManager.addUserSubscription(email, period, keyarr, valarr )

			except Exception as e:
				# log error
				error_cond = str(e)
				return render(request, 'cog/subscription/subscribe_done.html', { 'email' : email ,  'error' : "An Error Has Occurred While Processing Your Request. <p> {}".format(error_cond), })



			return render(request, 'cog/subscription/subscribe_done.html', { 'email' : email , 'count' : subs_count })
		else:
			return render(request, 'cog/subscription/subscribe.html')			
	
