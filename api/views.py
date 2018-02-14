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
from .serializers import TaskTagSerializer
from .serializers import GroupTagSerializer
from .serializers import FcmTokenSerializer
from .serializers import GroupMapSerializer
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
from .models import GroupMap
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
import datetime
import csv
import pandas as pd
import threading
import sys
from pyfcm import FCMNotification

import sys, os
# Create your views here.


push_service = FCMNotification(api_key="AAAAsyKdE-k:APA91bEYtdNnpTGmUsi6h8HVdgzmsFmLO9lxFVXhhQ-aEdwkqi5SOFq5nOPS4OSxZ1luZ2iFYNYdqbjghTp07Vl8NR4YjAJnt5mnjk81RrF49kaQORu-NTzVYAsQFic0HYyxowvcA61U")

TASK_TYPE = 1
GROUP_TYPE = 2

ADD_MESSAGE = " add you in "
REMOVE_MESSAGE = " removed you from "

@api_view (['POST'])
def user_list(request):

    if request.method =='POST':
        try:
            mail = request.POST.get('mail')
            password = request.POST.get('password')
            name = request.POST.get('name')

            fcm_token = request.POST.get('fcm_token')
            active = request.POST.get('active')
            active = json.loads(active)

            exists = User.objects.filter(mail=mail).exists()
            if exists:
                response = {"success":False,"data":{},"message":"already exists"}
                return Response(response,status=status.HTTP_200_OK)
            else:
                new_user = User.objects.create(mail=mail,password=password,image=None,name=name,phoneNumber=None,fcm_token=[fcm_token],active=active)
                serializer = UserSerializer(new_user)
                try:
                    send_mail('MY CALENDAR','your password is -- '+ password +" for My Calendar " ,'umbrubayet@gmail.com',[mail])
                except Exception as ex:
                    print(str(ex))
                response = {"success":True,"data": serializer.data,"message":"Successfully signed up"}

                return Response(response,status=status.HTTP_201_CREATED)
        except Exception as ex:
            print("exception signup... "+ str(ex))
            response = {"success":False,"data":{}, "message":"bad request"}
            return Response(response , status=status.HTTP_400_BAD_REQUEST)


@api_view(['POST'])
def login(request):

    if request.method == 'POST':
        try:
            requested_mail = request.POST.get('mail')
            requested_password = request.POST.get('password')

            fcm_token = request.POST.get('fcm_token')
            active = request.POST.get('active')
            active = json.loads(active)

            user = User.objects.filter(mail = requested_mail)

            if user :
                user = user[0]

                if requested_password ==  user.password :
                    if user.fcm_token:
                        old_token_list = user.fcm_token
                        if fcm_token in old_token_list:
                            pass
                        else:
                            old_token_list.append(fcm_token)
                            user.fcm_token = old_token_list
                            user.save()
                    else :
                        user.fcm_token = [fcm_token]
                        user.save()

                    serializer = UserSerializer(user)
                    response = {"success":True,"data":serializer.data,"message":"logged in"}
                    return Response(response,status=status.HTTP_200_OK)
                else:
                    response = {"success":False,"message":"password didn't match"}
                    return Response(response, status = status.HTTP_200_OK)

            else:
                response = {"success":False,"message":"user doesn't exist"}
                return Response(response, status=status.HTTP_200_OK)
        except Exception as ex:
            print("exception login... "+ str(ex))
            response = {"success":False,"data":{}, "message":"bad request"}
            return Response(response , status=status.HTTP_400_BAD_REQUEST)

@api_view (['GET'])
def get_month_tasks(request, user_id):
    """ get all tasks for an user from monthView table in specific date range """
    if request.method == 'GET':
        monthViewAllTasks = MonthView.objects.filter(user_id = user_id)
        if monthViewAllTasks :
            try:
                serializer = MonthViewSerializer(monthViewAllTasks, many=True)
                response = {"success":True, "data":serializer.data, "message":"all tasks of month"}
                return Response(response, status = status.HTTP_200_OK)
            except Exception as ex:
                exc_type, exc_obj, exc_tb = sys.exc_info()
                fname = os.path.split(exc_tb.tb_frame.f_code.co_filename)[1]
                print(exc_type, fname, exc_tb.tb_lineno)
                print("exception in month tasks... " + str(ex))
                reponse = {"success":False,"data":[],"message":"exception..."}
                return Response (response , status = statu.HTTP_400_BAD_REQUEST)
        else :
            response = {"success":True,"data":[], "message":"user doesn't have any task yet" }
            return Response (response , status = status.HTTP_200_OK)


def topTaskUpdateMonthView(user_id,date):
    topTask_dict = {}
    topTasks_dict = topTaskofDate(user_id,date)
    monthView_user = MonthView.objects.get_or_create(user_id=user_id,date=date)
    monthView_user[0].task_count = topTasks_dict['count']
    monthView_user[0].tasks = topTasks_dict['tasks']
    monthView_user[0].tag_flag = topTasks_dict['tag_flag']
    monthView_user[0].all_done = topTasks_dict['all_done']
    monthView_user[0].save()


