from django.shortcuts import render
from . import models
# Create your views here.


def home(request):
    if request.method=="POST":
        file = request.POST.get('name')

    context = {
        'models':models
    }
    return render(request , "home.html")