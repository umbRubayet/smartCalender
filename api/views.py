from django.shortcuts import render
from rest_framework.decorators import api_view
from rest_framework import status
#serializers-------
from .serializers import UserSerializer
from .serializers import MonthViewSerializer
from .serializers import TaskSerializer
from .serializers import ProfileSerializer
from .serializers import TopTaskSerializer
from .serializers import TaskSearchSerializer
from .serializers import WeatherSerializer
from .serializers import HolidaySerializer
from .serializers import GroupSerializer
from .serializers import TagMeSerializer
from .serializers import NoteSerializer
#serializers--------


#models---------
from .models import User
from .models import Info
from .models import MonthView
from .models import Task
from .models import FriendList
from .models import ForgotPass
from .models import Weather
from .models import Holiday
from .models import Group
from .models import TagMe
from .models import Note
#models---------

from rest_framework.response import Response
import json
import requests
import dateutil.parser
from collections import defaultdict

from django.core.mail import send_mail
from datetime import datetime,timedelta
from django.utils import timezone
import hashlib
import uuid
import requests

import csv
import pandas as pd
# Create your views here.

@api_view (['POST'])
def user_list(request):

    if request.method =='POST':

        mail = request.POST.get('mail')
        password = request.POST.get('password')
        exists = User.objects.filter(mail=mail).exists()
        if exists:
            response = {"success":False,"data":{},"message":"already exists"}
            return Response(response,status=status.HTTP_200_OK)
        else:
            new_user = User.objects.create(mail=mail,password=password,image=None,name=None,phoneNumber=None)
            serializer = UserSerializer(new_user)
            response = {"success":True,"data": serializer.data,"message":"Successfully signed up"}
            return Response(response,status=status.HTTP_201_CREATED)
        response = {"success":False,"data":{}, "message":"bad request"}
        return Response(response , status=status.HTTP_400_BAD_REQUEST)


@api_view(['POST'])
def login(request):

    if request.method == 'POST':
        requested_mail = request.POST.get('mail')
        requested_password = request.POST.get('password')
        exists = User.objects.filter(mail = requested_mail).exists()

        if exists :
            user = User.objects.get(mail=requested_mail)
            serializer = UserSerializer(user)
            if requested_password ==  user.password :
                response = {"success":True,"data":serializer.data,"message":"logged in"}
                return Response(response,status=status.HTTP_200_OK)
            else:
                response = {"success":False,"message":"password didn't match"}
                return Response(response, status = status.HTTP_200_OK)

        else:
            response = {"success":False,"message":"user doesn't exist"}
            return Response(response, status=status.HTTP_404_NOT_FOUND)


@api_view (['GET'])
def get_month_tasks(request, user_id):
    """ get all tasks for an user from monthView table in specific date range """
    if request.method == 'GET':
        exists = MonthView.objects.filter(user_id = user_id).exists()

        if exists :
            try:
                monthViewAllTasks = MonthView.objects.filter(user_id = user_id)
                serializer = MonthViewSerializer(monthViewAllTasks, many=True)
                response = {"success":True, "data":serializer.data, "message":"all tasks of month"}
                return Response(response, status = status.HTTP_200_OK)
            except Exception as ex:
                reponse = {"success":False,"data":[],"message":"exception..."}
                return Response (response , status = statu.HTTP_400_BAD_REQUEST)
        else :
            response = {"success":True,"data":[], "message":"user doesn't have any task yet" }
            return Response (response , status = status.HTTP_200_OK)

        return Response (status = status.HTTP_400_BAD_REQUEST)


