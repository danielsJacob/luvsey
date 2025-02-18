from django.db import models
from django.contrib.auth.models import User

# Create your models here.
class Video(models.Model):
    videoID = models.BigAutoField(primary_key=True)
    title = models.CharField(max_length=255)
    uploader = models.ForeignKey(User, on_delete=models.CASCADE)
    length = models.IntegerField(default=0)
    views = models.IntegerField(default=0)
    likes = models.IntegerField(default=0)
    dislikes = models.IntegerField(default=0)
    description = models.TextField()
    file_location = models.FileField(upload_to='videos/')
    thumbnail = models.ImageField(upload_to='thumbnails/')
    created_at = models.DateTimeField(auto_now_add=True)
    trending_score = models.IntegerField(default=0)

    def __str__(self):
        return self.title