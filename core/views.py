from django.shortcuts import render
import cv2
import numpy as np
from rest_framework.decorators import api_view
from .form import VideoForm
import face_recognition
from django.contrib.staticfiles.storage import staticfiles_storage
# from django.core.files.storage import default_storage
from django.core.files.storage import FileSystemStorage
from rest_framework.response import Response
from django.conf import settings
import os
import shutil
import math
import datetime
from concurrent.futures import ThreadPoolExecutor
from colorama import Fore, Back, Style
# Create your views here.
import requests
import os,sys
from urllib.parse import urlparse
import glob
import contextlib
from PIL import Image
from concurrent.futures import ThreadPoolExecutor
from threading import Thread
import time
import requests
from moviepy.editor import VideoFileClip

''' you can use this for file 
    file_name = default_storage.save(video.name, video)
    #  Reading file from storage
    file = default_storage.open(file_name)
    file_url = default_storage.url(file_name)
    
'''



CALLBACK_URL = settings.CALLBACK_URL
VIDEO_FOLDER = settings.VIDEO_FOLDER
IMAGE_FOLDER = settings.IMAGE_FOLDER
SCREEN_SHOT_FOLDER = settings.SCREEN_SHOT_FOLDER
XML_PATH_URL = settings.XML_PATH_URL

@api_view(["GET"])
def form_view(request):
    return render(request,'index.html')






@api_view(['POST'])
def remove_image_files(request):
    files = request.POST.get('images')
    images = files.strip('][').split(', ')
    print("images for delete ... ", images)
    try:
        for image in images:
            print(image)
            os.remove(os.path.join(image))
        return Response({"message" : "successfully delete"},status=200)
    except Exception as e:
        return Response({"message" : str(e)},status=500)




def create_folder(path):
    isExist = os.path.exists(path)
    if not isExist: 
        # Create a new directory because it does not exist
        os.makedirs(path)
        print("The new directory is created!")


# @api_view(['GET','POST'])

def compress_video(file_path,filename):
    try:
        width = 200
        height = 340
        fps = 30
        cap = cv2.VideoCapture(file_path)
        fourcc = cv2.VideoWriter_fourcc(*'XVID')  
        out_file_path =  os.path.join(settings.MEDIA_ROOT, 'compressed/'+filename)
        out = cv2.VideoWriter(out_file_path,fourcc, fps, (width,height))
        processing = False
        while True:
            ret, frame = cap.read()
            if ret == True:
                b = cv2.resize(frame,(width,height),fx=0,fy=0, interpolation = cv2.INTER_CUBIC)
                out.write(b)
                processing = True
            else:
                break
        cap.release()
        out.release()
        cv2.destroyAllWindows()
        os.remove(file_path)

        if processing:
            return out_file_path
        else:
            return None
    except Exception as e:
        print(Fore.RED ,str(e))
        return None





def is_video(url):
    content_type = requests.head(url).headers.get('content-type')
    if 'video' in content_type:
        return True
    return False

def is_image(url):
    content_type = requests.head(url).headers.get('content-type')
    if 'image' in content_type:
        return True
    return False


def is_downloadable(url):
    content_type = requests.head(url).headers.get('content-type')
    if 'image' in content_type or 'video' in content_type:
        return True
    return False



def download_file(url,folder):        
    a = urlparse(url)
    if is_downloadable(url):
        r = requests.get(url, allow_redirects=True)
        filename = os.path.basename(a.path)
        open(folder+filename, 'wb').write(r.content)
        return filename
    else: 
        return None
   
        
    



