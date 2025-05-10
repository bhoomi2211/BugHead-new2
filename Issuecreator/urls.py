"""
URL configuration for config project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.1/topics/http/urls/
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
from django.views.generic import TemplateView
from . import views


urlpatterns = [
    # path("admin/", admin.site.urls)
    path('api/issues/', views.create_issue, name='create_issue'),
    path('api/websites/', views.website_list, name='website_list'),
    path('widget/<uuid:site_key>.js', views.get_widget_script, name='widget_script'),
    
    # Dashboard URLs
    path('dashboard/', views.dashboard, name='dashboard'),
    path('website/<uuid:site_key>/', views.website_detail, name='website_detail'),
    path('website/add/', views.add_website, name='add_website'),
    path('website/<uuid:site_key>/delete/', views.delete_website, name='delete_website'),
]
