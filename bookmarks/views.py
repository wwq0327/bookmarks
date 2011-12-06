#!/usr/bin/env python
# -*- conding: utf-8 -*-

from django.http import HttpResponse, Http404, HttpResponseRedirect
from django.template import Context
from django.template.loader import get_template
from django.contrib.auth.models import User
from django.shortcuts import render_to_response, get_object_or_404
from django.contrib.auth import logout
from django.contrib.auth.decorators import login_required

from bookmarks.models import *

from bookmarks.forms import RegistrationForm, BookmarkSaveForm

def main_page(request):

    return render_to_response('main_page.html', {'user': request.user})

def user_page(request, username):
    user = get_object_or_404(User, username=username)

    bookmarks = user.bookmarks_set.order_by('-id')

    return render_to_response('user_page.html',
                              {'bookmarks': bookmarks,
                               'user':request.user,
                               'show_tags': True
                               })
@login_required
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
@login_required
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

    return render_to_response('bookmark_save.html', {'form': form,
                                                     'user': request.user})
def tag_page(request, tag_name):
    tag = get_object_or_404(Tag, name=tag_name)
    bookmarks = tag.bookmarks.order_by('-id')

    return render_to_response('tag_page.html',
                              {
                                  'bookmarks': bookmarks,
                                  'tag_name': tag_name,
                                  'show_tags': True,
                                  'show_tags': True,
                                  'user': request.user
                                  })

def tag_cloud_page(request):
    MAX_WEIGHT = 5
    tags = Tag.objects.order_by('name')
    min_count = max_count = tags[0].bookmarks.count()
    for tag in tags:
        tag.count = tag.bookmarks.count()
        if tag.count < min_count:
            min_count = tag.count
        if max_count < tag.count:
            max_count = tag.count

    range = float(max_count - min_count)
    if range == 0.0:
        range = 1.0
    for tag in tags:
        tag.weight = int(
            MAX_WEIGHT * (tag.count - min_count) /range
            )
    return render_to_response('tag_cloud_page.html',
                              {
                                  'user': request.user,
                                  'tags': tags
                                  })
