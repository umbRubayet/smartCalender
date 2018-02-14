# api/urls.py

from django.conf.urls import url, include
from rest_framework.urlpatterns import format_suffix_patterns
from api import views
from  django.conf.urls.static import static
from django.conf import settings

urlpatterns = [
    #url(r'fcm/', include('fcm.urls')),
    url(r'^signup/$', views.user_list),
    url(r'^login/$', views.login),
    #url(r'^tasks/$',views.tasks),
    url(r'^monthtasks/(?P<user_id>\d+)/$' , views.get_month_tasks),
    url(r'^detailedTask/(?P<user_id>\d+)/$', views.task),
    url(r'^searchTask/(?P<user_id>\d+)/$', views.search),
    url(r'^taskOnDate/(?P<user_id>\d+)/$', views.getTasksfromDate),
    url(r'^editTask/(?P<task_id>\d+)/$',views.editTask),
    url(r'^profile/(?P<user_id>\d+)/$', views.profile),
    url(r'^findFriend/(?P<user_id>\d+)/$',views.findFriend),
    url(r'^friend/(?P<user_id>\d+)/$',views.friend),
    url(r'^taskStatus/(?P<user_id>\d+)/(?P<task_id>\d+)/$',views.taskStatusOperation),
    url(r'^forgotpassword/$',views.forgotPass),
    url(r'^matchtoken/$',views.matchForgotPass),
    url(r'^syncdata/(?P<user_id>\d+)/$',views.syncTask),
    url(r'^forecast/(?P<city>\w+)/$',views.weatherForecast),
    url(r'^holiday/(?P<country>[\w\s\W]+)/$',views.holiday),
    url(r'^group/(?P<user_id>\d+)/$',views.group),
    url(r'^singlegroup/(?P<user_id>\d+)/(?P<group_id>\d+)/$',views.singleGroup),
    url(r'^tag/(?P<tagged_id>\d+)/$',views.tag),
    url(r'^writenote/(?P<user_id>\d+)/$',views.notePost),
    url(r'^noteoperation/(?P<user_id>\d+)/(?P<note_id>\d+)$',views.noteOperations),
    url(r'^changepassword/(?P<user_id>\d+)/$',views.changePassword),
    url(r'^token/(?P<user_id>\d+)/$',views.tokenOperation),
    url(r'^notification/(?P<user_id>\d+)/$',views.notification),
    #url(r'^fcm/', include('fcm.urls')),
    url(r'^tagaction/(?P<tagged_id>\d+)/(?P<tag_id>\d+)/$',views.tagAction),
    url(r'^groupoffer/(?P<invited_user>\d+)/(?P<group_id>\d+)/$',views.groupInvitation),
    url(r'^logout/(?P<user_id>\d+)/$',views.logout),
] + static(settings.MEDIA_URL, document_root= settings.MEDIA_ROOT)

urlpatterns = format_suffix_patterns(urlpatterns)