@api_view(["POST"])
def detect_face (request):
    try:
        
        form = VideoForm(request.POST or None)
        if form.is_valid():
            video = request.POST['video']
            image = request.POST['image']
            create_folder(VIDEO_FOLDER)
            create_folder(SCREEN_SHOT_FOLDER)

            '''TODO :  remove these commented line after testing.'''

            # video = request.FILES['video']
            # image = request.FILES['image']

            # video_fs = FileSystemStorage(location=video_folder)
            # image_fs = FileSystemStorage(location=image_folder)

            # video_name = video_fs.save(video.name, video)
            # image_name = image_fs.save(image.name, image)

            if not is_image(image):
                return Response({'message' : 'Not a valid image url.'})
            if not is_video(video):
                return Response({'message' : 'Not a valid video url.'})
            
            video_name = download_file(video,VIDEO_FOLDER)
            image_name = download_file(image,IMAGE_FOLDER)

            if (video_name is None):
                return Response({'message' : 'Not a valid video url.'})
            if(image_name is None):
                return Response({'message' : 'Not a valid video url.'}) 


            video_file_path = os.path.join(settings.MEDIA_ROOT,'video/'+video_name)
            com_file_path = compress_video(video_file_path,video_name)
            if com_file_path is None:
                return Response(data={"message", "Not a valid file."}, status=400)
            
            input_movie= cv2.VideoCapture(com_file_path)

            length = int(input_movie.get(cv2.CAP_PROP_FRAME_COUNT))

            image_path =  os.path.join(settings.MEDIA_ROOT, 'images/'+image_name)
            
            image = face_recognition.load_image_file(image_path)
            face_encoding = face_recognition.face_encodings(image)[0]

            fps = int(input_movie.get(cv2.CAP_PROP_FPS)) 
            frame_width = int(input_movie.get(cv2.CAP_PROP_FRAME_WIDTH))
            frame_height = int(input_movie.get(cv2.CAP_PROP_FRAME_HEIGHT))
            duration = input_movie.get(cv2.CAP_PROP_POS_MSEC)
            # frame_count = input_movie.get(cv2.CAP_PROP_FRAME_COUNT)

            if not frame_width > 0:
                return Response(data={"message":"Not a valid file."}, status=400)

            print('frame width : ' ,frame_width ,' frame height : ',frame_height , " frame rate ", fps)

            known_faces = [
                face_encoding,
            ]


            match_duration = []
            # Initialize variables
            face_locations = [image]
            face_encodings = []
            frame_count = 0
            for i in range(frame_count,length):
                
                #reading according my need
                input_movie.set(cv2.CAP_PROP_POS_FRAMES, frame_count)
                # Grab a single frame of video
                ret, frame = input_movie.read()
                frame_count+=1

                #calculating time
                seconds = round(frame_count / fps)
                video_time = datetime.timedelta(seconds=seconds)

                # Quit when the input video file ends
                if not ret:
                    break

                # Convert the image from BGR color (which OpenCV uses) to RGB color (which face_recognition uses)
                rgb_frame = frame[:, :, ::-1]

                # # Find all the faces and face encodings in the current frame of video
                face_locations = face_recognition.face_locations(rgb_frame)
                face_encodings = face_recognition.face_encodings(rgb_frame, face_locations)

                for face_encoding in face_encodings:
                    # See if the face is a match for the known face(s)
                    match = face_recognition.compare_faces(known_faces, face_encoding, tolerance=0.50)

                    '''face is matched here you can skip here....'''
                    if match[0]: 
                        frame_count = (math.ceil(frame_count/fps) * fps) +1
                        match_duration.append(str(video_time))
    
            # All done!
            input_movie.release()
            os.remove(com_file_path)
            os.remove(image_path)
            return Response(data={"match_duration" : match_duration },status=200)
           
        else:
            return Response(data={"message": "Not a valid file."}, status=400)
       
    except Exception as e:
        print(Fore.RED ,str(e))
        return Response(data={"message" : str(e)}, status=400)
       








def get_encoded_image(image_path):
    image = face_recognition.load_image_file(image_path)
    encoding_faces = face_recognition.face_encodings(image)
    image_encode = encoding_faces[0] if len(encoding_faces) > 0 else None  
    return image_encode