def personTag(tagged,user_id,event_id, date,event_type):
    try:
        bulk_data_list = []
        for tagged_user_id in tagged:
            tagMe_obj = TagMe(tagged_id=tagged_user_id,tagger_id=user_id,event_id=event_id,date=date,event_type=event_type)
            bulk_data_list.append(tagMe_obj)

        #TagMe.objects.create(tagged_id=tagged_user_id,tagger_id=user_id,event_id=event_id,date=date,event_type=event_type)
        TagMe.objects.bulk_create(bulk_data_list)
    except Exception as ex:
        print ("person tag exception..." + str(ex))


def groupTag(group_tag_list, user_id, event_id,date,event_type):
    try:
        for group_id in group_tag_list:
            group_object = Group.objects.get(id=group_id)
            group_people_list = group_object.group_list

            for tagged_person in group_people_list:
                TagMe.objects.create(tagger_id=user_id,tagged_id=tagged_person,event_id=event_id,date=date,event_type=event_type)

    except Exception as ex:
        print("group tag exception..." + str(ex))



def fcmNotification(initiator_id, to_notify_user_list, event_type, event_id, message_action):

    set_list = set(to_notify_user_list)
    to_notify_user_list = list(set_list)

    by_notify_user = User.objects.get(id = initiator_id)
    to_notify_users = list(User.objects.filter(id__in=to_notify_user_list).values('id','fcm_token'))

    friends_registration_tokens = []
    nonFriends_registration_tokens = []

    tagger_name = by_notify_user.name
    tagger_id = initiator_id
    print("fcm... "+ str(to_notify_user_list) )
    #print(serializer.data)
    for to_notify_user in to_notify_users:
        to_notify_id = to_notify_user['id']

        is_friend = alreadyFriend(to_notify_id, initiator_id)
        try:
            if is_friend:
                if to_notify_user['fcm_token']:
                    friends_registration_tokens.extend(to_notify_user['fcm_token'])
            else:
                if to_notify_user['fcm_token']:
                    nonFriends_registration_tokens.extend(to_notify_user['fcm_token'])
        except Exception as ex:
            print(str(ex))

    if event_type == TASK_TYPE :
        task = Task.objects.get(id=event_id)
        title = task.title
        message_title= "Task Tag Alert"
        message_body = tagger_name + " " +  message_action + " " + title + " task"

    elif event_type == GROUP_TYPE :
        group = Group.objects.get(id=event_id)
        title = group.group_name
        message_title="Group Tag Alert"
        message_body = tagger_name + " "+ message_action + " " + title + " group"

    result = ""
    data = {}
    data['tagger_id']=tagger_id
    data['tagger_name'] = tagger_name
    data['event_type'] = event_type
    data['event_id'] = event_id

    if len(friends_registration_tokens) > 0:
        result = push_service.notify_multiple_devices(registration_ids=friends_registration_tokens, message_body = " YOUR FRIEND " + message_body, data_message=data)
    if len(nonFriends_registration_tokens)>0:
        result = push_service.notify_multiple_devices(registration_ids=nonFriends_registration_tokens, message_body = " NOT FRIEND  " + message_body, data_message=data)
    print("noti...." + str(result))


@api_view(['POST','GET'])
def task(request, user_id):

    if request.method == 'POST':
        try:
            date = request.POST.get('date')
            image = request.POST.get('image_id')
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
            group_tag_list = json.loads(group_tag)

            print("date...." + str(date))

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

            task = Task.objects.create(date=date,image=image,category=category,title=title,from_time=from_time,to_time=to_time,description = description,tagged=tagged,reminders=reminders, user_id=user_id,tag_flag=tag_flag,group_tag=group_tag_list)
            taskSerializer = TaskSerializer(task)
            response = {"success":True, "data":taskSerializer.data, "message":"new task added"}

            """post task to month view to update internally """

            t = threading.Thread(target=topTaskUpdateMonthView, args=(user_id,date))
            t.start()

            send_notification_list = []
            all_tag_people_list = []

            if group_tag_list:
                person_list = list(Group.objects.filter(id__in=group_tag_list).values_list('group_list',flat=True))
                flat_list = list(set(item for sublist in person_list for item in sublist))
                send_ntification_list = flat_list
                all_tag_people_list = flat_list

            if tagged:
                all_tag_people_list.extend(tagged)
                all_tag_people_list = list(set(all_tag_people_list))

            send_notification_list = all_tag_people_list

            if len(all_tag_people_list)>0:
                t1 = threading.Thread(target = personTag, args=(all_tag_people_list,user_id,task.id,date, TASK_TYPE))
                t1.start()

                d = datetime.datetime.strptime(date, "%Y-%m-%d").date()
                if d >= datetime.date.today():
                    t3 = threading.Thread(target=fcmNotification, args=(user_id, send_notification_list, TASK_TYPE , task.id , ADD_MESSAGE ))
                    t3.start()

            # group people get

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
                    groups = Group.objects.filter(id__in=data['group_tag'])
                    groups_serializer = GroupTagSerializer(groups,many=True)
                    #for group_id in data['group_tag']:
                        #group_info = {}
                        #group = Group.objects.get(id=group_id)
                        #group_info['name'] = group.group_name
                        #group_info['id'] = group.id
                        #group_list.append(group_info)

                    data['groups'] = groups_serializer.data

                if data['tagged'] :
                    friends = User.objects.filter(id__in=data['tagged'])
                    friends_serializer = ProfileSerializer(friends,many=True)
                    data['friends'] = friends_serializer.data

            response = {"success":True, "message":"all detailed tasks", "data":serializer.data}
            return Response (response, status= status.HTTP_200_OK)

        except Exception as ex:
            response = {"success":False,"message":"error occured", "data":[] }
            return Response (response, status=status.HTTP_400_NOT_FOUND)

