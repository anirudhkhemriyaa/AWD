from django.shortcuts import render , redirect
from django.http import HttpResponse
import time
from Data_entry.tasks import celery_test_task

 
def celery_test(request):
    celery_test_task.delay()
    return HttpResponse('<h3>function</h3>')