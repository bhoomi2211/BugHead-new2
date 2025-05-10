from django.db import models
from django.contrib.auth.models import User
import uuid

class Website(models.Model):
    owner = models.CharField(max_length=150)
    websitelink = models.CharField(max_length=50)
    gitHubRepo = models.CharField(max_length=100)
    site_key = models.UUIDField(default=uuid.uuid4, editable=False, unique=True)
    create_at = models.DateTimeField(auto_now=True)
    update_at = models.DateTimeField(auto_now_add=True)
    user = models.ForeignKey(User, on_delete=models.CASCADE, null=True, blank=True, related_name='websites')

    def __str__(self):
        return self.owner
    
class Issue(models.Model):
    bugArea = models.CharField(max_length=200)   
    priority = models.CharField(max_length=50)  
    IssueDetail = models.TextField()
    Device = models.CharField(max_length=50)
    Browse = models.CharField(max_length=50)
    OperatingSystem = models.CharField(max_length=50)
    website = models.ForeignKey('Website', on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.bugArea}: {self.IssueDetail[:50]}"