@api_view(['POST','GET'])
def task(request, user_id):

    if request.method == 'POST':

        date = request.POST.get('date')
        image = request.data['file']
        category = request.POST.get('category')
        title = request.POST.get('title')
        from_time = request.POST.get('from_time')
        to_time = request.POST.get('to_time')
        description = request.POST.get('description')
        reminders = request.POST.get('reminders')
        reminders = json.loads(reminders)
        tagged = request.POST.get('tagged')
        tagged = json.loads(tagged)
        tag_flag = request.POST.get('tag_flag')
        tag_flag = json.loads(tag_flag)
        group_tag = request.POST.get('group_tag')
        group_tag_list = json.loads('group_tag')

        if not from_time:
            from_time=None
        if not to_time:
            to_time=None
        if not description:
            description = None
        if not reminders:
            reminders = None
        if not tagged:
            tagged = None
        if not image:
            image = None
        if not group_tag_list:
            group_tag_list = None

        try:
            task = Task.objects.create(date=date,image=image,category=category,title=title,from_time=from_time,to_time=to_time,description = description,tagged=tagged,reminders=reminders, user_id=user_id,tag_flag=tag_flag,group_tag=group_tag_list)
            taskSerializer = TaskSerializer(task)
            response = {"success":True, "data":taskSerializer.data, "message":"new task added"}

            """post task to month view to update internally """

            topTasks_dict = topTaskofDate(user_id,date)

            monthView_user = MonthView.objects.get_or_create(user_id=user_id,date=date)
            monthView_user[0].task_count = topTasks_dict['count']
            monthView_user[0].tasks = topTasks_dict['tasks']
            monthView_user[0].tag_flag = topTasks_dict['tag_flag']
            monthView_user[0].save()

            if tagged:
                for tagged_obj in tagged:
                    tagged_id = json.loads(tagged_obj['userId'])
                    TagMe.objects.create(tagged_id=tagged_id,tagger_id=user_id,task_id=task.id)

            if group_tag_list:
                for group_id in group_tag_list:
                    group_object = Group.objects.get(id=group_id)
                    group_people_list = group_object.group_list

                    for tagged_person in group_people_list:
                        TagMe.objects.create(tagger_id=user_id,tagged_id=tagged_person,task_id=task.id)


            print("monthview")
            return Response(response, status = status.HTTP_201_CREATED)

        except Exception as excep:
            print("exception..." + str(excep))
            response = {"success":False,"message":"exception occured . . ","data":[]}

            return Response(response, status=status.HTTP_400_BAD_REQUEST)

    elif request.method == 'GET':
        try:
            allTasks = Task.objects.filter(user_id=user_id)
            serializer = TaskSerializer(allTasks, many=True)
            for data in serializer.data:
                group_list = []
                if data['group_tag'] is not None:
                    for group_id in data['group_tag']:
                        group_info = {}
                        group = Group.objects.get(id=group_id)
                        group_info['name'] = group.group_name
                        group_info['id'] = group.id
                        group_list.append(group_info)

                    data['group'] = group_list
            response = {"success":True, "message":"all detailed tasks", "data":serializer.data}
            return Response (response, status= status.HTTP_200_OK)
        except Exception as ex:
            response = {"success":False,"message":"error occured", "data":[] }
            return Response (response, status=status.HTTP_400_NOT_FOUND)

def topTaskofDate(user_id,date):
    try:

        allTasks = Task.objects.filter(user_id=user_id, date=date, complete=False).order_by("from_time")
        taskCount = allTasks.count()
        tag_tasks=allTasks.filter(tag_flag=True)
        tag_flag = False
        if tag_tasks.count() > 0:
            tag_flag = True

        topThreeTasks = allTasks[:3]
        topTaskSerializer = TopTaskSerializer(topThreeTasks, many=True)

        result={}
        result['count'] = taskCount
        result['tasks'] = topTaskSerializer.data[:]
        result['tag_flag'] = tag_flag
        return result
    except:
        print("topTaskof date exception")
        return None


@api_view(['POST'])
def getTasksfromDate(request,user_id):

    if request.method == 'POST':
        date = request.POST.get('date')
        try:
            allTasks = Task.objects.filter(user_id=user_id,date=date).order_by("from_time")
            serializer = TaskSerializer(allTasks, many=True)
            for data in serializer.data:
                group_list = []
                if data['group_tag'] is not None:
                    for group_id in data['group_tag']:
                        group_info = {}
                        group = Group.objects.get(id=group_id)
                        group_info['name'] = group.group_name
                        group_info['id'] = group.id
                        group_list.append(group_info)

                    data['group'] = group_list
            response = {"success":True,"message":"all tasks of date","data":serializer.data}
            return Response(response,status=status.HTTP_200_OK)
        except:
            response = {"success":False,"message":"error occured", "data":[]}
            return Response(response, status=status.HTTP_400_BAD_REQUEST) 

