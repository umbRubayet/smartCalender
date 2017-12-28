from django.shortcuts import render
from rest_framework.decorators import api_view
from rest_framework import status
#serializers-------
from .serializers import UserSerializer
from .serializers import MonthViewSerializer
from .serializers import TaskSerializer
from .serializers import ProfileSerializer
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

@api_view (['GET','POST'])
def user_list(request):
    """
    new user create on post method. i.e : signing up
    """
    if request.method == 'GET':
        pass

    elif request.method =='POST':
        serializer = UserSerializer(data=request.data)
        data_input = json.dumps(request.data)
        data_dict = json.loads(data_input)
        #print("type"+data_dict['mail'])
        mail = data_dict['mail']
        exists = User.objects.filter(mail=mail).exists()
        if exists:
            response = {"success":"false","data":"","message":"already exists"}
            return Response(response,status=status.HTTP_400_BAD_REQUEST)
        if serializer.is_valid():
            serializer.save()
            response = {"success":"true","data": serializer.data,"message":"new user created"}
            return Response(response,status=status.HTTP_201_CREATED)
        response = {"success":"false","data":"", "message":"bad request"}
        return Response(response , status=status.HTTP_400_BAD_REQUEST)


@api_view(['POST'])
def login(request):
    """
    login method
    """
    if request.method == 'POST':
        data_input = json.dumps(request.data)
        data_dict = json.loads(data_input)
        requested_mail = data_dict['mail']
        requested_password = data_dict['password']
        exists = User.objects.filter(mail = requested_mail).exists()
        print ("mail...."+ str(exists) )
        if exists :
            user = User.objects.get(mail=requested_mail)
            print ("requested-password..."+requested_password+ "user password.." + user.password)
            if requested_password ==  user.password :
                response = {"success":"true","id":user.id,"message":"logged in"}
                return Response(response,status=status.HTTP_200_OK)
            else:
                response = {"success":"false","message":"password didn't match"}
                return Response(response, status = status.HTTP_404_NOT_FOUND)

        else:
            response = {"success":"false","message":"user doesn't exist"}
            return Response(response, status=status.HTTP_404_NOT_FOUND)

@api_view(['POST'])
def month_tasks(request):
    """
    monthview task  count add with default value = 1
    """

    if request.method == 'POST':
        data_input = json.dumps(request.data)
        data_dict = json.loads(data_input)
        requested_user_id = data_dict['user_id']
        requested_date = data_dict['date']

        data_dict['tasks'] = data_dict['tasks'][0]
        exists = MonthView.objects.filter(user_id = requested_user_id, date = requested_date).exists()

        if exists :
            """ Update tasks """
            monthView = MonthView.objects.get(user_id=requested_user_id, date = requested_date)
            task_list =[]

            tasks = monthView.tasks
            if monthView.task_count > 2 :
                min_id = monthView.tasks[0]['task_id']

                for i in tasks :
                    if min_id > i['task_id'] :
                        min_id = i['task_id']


                for i in tasks:
                    if i['task_id'] > min_id :
                        task_list.append(i)
            else:
                for i in tasks:
                    task_list.append(i)

            task_list.append(data_dict['tasks'])
            monthView.tasks = task_list
            monthView.task_count = monthView.task_count + 1
            monthView.save()
            response = {"success":"true","task_count":monthView.task_count}
            return Response(response , status = status.HTTP_200_OK)
        else:
            """ create new task """
            serializer = MonthViewSerializer(data = request.data)
            if serializer.is_valid():
                serializer.save()
                response = {"success":"true","data": serializer.data,"message":"new month view task saved"}
                return Response(response,status = status.HTTP_201_CREATED)
            response = {"success":"false","data": serializer.data,"message":""}
            return Response(response, data = serializer.data , status = status.HTTP_400_BAD_REQUEST)

"""
@api_view(['POST','GET'])
def tasks(request):
     create new task 

    if request.method == 'POST':
        data_input = json.dumps(request.data)
        data_dict = json.loads(data_input)
        user_id = data_dict['user_id']
        date = data_dict['date']
        task_id = data_dict['task_id']
        task_title = data_dict['task_title']

        task_dict = {}
        task_dict['task_id'] = task_id
        task_dict['task_title'] = task_title

        json_data = {}
        json_data['user_id'] = user_id
        json_data['date'] = date
        json_data['tasks'] = [task_dict]

        response = requests.post('http://127.0.0.1:8000/month_tasks/',json = json_data)
        #print("status Code.....  " + int(response.status_code) )

        if response.status_code == 201 :
            response = {"success":"true","message":"month view data created"}
            return Response (response, status = status.HTTP_201_CREATED)
        if response.status_code == 200 :
            return Response ({"success":"edit","message":"updated task count"}, status = status.HTTP_200_OK)
        return Response(status = status.HTTP_400_BAD_REQUEST)
"""


