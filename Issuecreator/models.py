from django.db import models

# Create your models here.
  
class Website(models.Model):
    owner= models.CharField(max_length = 150)
    websitelink= models.CharField(max_length=20)
    gitHubRepo= models.CharField(max_length=50)
    create_at= models.DateTimeField(auto_now=True)
    update_at=models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.owner