@api_view(['PUT','DELETE','GET'])
def editTask(request, task_id):
    if request.method == 'DELETE':
        try:
            task = Task.objects.get(id=task_id)
            date = task.date
            user_id = task.user_id
            task.delete()
            response = {"success":True,"message":"deleted"}

            """ MonthView Update """
            topTasks_dict = topTaskofDate(user_id,date)

            monthView_user = MonthView.objects.get_or_create(user_id=user_id,date=date)
            monthView_user[0].task_count = topTasks_dict['count']
            monthView_user[0].tasks = topTasks_dict['tasks']
            monthView_user[0].tag_flag = topTasks_dict['tag_flag']
            monthView_user[0].save()
            """ """
            return Response (response, status=status.HTTP_200_OK)
        except:
            response = {"success":False, "message":"error"}
            return Response (response, status=status.HTTP_400_BAD_REQUEST)

    if request.method == 'PUT':
        date = request.POST.get('date')
        category = request.POST.get('category')
        title = request.POST.get('title')
        from_time = request.POST.get('from_time')
        to_time = request.POST.get('to_time')
        image = request.data['file']
        description = request.POST.get('description')
        reminders = request.POST.get('reminders')
        reminders = json.loads(reminders)
        tagged = request.POST.get('tagged')
        tagged = json.loads(tagged)
        tag_flag = request.POST.get('tag_flag')
        tag_flag = json.loads(tag_flag)
        group_tag = request.POST.get('group_tag')
        group_tag_list = json.loads(group_tag)

        if not from_time:
            from_time=None
        if not to_time:
            to_time=None
        if not description:
            description = None
        if not reminders:
            reminders = None
        if not tagged:
            tagged = None
        if not image:
            image = None
        if not group_tag_list:
            group_tag_list = None

        try:
            task = Task.objects.get(id=task_id)
            task.date = date
            task.title = title
            task.category = category
            task.from_time = from_time
            task.to_time = to_time
            task.description = description
            task.reminders = reminders
            task.tagged = tagged
            task.tag_flag = tag_flag
            task.group_tag = group_tag_list
            task.save()

            user_id = task.user_id

            serializer = TaskSerializer(task)
            response = {"success":True,"message":"updated successfully","data":[serializer.data]}

            print("response")
            """post task to month view to update internally """

            topTasks_dict = topTaskofDate(user_id,date)
            print("top task")
            monthView_user = MonthView.objects.get_or_create(user_id=user_id,date=date)
            monthView_user[0].task_count = topTasks_dict['count']
            monthView_user[0].tasks = topTasks_dict['tasks']
            monthView_user[0].tag_flag = topTasks_dict['tag_flag']
            monthView_user[0].save()
            print("monthview sAVE")
            return Response (response,status = status.HTTP_200_OK)
        except:
            response = {"success":False,"message":"couldn't update","data":[]}
            return Response (response,status=status.HTTP_400_BAD_REQUEST)

    if request.method == 'GET':
        try:
            task = Task.objects.get(id=task_id)
            serializer = TaskSerializer(task)
            response = {"success":True,"message":"task","data":[serializer.data]}
            return Response(response,status=status.HTTP_200_OK)
        except:
            response = {"success":False,"message":"couldn't get task","data":[]}
            return Response(response,status = status.HTTP_400_BAD_REQUEST)


@api_view(['GET'])
def search(request, user_id , text):

    if request.method == 'GET':
        try:
            tasks = Task.objects.filter(user_id=user_id, title__icontains=text).order_by("from_time")
            serializer = TaskSearchSerializer(tasks, many=True)

            response = {"data":serializer.data}
            return Response(response, status=status.HTTP_200_OK)
        except Exception as ex:
            print("Exception... "+ str(ex))
            response = {"data":[]}
            return Response (response, status=status.HTTP_400_BAD_REQUEST)

@api_view(['GET','PUT'])
def profile(request, mail):

    if request.method=='PUT':
        user = User.objects.get(mail=mail)
        name=False
        phoneNumber=False
        image=False
        password = False
        try:
            image = request.data['file']
            user.image=image
        except:
            user.image=None
        try:
            name = request.data['name']
            user.name=name
        except:
            user.name=None
        try:
            phoneNumber = request.data['phoneNumber']
        except:
            pass
        try:
            password = request.data['password']
        except:
            pass
        if phoneNumber:
            user.phoneNumber = phoneNumber
        if password:
            user.password = password

        try:
            user.save()
            userSerializer = UserSerializer(user)
            response = {"data":userSerializer.data,"success":True,"message":"profile successfully updated"}
            return Response(response, status=status.HTTP_200_OK)
        except:
            response = {"success":False,"message":"Update was unsuccessfull"}
            return Response(response,status=status.HTTP_400_BAD_REQUEST)

    if request.method == 'GET':
        exists = User.objects.filter(mail=mail).exists()
        if exists:
            user = User.objects.get(mail=mail)
            try:
                userSerializer = UserSerializer(user)
                response = {"success":True,"message":"user found","data":userSerializer.data}
                return Response(response, status=status.HTTP_200_OK)
            except:
                response = {"success":False,"message":"error"}
                return Response(response,status=status.HTTP_400_BAD_REQUEST)

        else:
            response = {"success":True, "message":"user not found","data":{}}
            return Response(response,status=status.HTTP_404_NOT_FOUND)


