from django.contrib.auth.decorators import login_required
from django.http import (
    HttpResponse,
    HttpResponseRedirect,
    HttpResponseForbidden,
    HttpResponseServerError,
)
from django.shortcuts import render
from django.template import RequestContext
import json

import datetime

import os
import re
from cog.views.utils import getQueryDict

from cog.plugins.esgf.security import esgfDatabaseManager

import traceback
import json

# Code used for react components

# Get directories for static files
package_dir = os.path.dirname(os.path.abspath(__file__))
static_dir = os.path.dirname(package_dir)
js_dir = os.path.join(static_dir, "static/cog/cog-react/js/")
css_dir = os.path.join(static_dir, "static/cog/cog-react/css/")

# Get static list
js_files = os.listdir(js_dir)
css_files = os.listdir(css_dir)
js_files = list(map(lambda f: "cog/cog-react/js/" + f, js_files))
css_files = list(map(lambda f: "cog/cog-react/css/" + f, css_files))

# Separate source and map files
map_files = []
js_only = []
for f in js_files:
    if f.endswith(".map"):
        map_files.append(f)
    else:
        js_only.append(f)
css_only = []
for f in css_files:
    if f.endswith(".map"):
        map_files.append(f)
    else:
        css_only.append(f)

# These files are used by Django 'subscribe.html' page, to renders front-end.
react_files = {"css": css_only, "js": js_only, "map": map_files}

# Example data that subscriptions front-end could receive from back-end
test_data = {
    "post_url": "/subscription/",
    "saved_subs": [
        {
            "id": 1,
            "timestamp": 12978234,
            "period": "bi-weekly",
            "activities": ["CMIP", "CORDEX"],
            "variables": ["clt"],
        },
        {
            "id": 2,
            "timestamp": 9768234,
            "name": "Test Loaded",
            "period": "monthly",
            "varliables": ["clt", "ts"],
            "experiments": ["amip-TIP"],
        },
    ],
}

# To pass data to front-end, use react-props and pass it a dictionary with key-value pairs


def lookup_and_render(request):

    try:
        dbres = esgfDatabaseManager.lookupUserSubscriptions(request.user)
    except Exception as e:
        # log error
        error_cond = str(e)
        print(traceback.print_exc())
        return render(
            request,
            "cog/subscription/subscribe_done.html",
            {
                "email": request.user.email,
                "error": "An Error Has Occurred While Processing Your Request. <p> {}".format(
                    error_cond
                ),
            },
        )

    react_props =  {
    "post_url": "/subscription/",
    "saved_subs": dbres
    }
    return react_props


def delete_subscription(request):
    res = request.POST.get("subscription_id", None)
    try:
        if res == "ALL":
            dbres = esgfDatabaseManager.deleteAllUserSubscriptions(request.user)
        else:
            dbres = esgfDatabaseManager.deleteUserSubscriptionById(res)
    except Exception as e:
        # log error
        error_cond = str(e)
        return render(
            request,
            "cog/subscription/subscribe_done.html",
            {
                "error": "An Error Has Occurred While Processing Your Request. <p> {}".format(
                    error_cond
                )
            },
        )

    return render(request, "cog/subscription/subs_delete_done.html")


def temp_print(request, var_name, method="POST"):
    print(request.POST)
    if request.method == "POST":
        data = json.loads(request.body)
    else:
        data = request.GET.copy()

    if data:
        try:
            print("{} {}: {}".format(method, var_name, data[var_name]))
        except KeyError:
            print("Key error: {}".format(data))
    else:
        print("{} {}: None".format(method, var_name))


@login_required
def subscribe(request):

    # Contains the data from the front-end POST requests
    if request.method == "POST":

        # Get data from the POST request received from front-end
        data = json.loads(request.body)
        print(data) # Show data for debugging

        # Example obtaining data
        if data and data['action']:
            if data['action'] == "subscribe":
                print("Subscribing to data.")
                res = -1
                #                try
                res = esgfDatabaseManager.addUserSubscription(
                    request.user, data['payload'])

                print("Result={}".format(str(res)))
                # except Exception as e:
                #     # log error
                #     error_cond = str(e)
                #     return render(
                #         request,
                #         "cog/subscription/subscribe_done.html",
                #         {
                #             "email": request.user.email,
                #             "error": "An Error Has Occurred While Processing Your Request. <p> {}".format(
                #                 error_cond
                #             ),
                #         },
                #     )

            elif data['action'] == "unsubscribe":
                print("Unsubscribing..")
                print(data['payload'])
                res = 0 

        # Example response sent back to front-end
        if res > -1:
            test = {"status": "All good!", "data": data, "id" : res}
        else:
            test = {"status": "Not at all good!", "data": data}
        return HttpResponse(json.dumps(test), content_type="application/json")

    if request.method == "GET":
        react_props = lookup_and_render(request)
        print("1) Props are: " + str(react_props))
        return render(
            request,
            "cog/subscription/subscribe.html",
            {"react_files": react_files, "react_props": react_props},
        )
    else:
        react_props = lookup_and_render(request)
        print("2) Props are: " + str(react_props))
        return render(
            request,
            "cog/subscription/subscribe.html",
            {"react_files": react_files, "react_props": react_props},
        )

