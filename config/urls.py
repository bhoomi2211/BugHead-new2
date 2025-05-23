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
from django.urls import path, include
from django.views.generic import TemplateView


urlpatterns = [
    path("admin/", admin.site.urls),
    path("", TemplateView.as_view(template_name="index.html"),name="home"),
    path("Home/",TemplateView.as_view(template_name="home.html"),name="Home"),
    path("register/" , TemplateView.as_view(template_name="register.html"), name= "register") ,
    path("issueForm/" , TemplateView.as_view(template_name="issueForm.html"), name= "issueForm") ,
    path("devloperdashboard/" , TemplateView.as_view(template_name="devloperdashboard.html"), name= "devloperdashboard"),
    path("report-bug/" , TemplateView.as_view(template_name="report-bug.html"), name= "report-bug"),
    path("Bug-Traker/" , TemplateView.as_view(template_name="Bug-tracker.html"), name= "Bug-Tracker"),
    path("add-website/" , TemplateView.as_view(template_name="add-website.html"), name= "add-website"),
    path("", include("authentication.urls")),
    path("", include("Issuecreator.urls") ),
     path("footer/",TemplateView.as_view(template_name="footer.html"),name="footer"),
     path("signup/",TemplateView.as_view(template_name="signup.html"),name="signup"),
]
