# api/urls.py

from django.conf.urls import url, include
from rest_framework.urlpatterns import format_suffix_patterns
from api import views

urlpatterns = {
    url(r'^signup/$', views.user_list),
    url(r'^login/$', views.login),
    url(r'^month_tasks/$',views.month_tasks),
    url(r'^tasks/$',views.tasks),
    url(r'^monthtasks/(?P<user_id>\d+)/$' , views.get_month_tasks),
}

urlpatterns = format_suffix_patterns(urlpatterns)