def alreadyFriend(user_id,friend_id):
    exists = FriendList.objects.filter(user_id=user_id).exists()

    if exists:
        user = FriendList.objects.get(user_id=user_id)
        user_friend_list_dict = user.friend_list
        user_friend_list = user_friend_list_dict['friend_id']

        if str(friend_id) in user_friend_list:
            return True

        else:
            return False
    else:
        return False

@api_view(['GET'])
def findFriend(request, user_id, key):
    if request.method == 'GET':

        exists_mail = User.objects.filter(mail=key).exists()
        exists_phone = User.objects.filter(phoneNumber=key).exists()

        already_friend = False

        if exists_mail:
            user = User.objects.get(mail=key)
            profileSerializer = ProfileSerializer(user)

            already_friend =  alreadyFriend(user_id, user.id )

            response = {"already": already_friend, "success":True,"message":"user found","data":[profileSerializer.data]}
            return Response(response, status=status.HTTP_200_OK)
        elif exists_phone:
            user = User.objects.get(phoneNumber=key)
            profileSerializer = ProfileSerializer(user)

            already_friend = alreadyFriend(user_id,user.id)
            response = {"already":already_friend,"success":True,"message":"user found","data":[profileSerializer.data]}
            return Response(response, status=status.HTTP_200_OK)

        else:
            response = {"already":already_friend, "success":True,"message":"user not found","data":[]}
            return Response(response, status=status.HTTP_200_OK)

@api_view(['GET','POST','DELETE'])
def friend(request, user_id):

    if request.method == 'POST':
        friend_id = request.POST.get('friend_id')

        print("friend id.."+str(type(friend_id)))
        exists = FriendList.objects.filter(user_id=user_id).exists()

        try:
            if exists:
                user = FriendList.objects.get(user_id=user_id)
                friend_list = user.friend_list['friend_id']
                # if this userid is already added then no need to add.
                if not str(friend_id) in friend_list:
                    friend_list.append(friend_id)
                    user.friend_list['friend_id'] = friend_list
                    user.save()
                    response = {"success":True,"message":"friend added successfully"}
                    return Response(response, status=status.HTTP_201_CREATED)
                else:
                    response = {"success":False,"message":"already added"}
                    return Response (response, status=status.HTTP_200_OK)
            else:
                friend_list= {}
                friend_list['friend_id']= []
                friend_list['friend_id'].append(friend_id)
                FriendList.objects.create(user_id=user_id,friend_list=friend_list)
                response = {"success":True,"message":"friend added successfully"}
                return Response(response, status=status.HTTP_201_CREATED)

        except:
            response = {"success":False,"message":"couldn't add friend"}
            return Response(response,status=status.HTTP_400_BAD_REQUEST)

    if request.method=='GET':
        """ get all friends of a user_id """
        exists = FriendList.objects.filter(user_id=user_id).exists()

        if exists:
            try:
                user = FriendList.objects.get(user_id=user_id)

                friend_list = user.friend_list['friend_id']
                friends = User.objects.filter(id__in=friend_list)
                serializer = ProfileSerializer(friends,many=True)
                response = {"success":True,"data":serializer.data,"message":"all friends"}
                return Response(response,status=status.HTTP_200_OK)
            except:
                response = {"success":False, "data":[],"message":"error occured"} 
                return Response (response, status=status.HTTP_400_BAD_REQUEST)
        else:
            response = {"success":True,"data":[],"message":"no friend yet"}
            return Response(response, status=status.HTTP_200_OK)

    if request.method == 'DELETE':

        friend_id = request.POST.get('friend_id')
        try:
            user = FriendList.objects.get(user_id=user_id)
            friend_list = user.friend_list['friend_id']
            if str(friend_id) in friend_list:
                friend_list.remove(str(friend_id))
                user.friend_list['friend_id'] = friend_list
                user.save()
                response = {"success":True, "message":"friend removed"}
                return Response (response, status = status.HTTP_200_OK)
            else:
                response = {"success":True, "message":"not in friendlist"}
                return Response (response, status = status.HTTP_200_OK)

        except:
            response = {"success":False, "message":"couldn't remove"}
            return Response(response,status=status.HTTP_400_BAD_REQUEST)

