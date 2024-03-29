from django.conf.urls.defaults import patterns, include, url
from django.views.generic.simple import direct_to_template
from django.contrib.staticfiles.urls import staticfiles_urlpatterns
from django.conf.urls.static import static

from django.conf import settings

# Uncomment the next two lines to enable the admin:
# from django.contrib import admin
# admin.autodiscover()

from bookmarks.views import *

urlpatterns = patterns('',
    # Examples:
    # url(r'^$', 'django_bookmarks.views.home', name='home'),
    # url(r'^django_bookmarks/', include('django_bookmarks.foo.urls')),

    # Uncomment the admin/doc line below to enable admin documentation:
    # url(r'^admin/doc/', include('django.contrib.admindocs.urls')),

    # Uncomment the next line to enable the admin:
    # url(r'^admin/', include(admin.site.urls)),
                       (r'^$', main_page),
                       (r'^user/(\w+)/$', user_page),
                       (r'^login/$', 'django.contrib.auth.views.login'),
                       (r'^logout/$', logout_page),
                       (r'^register/$', register_page),
                       (r'^register/success/$', direct_to_template,
                        {'template': 'registration/register_success.html'}),
                       (r'^save/$', bookmark_save_page),
                       (r'^tag/([^\s]+)/$', tag_page),
                       (r'^tag/$', tag_cloud_page),
                       (r'^search/$', search_page),
                       (r'^vote/$', bookmark_vote_page),
                       (r'^popular/$', popular_page),
                       (r'^comments/', include('django.contrib.comments.urls')),
                       (r'^bookmark/(\d+)/$', bookmark_page),
                       (r'^friends/(\w+)/$', friends_page),
                       (r'^friend/add/$', friend_add),
                       (r'^friend/invite/$', friend_invite),
                       (r'^friend/accept/(\w+)/$', friend_accept),
)

urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
urlpatterns += staticfiles_urlpatterns()
