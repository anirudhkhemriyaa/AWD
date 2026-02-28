from django.urls import path

from . import views


urlpatterns = [
    path('import-data' , views.home , name="home"),
    path('export-data' , views.export , name="export"),
] 