@api_view (['POST'])
def taskStatusOperation(request,user_id,task_id):

    if request.method == 'POST':
        complition = request.POST.get('flag')
        complition = json.loads(complition)
        exists = Task.objects.filter(user_id=user_id,id=task_id)

        #complition = json.loads(complition)
        if exists:
            try:
                task = Task.objects.get(user_id=user_id,id=task_id)
                task.complete = complition
                task.save()
                
                date = task.date
                topTasks_dict = topTaskofDate(user_id,date)
                monthView_user = MonthView.objects.get_or_create(user_id=user_id,date=date)
                monthView_user[0].task_count = topTasks_dict['count']
                monthView_user[0].tasks = topTasks_dict['tasks']
                monthView_user[0].tag_flag = topTasks_dict['tag_flag']
                monthView_user[0].save()

                response = {"success":True, "message":"updated"}
                return Response(response, status = status.HTTP_200_OK)
            except Exception as ex:
                print("taskstatus exception... "+ str(ex))
                response = {"success":False, "message":"error"}
                return Response (response, status = status.HTTP_400_BAD_REQUEST)
        else:
            response = {"success":False,"message":"task doesn't exist"}
            return Response (response,status = status.HTTP_404_NOT_FOUND)

@api_view(['POST'])
def forgotPass(request):
    if request.method == 'POST':
        requested_mail = request.POST.get('mail')
        exists = User.objects.filter(mail=requested_mail).exists()

        if exists:

            requested_user = ForgotPass.objects.get_or_create(mail=requested_mail)

            last_update = requested_user[0].dateTime

            if timezone.now() > last_update :
                uid = str(uuid.uuid4())
                newStr = uid+requested_mail
                binary = newStr.encode('ascii')
                hash_object = hashlib.sha1(binary)
                hexvalue = hash_object.hexdigest()
                token = hexvalue[:8]
                print("token type "+str(type(token)) )
                print("token"+ token)
                requested_user[0].token = token
                requested_user[0].dateTime = timezone.now() + timedelta(seconds=30)
                requested_user[0].save()
                send_mail('password recover','your code is '+ token,'umbrubayet@gmail.com',[requested_mail])
                response = {"success":True,"message":"mail sent"}
                return Response(response,status=status.HTTP_200_OK)
            else:
                response = {"success":False,"message":"Too frequent recovey request. wait 30 seconds.."}
                return Response (response, status=status.HTTP_200_OK)
        else:
            response  ={"success":False,"message":"mail sent"}
            return Response(response,status = status.HTTP_200_OK)


@api_view(['POST'])
def matchForgotPass(request):
    if request.method == 'POST':
        token  = request.POST.get('token')
        new_password = request.POST.get('password')

        exists = ForgotPass.objects.filter(token=token).exists()

        if exists:
            gajni_user = ForgotPass.objects.get(token=token)
            gajni_mail = gajni_user.mail
            user = User.objects.get(mail=gajni_mail)
            user.password = new_password
            user.save()

            gajni_user.delete()

            response = {"success":True, "message":"password updated successfully"}
            return Response(response, status=status.HTTP_200_OK)

        else:
            response = {"success":False, "message":"invalid token"}
            return Response(response, status= status.HTTP_200_OK)

