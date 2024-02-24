from django.shortcuts import render, redirect, HttpResponse
from django.http import HttpResponse
from .models import Room,Topic,Message
from .forms import RoomForm, UserForm
from django.db.models import Q
from django.contrib.auth.models import User
from django.contrib import messages
from django.contrib.auth import authenticate,login,logout
from django.contrib.auth.decorators import login_required
from django.contrib.auth.forms import UserCreationForm


# Create your views here.

# rooms=[
#     { 'id':1, 'name':'Lets learn python'},
#     { 'id':2, 'name':'Lets learn Django!'},
#     { 'id':3, 'name':'Lets learn Javascript'},
# ]

def home(request):  
    #basically this store q parameter value from url to q variable like python, java etc..
    q=request.GET.get('q') if request.GET.get('q')!=None else ''
    # or  q=request.GET.get('q',')
    rooms = Room.objects.filter(Q(topic__name__icontains=q)|
                                Q(name__icontains=q)|                                
                                Q(description__icontains=q)                                
                                ) # this line filters out topic from room model class and 
    #then heads to parent class i.e. Topic and takes its name and compares to q variable
    topics = Topic.objects.all()[0:5]
    room_count = rooms.count()
    room_messages =Message.objects.filter(Q(room__topic__name__icontains=q))
    context={'rooms':rooms,'topics':topics,'q':q, 'room_count':room_count,'room_messages':room_messages}
    return render(request, 'base/home.html' ,context)

def room(request,pk):
    # room=None
    # for i in rooms:
    #     if i['id']==int(pk):
    #         room=i
    room=Room.objects.get(id=pk)
    room_messages = room.message_set.all().order_by('-created' ) #room-stores the all rooms ,message_set-->here message is model and set is different ,basically storing all the messages into message variable
    participants =room.participants.all()
    # Here we are going to check if the request method is 'POST'
    if request.method == 'POST' and request.user.is_authenticated():
        # We're creating a new 'Message' in the database
        # with information provided by the user.
        message = Message.objects.create(
            user=request.user,  # The user who is sending the message
            room=room,  # The room or chat where the message is sent
            body=request.POST.get('body'),  # The actual message content from the form
        )
        room.participants.add(request.user)
        # After creating the message, we redirect the user
        # back to the same room where they posted the message.
        return redirect('room', pk=room.id)
    
    elif not request.user.is_authenticated:
        return redirect('login')
    context={'room':room,'room_messages':room_messages,'participants':participants}
    return render(request, 'base/room.html',context)

def userProfile(request,pk):
    user=User.objects.get(id=pk)
    rooms=user.room_set.all()#this is how we get access to the children of the specific object
    room_messages =user.message_set.all()
    topics=Topic.objects.all()
    context={'user':user,'rooms':rooms,'room_messages':room_messages,'topics':topics}
    return render(request, 'base/profile.html',context)

# Ensure that the user is logged in; if not, redirect to the login page.
@login_required(login_url='login')
def createRoom(request):
    form=RoomForm() # create a new room object from the request object and add it to the request object list of the room object manager instance 
       # Retrieve all existing topics from the database.
    topics= Topic.objects.all()
     # Check if the form is submitted using POST method.

    if request.method == 'POST':
        # Extract the topic name from the POST data.
            topic_name =request.POST.get('topic')
        # Get or create a Topic object with the given name.

            topic,created = Topic.objects.get_or_create(name=topic_name)
        # Create a new Room object with the provided data and save it to the database.

            Room.objects.create(
                host=request.user,
                topic=topic,
                name=request.POST.get('name'),
                description=request.POST.get('description'),


            )

      #  print(request.POST)    
        # form=RoomForm(request.POST) # create a new room object from the request data and return it as a Room object instance
        # if form.is_valid():
        #     room=form.save(commit=False)
        #     room.host=request.user
        #     form.save()
     
        # Redirect the user to the home page after successfully creating the room.

            return redirect('home')
        # Prepare the context with the form and list of topics for rendering the template.

    context={'form' : form ,'topics':topics} # context object for the request data and return it as a Room instance
    return render(request, 'base/room_form.html',context) # return a Room instance