def save_screeshots(video_url,postid):
    try:
        # Finished in 110.08 second(s)
        # 109.06
        start = time.perf_counter()
        # await asyncio.sleep(100.0)
        create_folder(VIDEO_FOLDER)
        create_folder(SCREEN_SHOT_FOLDER)
        # Downloading the video file..
        video_name = download_file(video_url,VIDEO_FOLDER)
        print('the video name : ',video_name)
        if (video_name is None):
            context = {"message" : 'Not a valid video url.', 'images' : [],"action_id" : postid, "action_type" : "U"}
            x = requests.post(CALLBACK_URL, json = context)
            print(x.text)
            raise Exception('Not a valid video url.')
            # return Response({'message' : 'Not a valid video url.'},status=400)

        # retrive the video file from the save location.
        video_file_path = os.path.join(settings.MEDIA_ROOT,'video/'+video_name)
        cap = cv2.VideoCapture(video_file_path)
        image_paths = []
        fps = int(cap.get(cv2.CAP_PROP_FPS)) 
        count = 0
        length = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
        frame_count = 0
        for i in range(frame_count,length):
            #reading according my need
            cap.set(cv2.CAP_PROP_POS_FRAMES, frame_count)
            ret,frame = cap.read()
            frame_count+=1

            # Quit when the input video file ends
            if not ret:
                break

            # cv2.imshow('window-name',frame)
            # Below you have to insert the full path of XML file, below is mine
            face_cascade = cv2.CascadeClassifier(XML_PATH_URL)
            gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
            faces = face_cascade.detectMultiScale(gray, 1.3, 5)

            if(frame_count > 90 and len(image_paths) < 1):
                context = {"message" : 'Faces not found in first 3 seconds', 'images' : [],"action_id" : postid, "action_type" : "U"}
                x = requests.post(CALLBACK_URL, json = context)
                print(x)
                return None
        
            # # Find all the faces and face encodings in the current frame of video
            for (x, y, w, h) in faces:    
                cv2.imwrite(SCREEN_SHOT_FOLDER+video_name+"frame%d.jpg" % count,frame)
                image_paths.append(SCREEN_SHOT_FOLDER+video_name+"frame%d.jpg" % count)
                count = count + 1       
                '''TODO : there we skip the video '''
                frame_count = (math.ceil(frame_count/fps) * fps) +fps
            


            print(frame_count,' : ',length , " : ", fps)

            # if (cv2.waitKey(30) & 0xff) == 27:
            #     break

        cap.release()
        os.remove(video_file_path)
        verify_faces(image_paths,postid)
    except Exception as e:
        exc_type, exc_obj, exc_tb = sys.exc_info()
        fname = os.path.split(exc_tb.tb_frame.f_code.co_filename)[1]
        print(Fore.RED,exc_obj,exc_type, fname, exc_tb.tb_lineno)
        return Response({"message" : str(e)},status=500)
    
    


def verify_faces(image_paths,postid):
    try:
        first_image = get_encoded_image(image_paths[0]) if (len(image_paths) > 0)  else ''
        unknown_faces = []
        for image_path in image_paths: 
            image = get_encoded_image(image_path) if get_encoded_image(image_path) is not None else ''  
            if len(image) > 0:
                match = face_recognition.compare_faces([first_image],image, tolerance=0.50)
                if not match[0]:
                    if (len(unknown_faces) < 2):
                        unknown_faces.append(image_path)
                    else:
                        break
        print(unknown_faces)
        if (len(unknown_faces) > 0):


            context = {"message" : 'some extra persons found.', "images": unknown_faces,"action_id" : postid, "action_type" : "M"}
            x = requests.post(CALLBACK_URL,json = context)
            print(x.text)

            for image in unknown_faces:
                image_paths.remove(image)
        elif(len(image_paths) > 0 and len(unknown_faces) < 1):
            image_paths.remove(image_paths[0])
            context = {"message" : 'verfied user.',"action_id" : postid, 'images' : [image_paths[0]],"action_type": "S"}
            x = requests.post(CALLBACK_URL, json=context)
            print(x.text)
        else:
            context = {"message" : 'Faces not found', 'images' : [],"action_id" : postid, "action_type" : "U"}
            x = requests.post(CALLBACK_URL, json = context)
            print(x.text)

        remove_files(image_paths)
        
    except Exception as e:
            exc_type, exc_obj, exc_tb = sys.exc_info()
            fname = os.path.split(exc_tb.tb_frame.f_code.co_filename)[1]
            print(Fore.RED,exc_obj,exc_type, fname, exc_tb.tb_lineno)
            return Response({"message" : str(e)},status=500)





