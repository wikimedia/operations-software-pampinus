"""zarcillo URL Configuration

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/3.2/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path
from django.views.generic.base import RedirectView

from instances import views as instances_views
from dbbackups import views as dbbackups_views

urlpatterns = [
    path('', RedirectView.as_view(url='/dbbackups/')),
    path('admin/', admin.site.urls),
    path('instances/', instances_views.instance_list, name='instance_list'),
    path('instances/<str:pk>/', instances_views.instance_show, name='instance_show'),
    path('servers/', instances_views.server_list, name='server_list'),
    path('servers/<str:hostname>/', instances_views.server_show, name='server_show'),
    path('dbbackups/', dbbackups_views.backup_status, name='backup_status'),
    path('dbbackups/jobs/', dbbackups_views.backup_list, name='backup_list'),
    path('dbbackups/jobs/<int:pk>/', dbbackups_views.backup_show, name='backup_show'),
    path('dbbackups/<str:dc>/<str:section>/<str:backup_type>/',
         dbbackups_views.backup_status_section, name='backup_status_section'),

]