def topTaskofDate(user_id,date):
    try:
        all_done_flag = False
        all_tasks_on_date = Task.objects.filter(user_id=user_id, date=date)
        all_done_tasks = all_tasks_on_date.filter(complete=True)
        total_count = all_tasks_on_date.count()
        done_count = all_done_tasks.count()

        if total_count > 0:
            if total_count == done_count:
                all_done_flag = True

        allTasks = Task.objects.filter(user_id=user_id, date=date, complete=False).order_by("from_time")
        taskCount = allTasks.count()
        tag_tasks = allTasks.filter(tag_flag=True)
        tag_flag = False
        if tag_tasks.count() > 0:
            tag_flag = True

        topThreeTasks = allTasks[:3]
        topTaskSerializer = TopTaskSerializer(topThreeTasks, many=True)

        result={}
        result['count'] = taskCount
        result['tasks'] = topTaskSerializer.data[:]
        result['tag_flag'] = tag_flag
        result['all_done'] = all_done_flag
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
                person_list = []
                if data['group_tag'] is not None:
                    groups = Group.objects.filter(id__in=data['group_tag'])
                    groups_serializer = GroupTagSerializer(groups,many=True)
                    #for group_id in data['group_tag']:
                        #group_info = {}
                        #group = Group.objects.get(id=group_id)
                        #group_info['name'] = group.group_name
                        #group_info['id'] = group.id
                        #group_list.append(group_info)

                    data['group'] = groups_serializer.data
                else:
                    data['group']=[]

                if data['tagged'] is not None:
                    tagged_users = User.objects.filter(id__in=data['tagged'])
                    tagged_serializer = ProfileSerializer(tagged_users,many=True)
                    person_list = tagged_serializer.data
                    data['tagged_persons'] = person_list

                else:
                    data['tagged_persons'] = []

                del data['group_tag']
                del data['tagged']

            response = {"success":True,"message":"all tasks of date","data":serializer.data}
            return Response(response,status=status.HTTP_200_OK)

        except Exception as ex:
            exc_type, exc_obj, exc_tb = sys.exc_info()
            fname = os.path.split(exc_tb.tb_frame.f_code.co_filename)[1]
            print(exc_type, fname, exc_tb.tb_lineno)
            print(str(ex))
            response = {"success":False,"message":"error occured", "data":[]}
            return Response(response, status=status.HTTP_400_BAD_REQUEST) 

