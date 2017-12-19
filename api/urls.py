# api/urls.py

from django.conf.urls import url, include
from rest_framework.urlpatterns import format_suffix_patterns
from api import views
from  django.conf.urls.static import static
from django.conf import settings
urlpatterns = [
    url(r'^signup/$', views.user_list),
    url(r'^login/$', views.login),
    url(r'^month_tasks/$',views.month_tasks),
    url(r'^tasks/$',views.tasks),
    url(r'^monthtasks/$' , views.postTask),
    url(r'^detailedTask/(?P<user_id>\d+)/$', views.postTask),
] + static(settings.MEDIA_URL, document_root= settings.MEDIA_ROOT)

urlpatterns = format_suffix_patterns(urlpatterns)
