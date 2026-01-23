from django.shortcuts import render , redirect
from Email.models import List
from .utils import check_csv_error, get_all_models
from uploads.models import Upload
from django.conf import settings
from django.contrib import messages
from .tasks import import_data_task , export_data_task
from django.contrib.auth.decorators import login_required
from .models import History

# Create your views here.

#======================it is a importing view named as home ==========================
@login_required(login_url="login")
def home(request):
    all_models = get_all_models()
    subscriber_lists = List.objects.all()

    if request.method == "POST":
        file_path = request.FILES.get('file_name')
        model_name = request.POST.get('model_name').lower()
        list_id = request.POST.get('subscriber_list') 

        if model_name == "subscriber" and not list_id:
            messages.error(request, "You must select a subscriber list.")
            return redirect("home")

        upload = Upload.objects.create(
            file=file_path,
            model_name=model_name
        )

        relative_path = str(upload.file.url)
        base_url = str(settings.BASE_DIR)
        complete_path = base_url + relative_path

        try:
            check_csv_error(complete_path, model_name)
        except Exception as e:
            History.objects.create(
                company=request.user,
                work="Import",
                data=file_path.name,
                status="failed"
            )
            messages.error(request, str(e))
            return redirect('home')

        history = History.objects.create(
            company=request.user,
            work="Import",
            data=file_path.name,
            status="processing"
        )

        # PASS LIST ID TO CELERY
        import_data_task.delay(
            complete_path,
            model_name,
            history.id,
            list_id
        )

        messages.success(request, 'Your data is in processing, you will be notified')
        return redirect("home")

    return render(request, "home.html", {
        "models": all_models,
        "subscriber_lists": subscriber_lists
    })




#=========================Exporting view ===========================
@login_required(login_url="login")
def export(request):
    if request.method == "POST":
        model_name = request.POST.get('model_name')

        history = History.objects.create(
            company=request.user,
            work="Export",
            data=model_name,
            status="processing"
        )

        export_data_task.delay(model_name, history.id)

        messages.success(request, 'Your data is in processing, you will be notified')
        return redirect('export')

    all_models = get_all_models()
    return render(request, "export.html", {"models": all_models})
