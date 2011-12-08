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
from django.core.paginator import Paginator

from bookmarks.models import *

from bookmarks.forms import RegistrationForm, BookmarkSaveForm, SearchForm, FriendInviteForm

#PAGES
from settings import ITEMS_PER_PAGE

def main_page(request):
    shared_bookmarks = SharedBookmark.objects.order_by('-date')[:10]
    variables = RequestContext(request, {
        'shared_bookmarks': shared_bookmarks,
        'user': request.user
        })


    return render_to_response('main_page.html', variables)

def user_page(request, username):
    """分页技术"""

    user = get_object_or_404(User, username=username)
    query_set = user.bookmarks_set.order_by('-id')
    paginator = Paginator(query_set, ITEMS_PER_PAGE)
    is_friend = Friendship.objects.filter(from_friend=request.user, to_friend=user)
    try:
        page = int(request.GET['page'])
    except:
        page = 1

    try:
        bookmarks = paginator.page(page) ## 获取当前页
    except:
        raise Http404


    ## bookmarks = user.bookmarks_set.order_by('-id')

    return render_to_response('user_page.html',
                              {'bookmarks': bookmarks.object_list, ## 数据列表
                               'user':request.user,
                               'username':username,
                               'show_tags': True,
                               'show_edit': username == request.user.username,
                               'show_paginator': paginator.num_pages > 1, ## 判断总页数
                               'has_prev': bookmarks.has_previous(), ## 是否存在上一页
                               'has_next': bookmarks.has_next(),  ## 是否还有下一页
                               'page': page,
                               'pages': paginator.num_pages,  ## 总页数
                               'next_page': page + 1,
                               'prev_page': page - 1,
                               'is_friend': is_friend
                               })

@login_required
def logout_page(request):
    """退出登录"""

    logout(request)
    return HttpResponseRedirect('/')

def register_page(request):
    """用户注册"""

    if request.method == 'POST':
        form = RegistrationForm(request.POST)
        if form.is_valid():
            user = User.objects.create_user(
                username = form.cleaned_data['username'],
                password = form.cleaned_data['password1'],
                email = form.cleaned_data['email']
                )
            ## 来自于邀请的注册
            if 'invitation' in request.session:
                invitation = Invitation.objects.get(id=request.session['invistation'])
                #建立好友关系
                friendship = Friendship(from_friend=user, to_friend=invitation.sender)
                friendship.save()

                ## 双向
                friendship = Friendship(from_friend=invitation.sender, to_friend=user)
                friendship.save()

                invitation.delete()
                del request.session['invitation']

            return HttpResponseRedirect('/register/success/')

    else:
        form = RegistrationForm()

    return render_to_response('registration/register.html',
                              {'form': form}
                              )

def _bookmark_save(request, form):
    # Create or get link
    # 如果数据存在，则获得数据，此时返回False状态，
    # 否则，得到新建的数据，并返回True状态
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

def friends_page(request, username):
    """好友列表及相关收藏"""

    user = get_object_or_404(User, username=username)
    friends = [friendship.to_friend for friendship in user.friend_set.all()]
    friend_bookmarks = Bookmarks.objects.filter(user__in=friends).order_by('-id')
    variables = RequestContext(request, {
        'username': username,
        'friends': friends,
        'bookmarks': friend_bookmarks[:10],
        'show_tags': True,
        'show_user': True,
        })
    return render_to_response('friends_page.html', variables)

@login_required
def friend_add(request):
    """添加好友"""

    if request.GET.has_key('username'):
        friend = get_object_or_404(User, username=request.GET['username'])
        friendship = Friendship(from_friend=request.user, to_friend=friend)

        try:
            friendship.save()
            request.user.message_set.create(
                message='%s was added to your friend list.' % friend.username
                )
        except:
            request.user.message_set.create(
                message='%s already a friend of yours.' % friend.username
                )
        return HttpResponseRedirect('/friends/%s' % request.user.username)
    else:
        raise Http404

@login_required
def friend_invite(request):
    """好友邀请功能"""

    if request.method == 'POST':
        form = FriendInviteForm(request.POST)
        if form.is_valid():
            invitation = Invitation(
                name = form.cleaned_data['name'],
                email = form.cleaned_data['email'],
                code = User.objects.make_random_password(20),
                sender = request.user
                )
            invitation.save()
            try:
                invitation.send()
                request.user.message_set.create(
                    message='An invitation was sent to %s' % invitation.email
                    )
            except:
                retuqest.user.message_create(
                    message='There was an error while sending the invitation.'
                    )
    else:
        form = FriendInviteForm()

    variables = RequestContext(request, {'form': form})

    return render_to_response('friend_invite.html', variables)

def friend_accept(request, code):
    invitation = get_object_or_404(Invitation, code__exact=code)
    request.session['invitation'] = invitation.id
    return HttpResponseRedirect('/register/')
