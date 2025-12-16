from django.contrib import admin
from django.urls import path , include
from django.conf.urls.static import static
from django.conf import settings
from . import views


urlpatterns = [
    path('admin/', admin.site.urls),
    path('data_entry/' , include('Data_entry.urls')),
    path('Email/' , include('Email.urls')),
    path('celery-test/' ,views.celery_test),
    path('' ,views.Base , name="base"),
    path('register' ,views.register , name="register"),
    path('login' ,views.login , name="login"),
    path('logout' ,views.logout , name="logout"),
    
] + static(settings.MEDIA_URL , document_root = settings.MEDIA_ROOT)