@api_view(['PUT','DELETE','GET'])
def editTask(request, task_id):
    if request.method == 'DELETE':
        try:
            task = Task.objects.get(id=task_id)
            date = task.date
            user_id = task.user_id
            task_id = task.id
            task.delete()

            response = {"success":True,"message":"deleted"}

            tags_with_task = TagMe.objects.filter(event_type=TASK_TYPE,event_id=task_id)
            tags_with_task.delete()

            """ MonthView Update """
            t = threading.Thread(target=topTaskUpdateMonthView, args=(user_id,date))
            t.start()

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
        image = request.POST.get('image_id')
        description = request.POST.get('description')
        reminders = request.POST.get('reminders')
        reminders = json.loads(reminders)
        tagged = request.POST.get('tagged')
        print("tagged... "+ tagged)
        tagged = json.loads(tagged)
        print("tag... "+ str(tagged))
        tag_flag = request.POST.get('tag_flag')
        tag_flag = json.loads(tag_flag)
        group_tag = request.POST.get('group_tag')
        print("group tag... "+ group_tag)
        group_tag_list = json.loads(group_tag)

        if not from_time:
            from_time=None
        if not to_time:
            to_time=None
        if not description:
            description = None
        if len(reminders)==0:
            reminders = None
        if len(tagged)==0:
            tagged = None
        if not image:
            image = None
        if len(group_tag_list)==0:
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
            previous_tagged = task.tagged
            task.tagged = tagged
            task.tag_flag = tag_flag
            task.group_tag = group_tag_list
            previous_group_tag = group_tag_list
            task.image = image
            task.save()

            user_id = task.user_id

            serializer = TaskSerializer(task)
            response = {"success":True,"message":"updated successfully","data":[serializer.data]}

            """post task to month view to update internally """

            if not tagged:
                tagged=[]
            if not previous_tagged:
                previous_tagged = []
            if not group_tag_list:
                group_tag_list=[]
            if not previous_group_tag:
                previous_group_tag=[]

            #people_to_discard_list = list(set(previous_tagged) - set(tagged))
            #print("Group tag: " + str(tagged)+ "PreviousGroupTage: " + str(previous_tagged))
            people_to_add_list = list(set(tagged) - set(previous_tagged))

            #print("549.. "+str(people_to_add_list))
            #group_to_discard_list = list(set(previous_group_tag)-set(group_tag))
            #print("Group tag: " + str(type(group_tag))+ "PreviousGroupTage: " + str(type(previous_group_tag)))
            group_to_add_list =[]
            group_to_add_list = list(set(group_tag_list) - set(previous_group_tag))
            print("555 ... "+ str(group_to_add_list))

            tags_with_task = TagMe.objects.filter( event_type = TASK_TYPE , event_id=task_id)
            tags_with_task.delete()

            t = threading.Thread(target = topTaskUpdateMonthView, args=(user_id,date))
            t.start()

            add_notification_list = []
            remove_notification_list=[]
            add_tag_people_list = []
            remove_tag_people_list = []

            if len(group_tag)>0:
                try:
                    person_list = list(Group.objects.filter(id__in=group_tag_list).values_list('group_list',flat=True))
                    flat_list = list(set(item for sublist in person_list for item in sublist))
                    add_tag_people_list = flat_list
                except Exception as ex:
                    print(str(ex))

            if len(tagged)>0:
                add_tag_people_list.extend(tagged)

            if len(group_to_add_list)>0:
                print("len.." + str(group_to_add_list))
                person_list = list(Group.objects.filter(id__in=group_to_add_list).values_list('group_list',flat=True))
                flat_list = list(set(item for sublist in person_list for item in sublist))
                add_notification_list = flat_list

            if len(people_to_add_list)>0:
                add_notification_list.extend(people_to_add_list)

            add_tag_people_list = list(set(add_tag_people_list))
            add_notification_list = list(set(add_notification_list))

            if len(add_tag_people_list)>0:
                print(str(add_tag_people_list))
                t1 = threading.Thread(target=personTag, args=( add_tag_people_list, user_id, task.id, date, TASK_TYPE ))
                t1.start()

            if len(add_notification_list)>0:
                print(str(add_notification_list))
                t4 = threading.Thread(target=fcmNotification, args=(user_id, add_notification_list, TASK_TYPE , task.id, ADD_MESSAGE ))
                t4.start()

            print("monthview sAVE")
            return Response (response,status = status.HTTP_200_OK)
        except Exception as ex:
            exc_type, exc_obj, exc_tb = sys.exc_info()
            fname = os.path.split(exc_tb.tb_frame.f_code.co_filename)[1]
            print(exc_type, fname, exc_tb.tb_lineno)
            print(" edit task .. "+str(ex))
            response = {"success":False,"message":"couldn't update","data":[]}
            return Response (response,status=status.HTTP_400_BAD_REQUEST)

    if request.method == 'GET':
        try:
            task = Task.objects.get(id=task_id)
            serializer = TaskSerializer(task)
            group_list = []
            person_list = []
            if serializer['group_tag'] is not None:
                groups = Group.objects.filter(id__in=data['group_tag'])
                groups_serializer = GroupTagSerializer(groups,many=True)
                #for group_id in data['group_tag']:
                    #group_info = {}
                    #group = Group.objects.get(id=group_id)
                    #group_info['name'] = group.group_name
                    #group_info['id'] = group.id
                    #group_list.append(group_info)

                data['group'] = groups_serializer.data
            else:
                data['group']=[]

            if data['tagged'] is not None:
                tagged_users = User.objects.filter(id__in=data['tagged'])
                tagged_serializer = ProfileSerializer(tagged_users,many=True)
                person_list = tagged_serializer.data
                data['tagged_persons'] = person_list
            else:
                data['tagged_persons'] = []

            del data['tagged']
            del data['group_tag']
            response = {"success":True,"message":"task","data":[serializer.data]}
            return Response(response,status=status.HTTP_200_OK)
        except:
            response = {"success":False,"message":"couldn't get task","data":[]}
            return Response(response,status = status.HTTP_400_BAD_REQUEST)