@api_view(['POST'])
def syncTask(request,user_id):
    if request.method == 'POST':

        data = request.POST.get('data')
        data_list = json.loads(data)

        try:
            for task in data_list:
                date = task['date']
                title = task['title']
                from_time = task['from_time']
                to_time = task['to_time']

                if not from_time:
                    from_time = None
                if not to_time:
                    to_time = None

                image = None
                category = "Event"
                description = None
                complete = False
                tagged = []
                tag_flag = False
                reminders = []

                print("date .. "+str(date))
                try :
                    task = Task.objects.create(user_id=user_id,date=date,title=title,from_time=from_time,to_time=to_time,image=image,category=category,description=description,complete=complete,tagged=tagged,tag_flag=tag_flag,reminders=reminders)

                    topTask_dict = {}
                    topTasks_dict = topTaskofDate(user_id,date)
                    monthView_user = MonthView.objects.get_or_create(user_id=user_id,date=date)
                    monthView_user[0].task_count = topTasks_dict['count']
                    monthView_user[0].tasks = topTasks_dict['tasks']
                    monthView_user[0].tag_flag = topTasks_dict['tag_flag']
                    monthView_user[0].save()

                except Exception as exc:
                    print("eception.... "+str(exc))
                    pass

            response = {"success":True,"message":"successfully updated"}
            return Response(response, status= status.HTTP_200_OK)
        except Exception as ex:
            print("exception "+ str(ex))
            response = {"success":False,"message":"exception . . ."}
            return Response (response, status = status.HTTP_400_OK)

@api_view(['POST'])
def weatherForecast(request, city):
    if request.method == 'POST':

        lat = request.POST.get('lat')
        lan = request.POST.get('lan')

        exists = Weather.objects.filter(city=city).exists()

        headers = {'X-Mashape-Key':'7VMha4L2otmshWK1NdInqJP6ZT3fp1WBxYGjsnV3MfkFVH8lYW'}
        url = 'https://simple-weather.p.mashape.com/weatherdata?lat='+str(lat)+'&lng='+str(lan)
        url_current = 'https://simple-weather.p.mashape.com/weather?lat='+str(lat)+'&lng='+str(lan)
        if exists:
            data = Weather.objects.get(city=city)
            last_update = data.last_update
            if timezone.now() >  last_update:
                response = requests.get(url, headers=headers)
                response_current = requests.get(url_current, headers=headers)

                if response.status_code == 200:
                    try:
                        response_data = json.loads(response.text)
                        base_object = response_data['query']['results']['channel']
                        atm = base_object['atmosphere']
                        astronomy = base_object['astronomy']
                        forecast = base_object['item']['forecast']
                        current = response_current.text

                        data.atm = atm
                        data.astronomy = astronomy
                        data.forecast = forecast
                        data.last_update = timezone.now() + timedelta(hours=6)
                        data.current = current
                        data.save()

                        serializer = WeatherSerializer(data)
                        response = {"success":True,"data":serializer.data,"message":"weather data"}
                        return Response(response,status=status.HTTP_200_OK)
                    except Exception as exc:
                        print("...."+str(exc)+"...")
                        response = {"success":False,"data":{},"message":"couldn't load weather"}
                        return Response(response,status=status.HTTP_400_BAD_REQUEST)

                else:
                    response = {"success":False,"data":{},"message":"weather data service problem"}
                    return Response(response, status= status.HTTP_404_NOT_FOUND)

            else:
                serializer = WeatherSerializer(data)
                response = {"success":True,"data":serializer.data,"message":"weather data"}
                return Response(response,status=status.HTTP_200_OK)
        else:
            response = requests.get(url, headers=headers)
            response_current = requests.get(url_current, headers=headers)

            if response.status_code == 200:
                try:
                    response_data = json.loads(response.text)
                    base_object = response_data['query']['results']['channel']
                    atm = base_object['atmosphere']
                    astronomy = base_object['astronomy']
                    forecast = base_object['item']['forecast']
                    country = base_object['location']['country']
                    city = base_object['location']['city']
                    last_update = timezone.now() + timedelta(hours=6)
                    current = response_current.text
                    weather = Weather.objects.create(current=current,last_update=last_update,country=country,city=city,atm=atm,astronomy=astronomy,forecast=forecast)
                    serializer = WeatherSerializer(weather)
                    response = {"success":True,"data":serializer.data,"message":"weather data"}
                    return Response(response,status=status.HTTP_200_OK)
                except Exception as exc:
                    print("...."+str(exc)+"...")
                    response = {"success":False,"data":{},"message":"couldn't load weather"}
                    return Response(response,status=status.HTTP_400_BAD_REQUEST)
            else:
                response = {"success":False,"data":{},"message":"weather data service problem"}
                return Response(response, status= status.HTTP_404_NOT_FOUND)

