from django.shortcuts import render , redirect
from .forms import RegistrationForm
from django.contrib import messages
from django.contrib.auth.forms import AuthenticationForm
from django.contrib import auth
from Data_entry.models import CustomUser



#============= Landing page ===========

def Base(request):
    return render(request , "base.html")

#========================= Registration view ====================

def register(request):
    if request.method == "POST":
        form = RegistrationForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request , "Registration successful.")
            return redirect('profile')
        else:
            messages.error(request , "Registration failed. Invalid information.")
            return redirect('register')
    else:
        form = RegistrationForm()
        context ={
            'form':form,
        }
    return render(request , "register.html" , context)


#========================= Login view ==========================

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


#========================= Logout view =======================

def logout(request):
    auth.logout(request)
    return redirect('login')


#========================= Profile view =======================
def profile(request):
    user = CustomUser.objects.get(username=request.user.username)
    histories = request.user.histories.order_by('-created_at')[:20]
    context={
        'profile':user,
        "histories": histories,
    }
    return render(request , "profile.html" , context)

