from django.urls import path
from . import views

app_name = 'video'
urlpatterns = [
    path('<int:videoID>/', views.watch_video, name='watch_video'),
]