@api_view(['GET'])
def holiday(request,country):
    if request.method == 'POST':
        df = pd.read_csv("holiday.csv")
        target_rows = df.loc[df['country']==country]
        all_holidays = []
        for index,row in target_rows.iterrows():
            data = {}
            data['holiday_name'] = row['holiday_name']
            data['holiday_date'] = row['holiday_date']
            all_holidays.append(data)

        holiday = Holiday.objects.get_or_create(country=country,year=2018,holidays=all_holidays)
        serializer = HolidaySerializer(holiday)
        print(serializer.data)
        response = {"success":True,"message": country+" holiday added", "data":serializer.data}
        return Response(response,status=status.HTTP_200_OK)
    
    if request.method == 'GET':
        exists = Holiday.objects.filter(country=country).exists()
        if exists:
            try:
                holiday = Holiday.objects.get(country=country)
                serializer = HolidaySerializer(holiday)
                response = {"success":True,"message":"holidays","data":serializer.data}
                return Response(response,status=status.HTTP_200_OK)
            except Exception as ex:
                print("exception holiday get..."+ str(ex))
                response = {"success":False,"message":"error..","data":[]}
                return Response(response,status=status.HTTP_400_BAD_REQUEST)
        else:
            response = {"success":False,"message":"country's holiday data is not available"}
            return Response(response,status=status.HTTP_404_NOT_FOUND)
@api_view(['POST','GET'])
def group(request,user_id):
    if request.method == 'POST':
        group_name = request.POST.get('group_name')
        group_list = request.POST.get('group_list')
        print(str(type(group_list)))
        group_list = json.loads(group_list)
        print(str(type(group_list)))

        try:
            group = Group.objects.create(user_id=user_id,group_name=group_name,group_list=group_list)
            serializer = GroupSerializer(group)
            group_friends = User.objects.filter(id__in=group_list)
            group_friends_serializer = ProfileSerializer(group_friends, many=True)
            friends_dict = {}
            friends_dict['group_id'] = group.id
            friends_dict['group_friends'] = group_friends_serializer.data
            response = {"success":True,"message":"group created","group_data":serializer.data,"group_friends":friends_dict}
            return Response (response,status=status.HTTP_201_CREATED)
        except Exception as exc:
            print('exception... '+ str(exc))
            response = {"success":False, "message":"exception..","group_data":{},"group_friends":{[]}}
            return Response(response, status= status.HTTP_400_BAD_REQUEST)

    elif request.method == 'GET':
        try:
            groups = Group.objects.filter(user_id=user_id)
            serializer = GroupSerializer(groups, many=True)
            for group in serializer.data:
                group_friends = User.objects.filter(id__in=group['group_list'])
                group_friends_serializer = ProfileSerializer(group_friends, many=True)
                group['friends'] = group_friends_serializer.data
            response = {"success":True,"message":"groups","data":serializer.data}
            return Response (response,status=status.HTTP_200_OK)
        except Exception as ex:
            print("exception..." + str(ex))
            response = {"success": False , "message":"exception..."}
            return Response(response,status=status.HTTP_400_BAD_REQUEST)

@api_view(['GET','PUT','DELETE'])
def singleGroup(request,user_id,group_id):
    if request.method == 'GET':
        try:
            group = Group.objects.get(id=group_id)
            serializer = GroupSerializer(group)
            group_people_list = group['group_list']
            if group_people_list:
                group_friends = User.objects.filter(id__in=group_people_list)
                group_friends_serializer = ProfileSerializer(group_friends, many=True)
                friends_dict = {}
                friends_dict['group_id'] = group.id
                friends_dict['group_friends'] = group_friends_serializer.data
            else:
                friends_dict = {}
                friends_dict['group_id'] = group.id
                friends_dict['group_friends'] =[]
            response = {"success":True,"message":"group data","data":[serializer.data],"group_friends":friends_dict}
        except Exception as ex:
            print("exception..." + str(ex))
            response = {"success":False,"message":"error...."}
            return Response (response, status=status.HTTP_400_OK)

    if request.method == 'DELETE':
        try:
            group = Group.objects.get(id=group_id)
            group_name = group.group_name
            group.delete()
            response = {"success":True,"message":group_name+" group deleted"}
            return Response (response, status=status.HTTP_200_OK)

        except Exception as ex:
            print("exception ... "+ str(ex))
            response = {"success":False,"message":"exception.."}
            return Response (response, status=status.HTTP_400_BAD_REQUEST)

    if request.method == 'PUT':
        try:
            group_name = request.POST.get('group_name')
            group_list = request.POST.get('group_list')
            group_list = json.loads(group_list)

            group = Group.objects.get(id = group_id)
            group.group_name = group_name
            group.group_list = group_list
            group.save()

            response = {"success":True,"message":"group updated"}
            return Response (response,status=status.HTTP_200_OK)
        
        except Exception as ex:
            print("exception..." + str(ex))
            response = {"success":False,"message":"error ...."}
            return Response(response,status=status.HTTP_400_BAD_REQUEST)