@api_view(['POST'])
def search(request, user_id):

    if request.method == 'POST':
        text = request.POST.get('searchtext')
        try:
            tasks = Task.objects.filter(user_id=user_id, title__icontains=text).order_by("date","from_time")
            serializer = TaskSearchSerializer(tasks, many=True)

            response = {"data":serializer.data}
            return Response(response, status=status.HTTP_200_OK)
        except Exception as ex:
            print("Exception... "+ str(ex))
            response = {"data":[]}
            return Response (response, status=status.HTTP_400_BAD_REQUEST)

@api_view(['GET','PUT'])
def profile(request, user_id):

    if request.method=='PUT':
        user = User.objects.get(id=user_id)
        name=False
        phoneNumber=False
        #image=False
        password = False
        rm = request.POST.get('rm')
        rm = json.loads(rm)
        try:
            if rm:
                user.image=None
            if not rm:
                try:
                    user.image  = request.data['file']
            #user.image=image
                except Exception as ex:
                    print(str(ex))
        except Exception as ex:
            print("file + " + str(ex))
            #user.image=None
        try:
            name = request.POST.get('name')
            user.name=name
            print("name "+ name)
        except Exception as ex:
            print("name " + name)
            print(str(ex))
            user.name=None
        try:
            phoneNumber = request.POST.get('phoneNumber')
            print(phoneNumber)
        except Exception as ex:
            print(str(ex))
            pass
        try:
            password = request.POST.get('password')
        except Exception as ex:
            print(str(ex))
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
        user = User.objects.filter(id=user_id)
        if user:
            user = user[0]
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

@api_view(['POST'])
def findFriend(request, user_id):
    if request.method == 'POST':
        search_type = request.POST.get('type')
        search_type = json.loads(search_type)
        key = request.POST.get('value')
        user =False
        try:
            if search_type ==1:
                user = User.objects.filter(mail=key)
            elif search_type == 2:
                user = User.objects.filter(phoneNumber=key)
        except Exception as ex:
            print(str(ex))
        already_friend = False

        if user:
            user=user[0]
            profileSerializer = ProfileSerializer(user)

            already_friend =  alreadyFriend(user_id, user.id )

            response = {"already": already_friend, "success":True,"message":"user found","data":[profileSerializer.data]}
            return Response(response, status=status.HTTP_200_OK)
        #elif user_p:
            #user_p=user_p[0]
            #profileSerializer = ProfileSerializer(user_p)

            #already_friend = alreadyFriend(user_id,user_p.id)
            #response = {"already":already_friend,"success":True,"message":"user found","data":[profileSerializer.data]}
            #return Response(response, status=status.HTTP_200_OK)

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
                datas = serializer.data
                for data in datas:
                    is_friend = alreadyFriend(data['id'],user_id)
                    data['is_friend'] = is_friend
            
                #serializer = ProfileSerializer(friends,many=True)
                response = {"success":True,"data":datas,"message":"all friends"}
                return Response(response,status=status.HTTP_200_OK)
            except Exception as ex:
                print(str(ex))
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

                t = threading.Thread(target=topTaskUpdateMonthView, args=(user_id,date))
                t.start()

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
        
        try:
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
        except Exception as ex:
            print(str(ex))
            return Response({"success":False},status=status.HTTP_400_BAD_REQUEST)
@api_view(['POST'])
def syncTask(request,user_id):
    if request.method == 'POST':

        data = request.POST.get('data')
        data_list = json.loads(data)

        date_list = []
        bulk_tasks = []
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
                group_tag = None
                print("date .. "+str(date))
                try :
                    #task = Task.objects.create(user_id=user_id,date=date,title=title,from_time=from_time,to_time=to_time,image=image,category=category,description=description,complete=complete,tagged=tagged,tag_flag=tag_flag,reminders=reminders,group_tag=group_tag)
                    t = Task(user_id=user_id,date=date,title=title,from_time=from_time,to_time=to_time,image=image,category=category,description=description,complete=complete,tagged=tagged,tag_flag=tag_flag,reminders=reminders,group_tag=group_tag)
                    bulk_tasks.append(t)
                    date_list.append(date)
                    #t = threading.Thread(target=topTaskUpdateMonthView, args=(user_id,date))
                    #t.start()

                except Exception as exc:
                    print("eception.... "+str(exc))
                    pass
            Task.objects.bulk_create(bulk_tasks)

            """ MONTH VIEW UPDATE """
            for date in date_list:
                topTaskUpdateMonthView(user_id,date)

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
                    #city = base_object['location']['city']
                    city = city
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

        #if "_" in country:
            #country.replace("_"," ")

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

@api_view(['POST'])
def groupInvitation(request, invited_user, group_id):
    if request.method == 'POST':
        reply = request.POST.get('invitation')
        reply = json.loads(reply)
        invited_user = json.loads(invited_user)
        group_id = json.loads(group_id)
        if reply:
            data_row = GroupMap.objects.create(user_id=invited_user,group_id=group_id)
            #group = Group.objects.get(id=group_id)
            #serializer = GroupSerializer(group)
            response = {"success":True,"message":"added to the group","data":{}}
            return Response(response,status=status.HTTP_200_OK)

