from django.shortcuts import render, redirect
from django.contrib.auth import login as auth_login, authenticate
from django.contrib.auth.forms import AuthenticationForm, UserCreationForm
from django.contrib.auth import logout
import os
import subprocess
from django.core.files.storage import FileSystemStorage
from django.conf import settings
from django.http import HttpResponseBadRequest
from video.models import Video
import boto3
from botocore.exceptions import NoCredentialsError
import uuid

# Create your views here.
def index(request):
    return render(request, 'home/index.html')

def user_login(request):
    if request.method == 'POST':
        form = AuthenticationForm(request, data=request.POST)
        if form.is_valid():
            username = form.cleaned_data.get('username')
            password = form.cleaned_data.get('password')
            user = authenticate(username=username, password=password)
            if user is not None:
                auth_login(request, user)
                return redirect('index')
    else:
        form = AuthenticationForm()
    return render(request, 'profile/login.html', {'form': form})

def signup(request):
    if request.method == 'POST':
        form = UserCreationForm(request.POST)
        if form.is_valid():
            user = form.save()
            auth_login(request, user)
            return redirect('index')
    else:
        form = UserCreationForm()
    return render(request, 'profile/signup.html', {'form': form})

def logout_view(request):
    logout(request)
    return redirect('index')

def upload_video(request):
    if request.method == 'POST' and 'video' in request.FILES:
        video = request.FILES['video']
        if not video.name.endswith(('.mp4', '.avi', '.mov', '.mkv')):
            return HttpResponseBadRequest('Invalid file format')
        
        # Generate a unique filename to avoid conflicts
        unique_filename = f"{uuid.uuid4()}.mp4"
        fs = FileSystemStorage()
        filename = fs.save(unique_filename, video)
        uploaded_file_path = fs.path(filename)
        ffmpeg_path = r'c:/ffmpeg/bin/ffmpeg.exe'  # Replace with the actual path to ffmpeg.exe
        
        try:
            # Extract video length
            print("Extracting video length...")
            result_length = subprocess.run([ffmpeg_path, '-i', uploaded_file_path, '-hide_banner'], capture_output=True, text=True)
            duration_line = [line for line in result_length.stderr.split('\n') if 'Duration' in line]
            if duration_line:
                duration_str = duration_line[0].split(',')[0].split('Duration: ')[1].strip()
                h, m, s = duration_str.split(':')
                video_length = int(h) * 3600 + int(m) * 60 + float(s)
            else:
                video_length = 0.0
            print(f"Video length: {video_length} seconds")

            # Save the video object without file location
            print("Saving video object...")
            video_obj = Video.objects.create(
                uploader=request.user,
                length=video_length
            )

            # Update the file location with the video ID
            compressed_file_path = os.path.join(settings.MEDIA_ROOT, f'compressed_{video_obj.videoID}.mp4')
            print("Compressing video...")
            result = subprocess.run([ffmpeg_path, '-i', uploaded_file_path, '-vcodec', 'libx264', '-crf', '28', compressed_file_path], check=True, capture_output=True, text=True)
            print(result.stdout)
            print(result.stderr)
            os.remove(uploaded_file_path)

            # Upload the compressed video to R2 storage
            s3_client = boto3.client(
                's3',
                endpoint_url=settings.AWS_S3_ENDPOINT_URL,
                aws_access_key_id=settings.AWS_ACCESS_KEY_ID,
                aws_secret_access_key=settings.AWS_SECRET_ACCESS_KEY
            )
            try:
                s3_client.upload_file(compressed_file_path, settings.AWS_STORAGE_BUCKET_NAME, f'compressed_{video_obj.videoID}.mp4')
                video_url = f"{settings.AWS_S3_ENDPOINT_URL}/{settings.AWS_STORAGE_BUCKET_NAME}/compressed_{video_obj.videoID}.mp4"
                print(f"Video uploaded to R2 storage: {video_url}")
            except NoCredentialsError:
                return HttpResponseBadRequest('Credentials not available')

            # Update the video object with the file location
            video_obj.file_location = video_url
            video_obj.save()
            print("Video object saved successfully")

        except subprocess.CalledProcessError as e:
            print(e.stderr)
            return HttpResponseBadRequest('Video compression failed')
        
        return redirect('video:watch_video', videoID=video_obj.videoID)
    return render(request, 'upload/upload.html')