@login_required(login_url='login')
def updateRoom(request, pk):
    room=Room.objects.get(id=pk)# Retrieve a specific room instance from the database
    form=RoomForm(instance=room)# gonna pre-populate the form data from the existing room
    topics= Topic.objects.all()

    #instance=room allows you to create a form pre-filled with data from the specified room instance.

    if request.user != room.host:
        return HttpResponse('You are not allowed to update this room instance!')

    if request.method == 'POST':
        topic_name =request.POST.get('topic')
        # Get or create a Topic object with the given name.

        topic,created = Topic.objects.get_or_create(name=topic_name)
        room.name=request.POST.get('name')
        room.topic=topic
        room.description=request.POST.get('description')
        room.save()

        # Create a new Room object with the provided data and save it to the database.

        # form=RoomForm(request.POST, instance=room)
        # if form.is_valid():
        #     form.save()
        return redirect('home')
        
    context={'form' : form,'topics':topics,'room':room} # context object for the request data and return it as a Room instance
    return render(request, 'base/room_form.html',context) 

@login_required(login_url='login')
def deleteRoom(request, pk):
    room=Room.objects.get(id=pk)# Retrieve a specific room instance from the database

    if request.user != room.host:
        return HttpResponse('You are not allowed to update this room instance!')

    if request.method == 'POST':
      room.delete()
      return redirect('home')

    return render(request, 'base/delete.html', {'obj': room})
    
def loginPage(request):
 page='login'
 if request.method == 'POST':
    username=request.POST.get('username').lower() #stores username that the user recently used on username
    password=request.POST.get('password')
 
    try:
        user=User.objects.get(username=username, password=password) #checks if username and password is already
    except:
        messages.error(request, "User doesn't exist.")

    user=authenticate(request , username=username, password=password)
    if user is not None:
        login(request,user)
        return redirect('home')
    else:
         messages.error(request, "Username or password doesnot exist")
 context={'page':page}
 return render(request, 'base/login_register.html',context)


def logoutUser(request):
    logout(request)
    return redirect('home')

def registerPage(request):
    form=UserCreationForm()
    if request.method == 'POST':# passes user data into backend
        form=UserCreationForm(request.POST) # throws into UserCreationForm
        if form.is_valid(): # checks form validity
            user=form.save(commit=False) # saves user data and store in user variable..Here commit=false doesn't saves the data immmediately to database and holds for furthuer modifications..
            user.username=user.username.lower() #saves username in lowercase
            user.save() # after lowercase modifications user is finally saved t database
            login(request,user)#logged the user in 
            return redirect('home') 
        else: 
            messages.error(request,'Error in creating user Try again later')
    return render(request, 'base/login_register.html',{'form':form })


@login_required(login_url='login')
def deleteMessage(request, pk):
    message=Message.objects.get(id=pk)# Retrieve a specific message instance from the database

    if request.user != message.user:
        return HttpResponse('You are not allowed to delete this message instance!')

    if request.method == 'POST':
      message.delete()
      return redirect('home')

    return render(request, 'base/delete.html', {'obj': message})
    
@login_required(login_url='login')
def updateUser(request):
    user=request.user
    form = UserForm(instance=user) # here instance = user gives user already filled data from the database

    if request.method == 'POST':
        form =UserForm(request.POST, instance=user)
        if form.is_valid():
            form.save()
            return redirect('user-profile',pk=user.id)
    return render(request , 'base/update-user.html',{'form': form})

def topicsPage(request):
    q=request.GET.get('q') if request.GET.get('q')!=None else ''

    topics = Topic.objects.filter(name__icontains=q)
    return render(request, 'base/topics.html',{'topics': topics})

def activityPage(request):
    room_messages = Message.objects.all()
    return render(request, 'base/activity.html',{'room_messages':room_messages})
