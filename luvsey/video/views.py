from django.shortcuts import render
from django.shortcuts import get_object_or_404
from .models import Video

# Create your views here.

def upload_end(request):
    return render('home/index.html')

def watch_video(request, videoID):
    video = get_object_or_404(Video, videoID=videoID)
    return render(request, 'video/video.html', {'video': video})