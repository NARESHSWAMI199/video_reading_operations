
from django.urls import path
from .views import detect_face,form_view,verify_same_face_in_video,video_thumbnail,video_to_gif,remove_image_files

app_name = 'core'
urlpatterns = [
    path('',form_view,name="form_view"),
    path('compress/',detect_face ,name='compress'),
    path('verify/',verify_same_face_in_video,name='verify'),
    path('thumbnail/',video_thumbnail,name='thumbnail'),
    path('gif/',video_to_gif,name=''),
    path('delete/',remove_image_files,name='delete'),

]
