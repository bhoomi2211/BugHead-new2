from django.contrib import admin

# Register your models here.

from.models import Website
from.models import Issue

admin.site.register(Website)
admin.site.register(Issue)