@api_view (['GET','POST'])
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
            response = {"success":"true", "message":"user doesn't have any task yet", "data":"" }
            return Response (response , status = status.HTTP_200_OK)

        return Response (status = status.HTTP_400_BAD_REQUEST)


@api_view(['POST','GET'])
def postTask(request, user_id):

    if request.method == 'POST':
    #    try:
     #       serializer = TaskSerializer(data=request.data)
      #  except Exception as excep:
       #     response = {"success":False, "message": excep}
        #    return Response(response, status= status.HTTP_400_BAD_REQUEST)"""

        date = request.POST.get('date')
        image = request.data['file']
        category = request.POST.get('category')
        title = request.POST.get('title')
        from_time = request.POST.get('from_time')
        to_time = request.POST.get('to_time')
        description = request.POST.get('description')
        reminders = request.POST.get('reminders')
        print("dateeeeeeeeeee    "+str(type(date))) 

        if not from_time:
            from_time=None
        if not to_time:
            to_time=None
        if not description:
            description = None
        if not reminders:
            reminders = None
        try:
            task = Task.objects.create(date=date,image=image,category=category,title=title,from_time=from_time,to_time=to_time,description = description,reminders=reminders, user_id=user_id)
            taskSerializer = TaskSerializer(task)
            response = {"success":True, "data":taskSerializer.data, "message":"new task added"}

            """post task to month view to update internally """
            task_dict = {}
            task_dict['task_id'] = taskSerializer.data['id']
            task_dict['task_title'] = title
            
            if from_time:
                task_dict['time'] = from_time
            
            json_data = {}
            json_data['user_id'] = user_id
            
            json_data['date'] = date
            json_data['tasks'] = [task_dict]

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


@api_view(['GET','POST'])
def getTasksfromDate(request,user_id):
    if request.method == 'POST':
        data_input = json.dumps(request.data)
        data_dict = json.loads(data_input)
        date = data_dict['date']
        try:
            allTasks = Task.objects.filter(user_id=user_id,date=date)
            serializer = TaskSerializer(allTasks, many=True)
            response = {"data":serializer.data}
            return Response(response,status=status.HTTP_200_OK)
        except:
            pass

@api_view(['PUT','DELETE'])
def editTask(request, task_id):
    if request.method == 'DELETE':
        try:
            task = Task.objects.get(id=task_id)
            date = task.date
            task.delete()
            response = {"success":True,"message":"deleted"}
            return Response (response, status=status.HTTP_204_NO_CONTENT)
        except:
            response = {"success":False, "message":"error"}
            return Response (response, status=status.HTTP_404_NOT_FOUND)

@api_view(['GET'])
def search(request, user_id , text):

    if request.method == 'GET':
        tasksWithText = Task.objects.filter(user_id=user_id, title__contains=text)
        taskList=[]
        for task in tasksWithText:
            task_dict={}
            task_dict['task_id']=task.id
            task_dict['task_title'] = task.title
            taskList.append(task_dict)

        response = {"data":taskList}
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

@api_view(['GET'])
def findFriend(request, key):
    if request.method == 'GET':
        exists_mail = User.objects.filter(mail=key).exists()
        exists_phone = User.objects.filter(phoneNumber=key).exists()
        
        if exists_mail:
            user = User.objects.filter(mail=key)
            profileSerializer = ProfileSerializer(user, many=True)
            response = {"success":True,"message":"user found","data":profileSerializer.data}
            return Response(response, status=status.HTTP_200_OK)
        elif exists_phone:
            user = User.objects.filter(phoneNumber=key)
            profileSerializer = ProfileSerializer(user, many=True)
            response = {"success":True,"message":"user found","data":profileSerializer.data}
            return Response(response, status=status.HTTP_200_OK)
        
        else:
            response = {"success":False,"message":"user not found","data":""}
            return Response(response, status=status.HTTP_404_NOT_FOUND)

@api_view(['GET','POST'])
def addFriend(request, user_id):
    if request.method == 'POST':
        friend_id = request.POST.get('friend_id')
        
        exists = FriendList.objects.filter(user_id=user_id).exists()
        
        try:
            if exists:
                user = FriendList.objects.get(user_id=user_id)
                friend_list = user.friend_list['friend_id']
                # if this userid is already added then no need to add.
                if not friend_id in friend_list:
                    friend_list.append(friend_id)
                    user.friend_list['friend_id'] = friend_list
                    user.save()
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
