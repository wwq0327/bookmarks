#!/usr/bin/env python
# -*- coding: utf-8 -*-

from datetime import datetime, timedelta

from django.http import HttpResponse, Http404, HttpResponseRedirect
from django.template import Context, RequestContext
from django.template.loader import get_template
from django.contrib.auth.models import User
from django.shortcuts import render_to_response, get_object_or_404
from django.contrib.auth import logout
from django.contrib.auth.decorators import login_required
from django.core.exceptions import ObjectDoesNotExist

from bookmarks.models import *

from bookmarks.forms import RegistrationForm, BookmarkSaveForm, SearchForm

def main_page(request):
    shared_bookmarks = SharedBookmark.objects.order_by('-date')[:10]
    variables = RequestContext(request, {
        'shared_bookmarks': shared_bookmarks,
        'user': request.user
        })


    return render_to_response('main_page.html', variables)

def user_page(request, username):
    user = get_object_or_404(User, username=username)

    bookmarks = user.bookmarks_set.order_by('-id')

    return render_to_response('user_page.html',
                              {'bookmarks': bookmarks,
                               'user':request.user,
                               'username':username,
                               'show_tags': True,
                               'show_edit': username == request.user.username
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

def _bookmark_save(request, form):
    # Create or get link
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
    # Share on the main page if requested.
    if form.cleaned_data['share']:
        shared_bookmark, created = SharedBookmark.objects.get_or_create(
            bookmark=bookmark)
        if created:
            shared_bookmark.users_voted.add(request.user)
            shared_bookmark.save()

    bookmark.save()

    return bookmark

@login_required
def bookmark_save_page(request):
    ajax = request.GET.has_key('ajax')
    if request.method == 'POST':
        form = BookmarkSaveForm(request.POST)
        if form.is_valid():
            bookmark = _bookmark_save(request, form)
            if ajax:
                variables = RequestContext(request, {
                    'bookmarks': [bookmark],
                    'show_edit': True,
                    'show_tags': True
                    })
                return render_ro_response('bookmark_list.html', variables)
            else:
                return HttpResponseRedirect('/user/%s/' % request.user.username)
        else:
            if ajax:
                return HttpResponse('failure')
    elif request.GET.has_key('url'):
        url = request.GET['url']
        title = ''
        tags = ''
        try:
            link = Link.objects.get(url=url)
            bookmark = Bookmarks.objects.get(
                link = link,
                user = request.user
                )
            title = bookmark.title
            tags = ' '.join(
                tag.name for tag in bookmark.tag_set.all()
                )
        except ObjectDoesNotExist:
            pass
        form = BookmarkSaveForm({
            'url': url,
            'title': title,
            'tags': tags
            })
    else:
        form = BookmarkSaveForm()

    variables = RequestContext(request, {
        'form': form
        })

    if ajax:
        return render_to_response('bookmark_save_form.html', variables)
    else:
        return render_to_response('bookmark_save.html', variables )

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

def search_page(request):
    form = SearchForm()
    bookmarks = []
    show_results = False
    if request.GET.has_key('query'):  ## request.GET获取query的值
        show_results = True
        query = request.GET['query'].strip()
        if query:
            form = SearchForm({'query': query})
            bookmarks = Bookmarks.objects.filter(title__icontains=query)[:10]

    variables = RequestContext(request, {
        'bookmarks': bookmarks,
        'show_results': show_results,
        'show_tags': True,
        'show_user': True,
        'user': request.user,
        'form': form
        })

    if request.GET.has_key('ajax'):
        return render_to_response('bookmark_list.html', variables)
    else:
        return render_to_response('search.html', variables)

@login_required
def bookmark_vote_page(request):
    if request.GET.has_key('id'):
        try:
            id = request.GET['id']
            shared_bookmark = SharedBookmark.objects.get(id=id)
            user_voted = shared_bookmark.users_voted.filter(
                username=request.user.username)
            if not user_voted:
                shared_bookmark.votes += 1
                shared_bookmark.users_voted.add(request.user)
                shared_bookmark.save()
        except ObjectDoesNotExist:
            raise Http404('Bookmark not found.')
    if request.META.has_key('HTTP_REFERER'):
        return HttpResponseRedirect(request.META['HTTP_REFERER'])

    return HttpResponseRedirect('/')
def popular_page(request):
    '''一天当中最受欢迎的链接'''

    today = datetime.today()
    yesterday = today - timedelta(1)
    shared_bookmarks = SharedBookmark.objects.filter(date__gt=yesterday)
    shared_bookmarks = shared_bookmarks.order_by('-votes')[:10]
    variables = RequestContext(request, {'shared_bookmarks': shared_bookmarks})
    return render_to_response('popular_page.html', variables)

def bookmark_page(request, bookmark_id):
    shared_bookmark = get_object_or_404(SharedBookmark, id=bookmark_id)
    variables = RequestContext(request, {
        'shared_bookmark': shared_bookmark})
    return render_to_response('bookmark_page.html', variables)
