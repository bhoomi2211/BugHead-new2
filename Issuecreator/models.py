from django.db import models

# Create your models here.
  
class Issue(models.Model):
    owner= models.CharField(max_length = 150)
    websitelink= models.CharField(max_length=20)
    gitHubRepo= models.TextField()
    create_at= models.DateTimeField(auto_now=True)
    update_at=models.DateTimeField(auto_now_add= True)
    feedback= models.TextField()
    

    def __str__(self):
        return self.name
        