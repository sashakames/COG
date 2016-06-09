"""
Module containing common views.

@author: cinquini
"""

from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404
from django_comments.models import Comment
from django.http import HttpResponseRedirect, HttpResponseForbidden
from constants import PERMISSION_DENIED_MESSAGE
from cog.models.project import userHasAdminPermission
from cog.views.utils import getQueryDict

@login_required
def deleteComment(request, id):
    
    comment = get_object_or_404(Comment, id=id)
    queryDict = getQueryDict(request)
    redirect_url = queryDict['next']
    
    # comments can only be deleted by the original authors, or project administrators
    project = comment.content_object.getProject()
    if comment.user != request.user and not userHasAdminPermission(request.user, project):
        return HttpResponseForbidden(PERMISSION_DENIED_MESSAGE)
    
    # delete comment
    comment.delete()

    # redirect to original page    
    return HttpResponseRedirect(redirect_url)