def remove_files(unused_images):
    try: 
        for image in unused_images:
            print('removed : ',image)
            os.remove(image)
    except Exception as e: 
            exc_type, exc_obj, exc_tb = sys.exc_info()
            fname = os.path.split(exc_tb.tb_frame.f_code.co_filename)[1]
            print(Fore.RED,exc_obj,exc_type, fname, exc_tb.tb_lineno)
            return Response({"message" : str(e)},status=500)






@api_view(["POST"])
def verify_same_face_in_video(request):
    try: 

        print(request.POST )

        form = VideoForm(request.POST or None)
        if not form.is_valid():
            return Response({"message" : form.errors},status=400)
        video_url = request.POST['video']
        post_id = form.cleaned_data.get("id")
        print('the video url ',video_url)


        
        with ThreadPoolExecutor(10) as executor:
           executor.map(Thread(target=save_screeshots, args=(video_url, post_id )).start())
            # executor.map(save_screeshots,((video_url, post_id ),))
           
    
        return Response({"message" : 'Processing...'}, status=200)

    except Exception as e:
            exc_type, exc_obj, exc_tb = sys.exc_info()
            fname = os.path.split(exc_tb.tb_frame.f_code.co_filename)[1]
            print(Fore.RED,exc_obj,exc_type, fname, exc_tb.tb_lineno)
            return Response({"message" : str(e)},status=500)





@api_view(["POST"])
def video_thumbnail(request):
    try: 
        location = ''
        create_folder(VIDEO_FOLDER)
        create_folder(SCREEN_SHOT_FOLDER)
        form = VideoForm(request.POST or None)
        if not form.is_valid():
            return Response({"message" : form.errors},status=400)
        video_url = request.POST['video']
        # Downloading the video file..
        video_name = download_file(video_url,VIDEO_FOLDER)
        if (video_name is None):
            return Response({'message' : 'Not a valid video url.'},status=400)
        # retrive the video file from the save location.
        video_file_path = os.path.join(settings.MEDIA_ROOT,'video/'+video_name)


        cam = cv2.VideoCapture(video_file_path)
        try:
            # creating a folder named data
            if not os.path.exists('data'):
                os.makedirs('data')

        # if not created then raise error
        except OSError:
            print ('Error: Creating directory of data')
        # reading from frame
        ret,frame = cam.read()
        if ret:
            # if video is still left continue creating images
            name = SCREEN_SHOT_FOLDER+video_name+'thumnail'+str(datetime.datetime.now()) + '.jpg'
            print ('Creating...' + name)
            # writing the extracted images
            cv2.imwrite(name, frame)
            location = name
            # increasing counter so that it will
            # show how many frames are created
        # Release all space and windows once done
        cam.release()
       
        return Response({"image_name": location }, status=200)
        
    except Exception as e:
            exc_type, exc_obj, exc_tb = sys.exc_info()
            fname = os.path.split(exc_tb.tb_frame.f_code.co_filename)[1]
            print(Fore.RED,exc_obj,exc_type, fname, exc_tb.tb_lineno)
            return Response({"message" : str(e)},status=500)



@api_view(['post'])
def video_to_gif(request):
    create_folder(VIDEO_FOLDER)
    create_folder(SCREEN_SHOT_FOLDER)
    create_folder(VIDEO_FOLDER+'GIF/')
    form = VideoForm(request.POST or None)
    if not form.is_valid():
        return Response({"message" : form.errors},status=400)
    video_url = request.POST['video']
    # Downloading the video file..
    video_name = download_file(video_url,VIDEO_FOLDER)
    if (video_name is None):
        return Response({'message' : 'Not a valid video url.'},status=400)
    # retrive the video file from the save location.
    video_file_path = os.path.join(settings.MEDIA_ROOT,'video/'+video_name)
    videoClip = VideoFileClip(video_file_path)
    # getting only first 5 seconds
    videoClip = videoClip.subclip(0, 5)
    videoClip.write_gif(VIDEO_FOLDER+'GIF/'+video_name+str(datetime.datetime.now())+".gif")
    return Response('successs')