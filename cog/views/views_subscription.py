
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

import traceback
import json

# Code used for react components

# Get static js files list
js_files = os.listdir(
    "/Users/downie4/Desktop/COG_devel/COG/cog/static/cog/cog-react/js")
css_files = os.listdir(
    "/Users/downie4/Desktop/COG_devel/COG/cog/static/cog/cog-react/css")
js_files = list(map(lambda f: "cog/cog-react/js/" + f, js_files))
css_files = list(map(lambda f: "cog/cog-react/css/" + f, css_files))

react_files = {
    'css': css_files,
    'js': js_files
}

# Example data that subscriptions front-end could use
test_data = {
    "user_info": {"first":"John","last":"Doe","hobbies":"Programming.","send_emails_to":"This place."},
    "activities": {"method":["email"],"weekly":["CMIP"],"monthly":["CMIP6"]},
    "experiments": {"method":["popup"],"daily":["test", "experiment 2"],"weekly":["test2"]},
}

test_results = {
 "results" : [ {"subs_id" : 1 , "activity_id" : ["CMIP", "ScenarioMIP"],  "experiment_id" : ["historical", "ssp226"],
  "period" : "daily", "timestamp" : "2020-06-08T09:49:25Z"},  
 {"subs_id" : 2 , "variable_id" : ["tas", "pr"],  "experiment_id" : ["piControl"] , 
 "period" : "daily", "name" : "temp-precip", "timestamp" : "2020-06-08T10:00:13Z" } ]
  
}


# To pass data to front-end, use react-props and pass it a dictionary with key-value pairs
react_props = test_data

def lookup_and_render(request):

    try:
        dbres = esgfDatabaseManager.lookupUserSubscriptions(request.user)
    except Exception as e:
        # log error
        error_cond = str(e)
        print(traceback.print_exc())
        return render(request, 'cog/subscription/subscribe_done.html', {'email': email,  'error': "An Error Has Occurred While Processing Your Request. <p> {}".format(error_cond)})

    return render(request, 'cog/subscription/subscribe_list.html', {'dbres': dbres})


def delete_subscription(request):
    res = request.POST.get('subscription_id', None)
    try:
        if res == "ALL":
            dbres = esgfDatabaseManager.deleteAllUserSubscriptions(
                request.user)
        else:
            dbres = esgfDatabaseManager.deleteUserSubscriptionById(res)
    except Exception as e:
        # log error
        error_cond = str(e)
        return render(request, 'cog/subscription/subscribe_done.html', {'error': "An Error Has Occurred While Processing Your Request. <p> {}".format(error_cond)})

    return render(request, 'cog/subscription/subs_delete_done.html')


@login_required
def subscribe(request):

    if request.method == 'GET':

        if request.GET.get('action') == "modify":
            return lookup_and_render(request)
        else:
            return render(request, 'cog/subscription/subscribe.html', {'react_files': react_files, 'react_props': react_props})
    elif request.POST.get('action') == "delete":
        return delete_subscription(request)
    else:

        period = request.POST.get("period", -1)
        if period == -1:
            return render(request, 'cog/subscription/subscribe_done.html', {'email': email,  'error': "Invalid period"})

        subs_count = 0
        error_cond = ""
        keyarr = []
        valarr = []
        for i in range(1, 4):

            keystr = 'subscription_key{}'.format(i)
            keyres = request.POST.get(keystr, '')

            valstr = 'subscription_value{}'.format(i)
            valres = request.POST.get(valstr, '')

            if len(keyres) < 2 or len(valres) < 2:
                continue

            keyarr.append(keyres)
            valarr.append(valres)

            subs_count = subs_count + 1

        if subs_count > 0:

            try:

                esgfDatabaseManager.addUserSubscription(
                    request.user, period, keyarr, valarr)

            except Exception as e:
                # log error
                error_cond = str(e)
                return render(request, 'cog/subscription/subscribe_done.html', {'email': request.user.email,  'error': "An Error Has Occurred While Processing Your Request. <p> {}".format(error_cond), })

            return render(request, 'cog/subscription/subscribe_done.html', {'email': request.user.email, 'count': subs_count})
        else:
            return render(request, 'cog/subscription/subscribe.html', {'react_files': react_files, 'react_props': react_props})