def groupMapAdd(user_id, group_id, person_list):
    group_map_list = []
    for person_id in person_list:
        is_friend = alreadyFriend(str(person_id), user_id)

        if is_friend:
            obj = GroupMap(user_id=person_id,group_id=group_id)
            group_map_list.append(obj)
            #GroupMap.objects.create(user_id=person_id, group_id=group_id)
    obj = GroupMap(user_id=user_id,group_id=group_id)
    group_map_list.append(obj)
    GroupMap.objects.bulk_create(group_map_list)

@api_view(['POST','GET'])
def group(request,user_id):
    if request.method == 'POST':
        group_name = request.POST.get('group_name')
        group_list = request.POST.get('group_list')
        print(str(type(group_list)))
        group_list = json.loads(group_list)
        print(str(group_list))

        try:
            group = Group.objects.create(user_id=user_id,group_name=group_name,group_list=group_list)
            serializer = GroupSerializer(group)

            print("before noti thread")
            # send notifications to everyone
            try:
                t1 = threading.Thread(target=fcmNotification, args=(user_id, group_list, GROUP_TYPE , group.id , ADD_MESSAGE ))
                t1.start()
            except Exception as ex:
                print(str(ex))

            to_write_list = group_list
            print("map add thread")
            #write to add group add people
            t2 = threading.Thread(target=groupMapAdd, args=(user_id,group.id,to_write_list))
            t2.start()
            print("after thread")

            date =datetime.date.today() + timedelta(days=1)
            t3 = threading.Thread(target = personTag, args=(group_list,user_id, group.id, date, GROUP_TYPE))
            t3.start()

            group_friends = User.objects.filter(id__in=group_list)
            group_friends_serializer = ProfileSerializer(group_friends, many=True)
            friends_dict = {}
            friends_dict['group_id'] = group.id
            friends_dict['group_friends'] = group_friends_serializer.data
            response = {"success":True,"message":"group created","group_data":serializer.data,"group_friends":friends_dict}
            print("before response")
            return Response (response,status=status.HTTP_201_CREATED)
        except Exception as exc:
            exc_type, exc_obj, exc_tb = sys.exc_info()
            fname = os.path.split(exc_tb.tb_frame.f_code.co_filename)[1]
            print(exc_type, fname, exc_tb.tb_lineno)
            print('exception... '+ str(exc))
            response = {"success":False, "message":"exception..","group_data":{},"group_friends":{[]}}
            return Response(response, status= status.HTTP_400_BAD_REQUEST)

    elif request.method == 'GET':
        try:
            group_ids = GroupMap.objects.filter(user_id=user_id).values_list('group_id',flat=True)
            group_ids = list(group_ids)
            groups = Group.objects.filter(id__in=group_ids)

            serializer = GroupSerializer(groups,many=True)
            for group in serializer.data:
                admin = User.objects.get(id=group['user_id'])
                s = ProfileSerializer(admin)
                group['admin'] = s.data
                group_friends = User.objects.filter(id__in=group['group_list'])
                group_friends_serializer = ProfileSerializer(group_friends, many=True)
                group['friends'] = group_friends_serializer.data
            response = {"success":True,"message":"groups","data":serializer.data}
            return Response (response,status=status.HTTP_200_OK)
        except Exception as ex:
            print("exception..." + str(ex))
            response = {"success": False , "message":"exception..."}
            return Response(response,status=status.HTTP_400_BAD_REQUEST)

def groupMapRemove(group_id, people_list):
    try:
        entry_with_group_id = GroupMap.objects.filter(group_id=group_id)
        entry_with_group_id.delete()
    except Exception as ex:
        print("map remove thread exception")

