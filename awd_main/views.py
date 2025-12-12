from django.shortcuts import render , redirect
from django.http import HttpResponse

def celery_test(request):
    return HttpResponse('<h3>function</h3>')