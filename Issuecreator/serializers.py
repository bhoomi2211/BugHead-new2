from rest_framework import serializers
from .models import Issue, Website

class WebsiteSerializer(serializers.ModelSerializer):
    class Meta:
        model = Website
        fields = ['id', 'owner', 'websitelink', 'gitHubRepo', 'site_key', 'create_at', 'update_at']
        read_only_fields = ['site_key', 'create_at', 'update_at']

class IssueSerializer(serializers.ModelSerializer):
    class Meta:
        model = Issue
        fields = ['bugArea', 'priority', 'IssueDetail', 'Device', 'Browse', 'OperatingSystem', 'website']