@api_view(['GET','PUT','DELETE'])
def singleGroup(request,user_id,group_id):
    if request.method == 'GET':
        try:
            group_ids = GroupMap.objects.filter(user_id=user_id).values_list('group_id',flat=True)
            group_ids = list(group_ids)

            if group_id in group_ids:
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
        print("delete")
        try:
            group = Group.objects.get(id=group_id)
            people_list = group.group_list
            admin_id = group.user_id
            print("before if")
            print("admin type.. "+ str(type(admin_id)))
            user_id_int = json.loads(user_id)
            if user_id_int == admin_id:
                    #then delete group and remove everyone from group
                group_name = group.group_name
                people_list = group.group_list
                group_id = group.id
                group.delete()

                t1 = threading.Thread( target = groupMapRemove , args=(group.id,people_list))
                t1.start()

                tags_with_group = TagMe.objects.filter(event_type= GROUP_TYPE , event_id=group_id)
                tags_with_group.delete()

                response = {"success":True,"message":group_name+" group deleted"}
                return Response (response, status=status.HTTP_200_OK)

                #else he has group but not owner.so leave from group
            if user_id_int in people_list:
                try:
                    group_name = group.group_name
                    groupMap_entry = GroupMap.objects.filter(user_id=user_id,group_id=group_id)
                    groupMap_entry.delete()
                    group.group_list.remove(user_id_int)
                    group.save()
                    tag_with_group = TagMe.objects.filter(tagged_id=user_id,event_type=GROUP_TYPE,event_id=group_id)
                    tag_with_group.delete()

                    response = {"success":True, "message": "Left Group " + group_name }
                    return Response(response,status=status.HTTP_200_OK)
                except Exception as ex:
                    print(str(ex))
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
            user_id_int = json.loads(user_id)
            if user_id_int==group.user_id:

                group.group_name = group_name
                previous_list = group.group_list
                group.group_list = group_list
                group.save()
 
                group_maps = GroupMap.objects.filter(group_id=group_id)
                group_maps.delete()
 
                if group_list:
                    if len(group_list)>0:
                        t2 = threading.Thread(target=groupMapAdd, args=(user_id,group.id,group_list))
                        t2.start()

                people_to_add_list = list(set(group_list) - set(previous_list))

                if len(people_to_add_list)>0:
                    t1 = threading.Thread(target=fcmNotification, args= (user_id, people_to_add_list, GROUP_TYPE , group.id, ADD_MESSAGE))
                    t1.start()

                date =datetime.date.today() + timedelta(days=1)
                t3 = threading.Thread(target = personTag, args=(people_to_add_list,user_id, group.id, date, GROUP_TYPE))
                t3.start()
                response = {"success":True,"message":"group updated"}
                return Response (response,status=status.HTTP_200_OK)
            else:
                response = {"success":False,"message":"only group owner can edit"}
                return Response(response,status=status.HTTP_200_OK)
        except Exception as ex:
            print("exception..." + str(ex))
            response = {"success":False,"message":"error ...."}
            return Response(response,status=status.HTTP_400_BAD_REQUEST)

import traceback

@api_view(['GET','DELETE'])
def tag(request,tagged_id):
    if request.method == 'GET':
        try:
            tags = TagMe.objects.filter(tagged_id=tagged_id, date__gte=datetime.date.today()).order_by('action','date')
            serializer = TagMeSerializer(tags,many=True)
            tag_hoichi_list = []
            for tag in serializer.data:
                tag_dict ={}
                tagger = User.objects.get(id=tag['tagger_id'])
                tagger_serializer = ProfileSerializer(tagger)
                tag_dict['tag_korche'] = [tagger_serializer.data]
                event_type = tag['event_type']
                if event_type==1:
                    task  = Task.objects.get(id=tag['event_id'])
                    task_tag_serializer = TaskTagSerializer(task)
                    tag_dict['task'] = task_tag_serializer.data
                    tag_dict['event_type'] = event_type

                if event_type==2:
                    group = Group.objects.get(id=tag['event_id'])
                    group_serializer = GroupTagSerializer(group)
                    tag_dict['group_info'] = group_serializer.data
                    tag_dict['event_type'] = event_type

                tag_dict['action'] = tag['action']
                is_friend = alreadyFriend(tagged_id, tag['tagger_id'])
                tag_dict['is_friend'] = is_friend
                tag_dict["id"] = tag['id']

                tag_hoichi_list.append(tag_dict)
            serializer.tag_hoichi = tag_hoichi_list

            diff_tasks = TagMe.objects.filter(tagger_id=tagged_id,event_type=TASK_TYPE, date__gte=datetime.date.today()).order_by('date')
            serializer_k = TagMeSerializer(diff_tasks,many=True)

            tag_korchi_list = []
            event_set = set()
            print("tag iterate before .data... ")
            print(str(serializer_k.data))
            for tag in serializer_k.data:
                try:
                    tag_dict = {}
                    event_type = tag['event_type']
                    event_id = tag['event_id']
                    print("is already...")
                    is_already_processed = (event_type,event_id) in event_set
                    if not is_already_processed:
                        if event_type==1:
                            print("type = 1")
                            task = Task.objects.get(id=event_id)
                            people_tag = task.tagged
                            group_tag = task.group_tag
 
                            if people_tag:
                                tagged_users = User.objects.filter(id__in=people_tag)
                                tagged_serializer = ProfileSerializer(tagged_users,many=True)
                                print("tag serializer..")
                                tag_dict['people_tag_korchi'] = tagged_serializer.data
 
                            print("group tag type " + str(type(group_tag)))
                            print(""+str(group_tag))
                            if group_tag:
                                groups = Group.objects.filter(id__in=group_tag)
                                groups_serializer = GroupTagSerializer(groups,many=True)
                                tag_dict['group_tag_korchi'] = groups_serializer.data
                            print("group serializer...")
                            task_tag_serializer = TaskTagSerializer(task)
                            tag_dict['task'] = task_tag_serializer.data
                            tag_korchi_list.append(tag_dict)
                            print("tag korchi append")
                            t = (event_type,event_id)
                            event_set.add(t)
                            print("set add")
                        #elif event_type == 2:
                            #group = Group.objects.get(id=event_id)
                            #group_serializer = GroupTagSerializer(group)
                            #tag_dict['group']=group_serializer.data
                            #tag_korchi_list.append(tag_dict)
                    else:
                        print("already processed . . ." )
                except Exception as ex:
                    print(str(ex))
            serializer_k.tag_korchi = tag_korchi_list

            response = {"success":True,"message":"tagged tasks","tag_hoichi":serializer.tag_hoichi,"tag_korchi":serializer_k.tag_korchi}
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

