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
#serializers--------


#models---------
from .models import User
from .models import Info
from .models import MonthView
from .models import Task
from .models import FriendList
#models---------

from rest_framework.response import Response
import json
import requests
import dateutil.parser
from collections import defaultdict

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
            monthViewAllTasks = MonthView.objects.filter(user_id = user_id)
            serializer = MonthViewSerializer(monthViewAllTasks, many=True)
            response = {"success":"true", "data":serializer.data, "message":"all tasks"}
            return Response(response, status = status.HTTP_200_OK)
        else :
            response = {"success":"true","data":"", "message":"user doesn't have any task yet" }
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
        try:
            task = Task.objects.create(date=date,image=image,category=category,title=title,from_time=from_time,to_time=to_time,description = description,tagged=tagged,reminders=reminders, user_id=user_id,tag_flag=tag_flag)
            taskSerializer = TaskSerializer(task)
            response = {"success":True, "data":taskSerializer.data, "message":"new task added"}

            """post task to month view to update internally """

            topTasks_dict = topTaskofDate(user_id,date)

            monthView_user = MonthView.objects.get_or_create(user_id=user_id,date=date)
            monthView_user[0].task_count = topTasks_dict['count']
            monthView_user[0].tasks = topTasks_dict['tasks']
            monthView_user[0].tag_flag = topTasks_dict['tag_flag']
            monthView_user[0].save()

            return Response(response, status = status.HTTP_201_CREATED)

        except Exception as excep:
            response = {"success":False,"message":excep}
            return Response(response, status=status.HTTP_400_BAD_REQUEST)

    elif request.method == 'GET':
        try:
            allTasks = Task.objects.filter(user_id=user_id)
            serializer = TaskSerializer(allTasks, many=True)
            response = {"success":True, "message":"all detailed tasks", "data":serializer.data}
            return Response (response, status= status.HTTP_200_OK)
        except Exception as ex:
            response = {"success":False,"message":"error occured", "data":"" }
            return Response (response, status=status.HTTP_404_NOT_FOUND)

        response = {"success":False, "message":"others error", "data":""}
        return Response(response, status=status.HTTP_400_BAD_REQUEST)

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
            response = {"data":serializer.data}
            return Response(response,status=status.HTTP_200_OK)
        except:
            response = {"message":"error occured", "data":[]}
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
            return Response (response, status=status.HTTP_204_NO_CONTENT)
        except:
            response = {"success":False, "message":"error"}
            return Response (response, status=status.HTTP_404_NOT_FOUND)

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
            task.save()
            
            serializer = TaskSerializer(task)
            response = {"success":True,"message":"updated successfully","data":[serializer.data]}
            
            """post task to month view to update internally """

            topTasks_dict = topTaskofDate(user_id,date)

            monthView_user = MonthView.objects.get_or_create(user_id=user_id,date=date)
            monthView_user[0].task_count = topTasks_dict['count']
            monthView_user[0].tasks = topTasks_dict['tasks']
            monthView_user[0].tag_flag = topTasks_dict['tag_flag']
            monthView_user[0].save()

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
        tasks = Task.objects.filter(user_id=user_id, title__contains=text).order_by("from_time")
        serializer = TaskSearchSerializer(tasks, many=True)

        response = {"data":serializer.data}
        return Response(response, status=status.HTTP_200_OK)

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
            return Response(response,status=status.HTTP_202_ACCEPTED)

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
            response = {"success":True, "message":"user not found","data":""}
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
        exists = Task.objects.filter(user_id=user_id,id=task_id)
        
        #complition = json.loads(complition)
        if exists:
            try:
                task = Task.objects.get(user_id=user_id,id=task_id)
                task.complete = complition
                task.save()

                response = {"success":True, "message":"updated"}
                return Response(response, status = status.HTTP_200_OK)
            except:
                response = {"success":False, "message":"error"}
                return Response (response, status = status.HTTP_400_BAD_REQUEST)
        else:
            response = {"success":True,"message":"task doesn't exist"} 
            return Response (response,status = status.HTTP_200_OK)
