from django.shortcuts import render , redirect
from . import models
from .utils import check_csv_error, get_all_models
from uploads.models import Upload
from django.conf import settings
from django.core.management import call_command
from django.contrib import messages
from .tasks import import_data_task , export_data_task

# Create your views here.

#======================it is a importing view named as home ==========================
def home(request):
    all_models = get_all_models()
    if request.method=="POST":
        file_path = request.FILES.get('file_name')
        model_name = request.POST.get('model_name')

        upload = Upload.objects.create(file=file_path , model_name=model_name)
        relative_path = str(upload.file.url)
        base_url = str(settings.BASE_DIR)

        complete_path = base_url+relative_path

        try:
            check_csv_error(complete_path , model_name)
        except Exception as e:
            messages.error(request , str(e))
            return redirect('home')

        import_data_task.delay(complete_path,model_name)

        messages.success(request , 'Your data is in processing , you will we notified')

        return redirect("home")
    context = {
        'models':all_models
    }
    return render(request , "home.html" , context) 


#=========================Exporting view ===========================

def export(request):
    if request.method=="POST":
        model_name  = request.POST.get('model_name')
        export_data_task.delay(model_name)
        messages.success(request , 'Your data is in processing , you will we notified')
        return redirect('export')
    else:
        all_models = get_all_models()
        context= {
            'models':all_models
        }
    return render(request , "export.html" , context)