from django.shortcuts import render , redirect
from django.http import HttpResponse
from Data_entry.tasks import celery_test_task
from .forms import RegistrationForm
from django.contrib import messages
from django.contrib.auth.forms import AuthenticationForm
from django.contrib import auth

#=================Test celery view============================
 
def celery_test(request):
    celery_test_task.delay()
    return HttpResponse('<h3>function</h3>')

#=============Landing page===========
def Base(request):
    return render(request , "base.html")

#=========================Registration view====================
def register(request):
    if request.method == "POST":
        form = RegistrationForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request , "Registration successful.")
            return redirect('register')
        else:
            return redirect('register')
    else:
        form = RegistrationForm()
        context ={
            'form':form,
        }
    return render(request , "register.html" , context)


#=========================Login view==========================

def login(request):
    if request.method=='POST':
        form = AuthenticationForm( request ,request.POST)
        if form.is_valid():
            username = form.cleaned_data['username']
            password = form.cleaned_data['password']

            user = auth.authenticate(username=username , password=password)

            if user is not None:
                auth.login(request , user)
                return redirect('base')
        else:
            messages.error(request , 'Invalid Credentials')
            return redirect('login')

    else:
        form = AuthenticationForm()
        context = {
            'form':form,
        }
    return render(request , "login.html" , context)


#=========================Logout view=======================

def logout(request):
    auth.logout(request)
    return redirect('login')