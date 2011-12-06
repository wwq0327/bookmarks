#!/usr/bin/env python
# -*- conding: utf-8 -*-

from django.http import HttpResponse, Http404, HttpResponseRedirect
from django.template import Context
from django.template.loader import get_template
from django.contrib.auth.models import User
from django.shortcuts import render_to_response
from django.contrib.auth import logout

from bookmarks.models import *

from bookmarks.forms import RegistrationForm, BookmarkSaveForm

def main_page(request):

    return render_to_response('main_page.html', {'user': request.user})

def user_page(request, username):
    try:
        user = User.objects.get(username=username)
    except:
        raise Http404('Requested user not found.')

    bookmarks = user.bookmarks_set.all()

    return render_to_response('user_page.html',
                              {'username': username,
                               'bookmarks': bookmarks
                               })
def logout_page(request):
    logout(request)
    return HttpResponseRedirect('/')

def register_page(request):
    if request.method == 'POST':
        form = RegistrationForm(request.POST)
        if form.is_valid():
            user = User.objects.create_user(
                username = form.cleaned_data['username'],
                password = form.cleaned_data['password1'],
                email = form.cleaned_data['email']
                )
            return HttpResponseRedirect('/register/success/')
    else:
        form = RegistrationForm()

    return render_to_response('registration/register.html',
                              {'form': form}
                              )

def bookmark_save_page(request):
    if request.method == 'POST':
        form = BookmarkSaveForm(request.POST)
        if form.is_valid():
            link, dummy = Link.objects.get_or_create(
                url=form.cleaned_data['url']
                )
            bookmark, created = Bookmarks.objects.get_or_create(
                user=request.user,
                link=link
                )
            bookmark.title = form.cleaned_data['title']
            if not created:
                bookmark.tag_set.clear()
            tag_names = form.cleaned_data['tags'].split()
            for tag_name in tag_names:
                tag, dummy = Tag.objects.get_or_create(name=tag_name)
                bookmark.tag_set.add(tag)
            bookmark.save()
            return HttpResponseRedirect('/user/%s/' % request.user.username)
    else:
        form = BookmarkSaveForm()

    return render_to_response('bookmark_save.html', {'form': form})