@api_view(['GET'])
def notification(request,user_id):
    if request.method == "GET":
        try:
            all_notifications = TagMe.objects.filter(tagged_id=user_id,date__gte=datetime.date.today()).order_by('action','date')[:15]
            serializer = TagMeSerializer(all_notifications,many=True)

            for data in serializer.data:
                tagger_id = data['tagger_id']
                tagger_user = User.objects.get(id = tagger_id)
                tagger_serializer  = ProfileSerializer(tagger_user)
                data['tagger'] = tagger_serializer.data
                event_type = data['event_type']
                if event_type == 1:
                    task = Task.objects.get(id=data['event_id'])
                    title = task.title
                elif event_type ==2:
                    group = Group.objects.get(id=data['event_id'])
                    title = group.group_name
                data['title'] = title
            response = {"success":True,"message":"notis","data":serializer.data}
            return Response(response,status=status.HTTP_200_OK)
        except Exception as ex:
            print(str(ex))
            response = {"success":False,"message":"errors .. . .","data":[]}
            return Response(response,status=status.HTTP_400_BAD_REQUEST)

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

@api_view(['PUT'])
def changePassword(request,user_id):
    if request.method == 'PUT':
        try:
            user = User.objects.get(id=user_id)
            password = user.password
            old_password = request.POST.get('old_password')
            new_password = request.POST.get('new_password') 
            if password == old_password:
                user.password = new_password
                user.save()
                response = {"success":True,"message":"changed successfully"}
                return Response(response,status=status.HTTP_200_OK)
            else:
                response = {"success":False,"message":"password didn't match"}
                return Response(response,status=status.HTTP_200_OK)
        except Exception as ex:
            print(str(ex))
            response={"success":False,"message":"couldn't update"}
            return Response(response,status=status.HTTP_400_BAD_REQUEST)

@api_view(['GET','PUT'])
def tokenOperation(request,user_id):
    if request.method == 'PUT':
        try:
            fcm_token = request.POST.get('fcm_token')
            active = request.POST.get('active')
            active = json.loads(active)

            user = User.objects.get(id=user_id)
            user.fcm_token = fcm_token
            user.active = active
            user.save()

            response = {"success":True,"message":"updated successfully"}
            return Response(response,status=status.HTTP_200_OK)
        except Exception as ex:
            print(str(ex))
            response = {"success":False,"message":"problem.."}
            return Response (response,status=status.HTTP_400_BAD_REQUEST)

    elif request.method == 'GET':
        try:
            user = User.objects.get(id=user_id)
            serializer = FcmTokenSerializer(user)
            response = {"success":True,"message":"token","data":serializer.data}
            return Response(response,status=status.HTTP_200_OK)

        except Exception as ex:
            print (str(ex))
            response = {"success":False,"message":"problem","data":{}}
            return Response (response,status=status.HTTP_400_BAD_REQUEST)

@api_view(['PUT'])
def tagAction(request,tagged_id,tag_id):
    if request.method == 'PUT':
        try:
            action = request.POST.get('action')
            tagRow = TagMe.objects.get(id=tag_id)
            tagRow.action = action
            tagRow.save()
            response = {"success":True,"message":"action updated"}
            return Response(response,status=status.HTTP_200_OK)
        except Exception as ex:
            print("tagAction error..  "+str(ex))
            response = {"success":False,"message":"error.. "}
            return Response(response,status=status.HTTP_400_BAD_REQUEST)

@api_view(['POST'])
def logout(request, user_id):
    if request.method == 'POST':
        try:
            token = request.POST.get('token')
            user = User.objects.get(id=user_id)
            token_list = user.fcm_token
            if token in token_list:
                token_list.remove(token)
                user.fcm_token = token_list
                user.save()

            response = {"success":True, "msssage":"logged out"}
            return  Response(response,status=status.HTTP_200_OK)
        except Exception as ex:
            print(str(ex))
            response = {"success":False,"message":"error"}
            return Response(response,status=status.HTTP_400_BAD_REQUEST)