@api_view(['GET','DELETE'])
def tagMe(request,tagged_id):
    if request.method == 'GET':
        try:
            tags = TagMe.objects.filter(tagged_id=tagged_id)
            serializer = TagMeSerializer(tags,many=True)
            for tag in serializer.data:
                tagger = User.objects.get(id=tag['tagger_id'])
                tagger_serializer = ProfileSerializer(tagger)
                tag['tagger'] = tagger_serializer.data
                task  = Task.objects.get(id=tag['task_id'])
                task_serializer = TaskSerializer(task)
                tag['task'] = task_serializer.data

            response = {"success":True,"message":"tagged tasks","data":serializer.data}
            return Response (response, status=status.HTTP_200_OK)
        except Exception as ex:
            print("exception..." + str(ex))
            response = {"success":False,"message":"error...","data":[]}
            return Response (response, status = status.HTTP_400_BAD_REQUEST)

    if request.method =='DELETE':
        tag_id = request.POST.get('tag_id')

        try:
            tag = TagMe.objects.get(id=tag_id)
            tag.delete()
            response = {"success":True,"message":"deleted"}
            return Response (response,status=status.HTTP_200_OK)
        except Exception as ex:
            print ("exception tag me ... "+ str(ex))
            response = {"success":False,"message":"error ...","data":[]}
            return Response (response, status=status.HTTP_400_BAD_REQUEST)

@api_view(['GET','POST'])
def notePost(request, user_id):
    if request.method == 'POST':
        try:
            title = request.POST.get('title')
            description = request.POST.get('description')

            note = Note.objects.create(title=title,description=description,user_id=user_id)
            response = {"success":True,"message":"saved"}
            return Response (response,status=status.HTTP_201_CREATED)
        except Exception as ex:
            print("exception.."+ str(ex))
            response = {"success":False,"message":"save unsuccessfull"}
            return Response(response,status=status.HTTP_400_BAD_REQUEST)

    if request.method == 'GET':
        try:
            notes = Note.objects.filter(user_id=user_id)
            serializer = NoteSerializer(notes,many=True)
            response = {"success":True,"data":serializer.data,"message":"all notes"}
            return Response(response,status=status.HTTP_200_OK)
        except Exception as ex:
            print("exception.. "+ str(ex))
            response = {"success":False,"data":[],"message":"error in get..."}
            return Response(response,status=status.HTTP_400_BAD_REQUEST)

@api_view(['GET','PUT','DELETE'])
def noteOperations(request,user_id,note_id):
    if request.method == 'GET':
        try:
            note = Note.objects.get(id=note_id)
            serializer = NoteSerializer(note)
            response = {"success":True,"message":"note","data":[serializer.data]}
            return Response(response,status=status.HTTP_200_OK)
        except Exception as ex:
            print("exception.. "+ str(ex))
            response = {"success":False,"data":[],"message":"error in get..."}
            return Response(response,status=status.HTTP_400_BAD_REQUEST)

    if request.method == 'DELETE':
        try:
            note = Note.objects.get(id=note_id)
            note.delete()
            response = {"success":True,"message":"note deleted"}
            return Response(response,status=status.HTTP_200_OK)
        except Exception as ex:
            print("exception.. "+ str(ex))
            response = {"success":False,"message":"error in deletion..."}
            return Response(response,status=status.HTTP_400_BAD_REQUEST)

    if request.method == 'PUT':
        try:
            title = request.POST.get('title')
            description = request.POST.get('description')
            note = Note.objects.get(id=note_id)
            note.title = title
            note.description = description
            note.save()
            response = {"success":True,"message":"note updated"}
            return Response (response,status=status.HTTP_200_OK)
        except Exception as ex:
            print("exception.. "+ str(ex))
            response = {"success":False,"message":"error in update..."}
            return Response(response,status=status.HTTP_400_BAD_REQUEST)
