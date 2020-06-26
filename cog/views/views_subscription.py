from django.contrib.auth.decorators import login_required
from django.http import HttpResponse, HttpResponseRedirect, HttpResponseForbidden, HttpResponseServerError
from django.shortcuts import render
from django.template import RequestContext

import datetime

import os
import re
from cog.views.utils import getQueryDict

from cog.plugins.esgf.security import esgfDatabaseManager

import traceback

def lookup_and_render(request):

	try:
		dbres = esgfDatabaseManager.lookupUserSubscriptions(request.user)
	except Exception as e:
		# log error
		error_cond = str(e)
		print(traceback.print_exc())
		return render(request, 'cog/subscription/subscribe_done.html', {  'error' : "An Error Has Occurred While Processing Your Request. <p> {}".format(error_cond) })
	
	return render(request, 'cog/subscription/subscribe_list.html', { 'dbres' : str(dbres) } )

def delete_subscription(request):

	res = request.POST.get('subscription_id', None)
	try:
		if res == "ALL":
			dbres = esgfDatabaseManager.deleteAllUserSubscriptions(request.user)
		else:
			dbres = esgfDatabaseManager.deleteUserSubscriptionById(res)
	except Exception as e:
		# log error
		error_cond = str(e)
		return render(request, 'cog/subscription/subscribe_done.html', { 'error' : "An Error Has Occurred While Processing Your Request. <p> {}".format(error_cond) })

	return render(request, 'cog/subscription/subs_delete_done.html')


@login_required
def subscribe(request):

	if request.method=='GET':

		if request.GET.get('action') == "modify":
			return lookup_and_render(request)
		else:	
			return render(request, 'cog/subscription/subscribe.html')
	elif request.POST.get('action') == "delete":
		return delete_subscription(request)
	else:
	# result.inserted_primary_key

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
				
				esgfDatabaseManager.addUserSubscription(request.user, period, keyarr, valarr )

			except Exception as e:
				# log error
				error_cond = str(e)
				return render(request, 'cog/subscription/subscribe_done.html', { 'email' : request.user.email ,  'error' : "An Error Has Occurred While Processing Your Request. <p> {}".format(error_cond), })



			return render(request, 'cog/subscription/subscribe_done.html', { 'email' : request.user.email , 'count' : subs_count })
		else:
			return render(request, 'cog/subscription/subscribe.html')			
	
