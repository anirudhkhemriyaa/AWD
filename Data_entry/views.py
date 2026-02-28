from django.shortcuts import render , redirect
from Email.models import List
from .utils import check_csv_error, get_all_models
from django.conf import settings
from django.contrib import messages
from .tasks import import_data_task , export_data_task
from django.contrib.auth.decorators import login_required
from .models import History, UserSubscription
from .limit import enforce
from django.core.exceptions import PermissionDenied
from uploads.models import Upload

# Create your views here.


@login_required(login_url="login")
def home(request):
    all_models = get_all_models()
    subscriber_lists = List.objects.all()

    if request.method == "POST":
        file_path = request.FILES.get("file_name")
        model_name = request.POST.get("model_name").lower()
        list_id = request.POST.get("subscriber_list")

        if model_name == "subscriber" and not list_id:
            messages.error(request, "You must select a subscriber list.")
            return redirect("home")

        upload = Upload.objects.create(
            file=file_path,
            model_name=model_name
        )

        relative_path = str(upload.file.url)
        complete_path = str(settings.BASE_DIR) + relative_path

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
            return redirect("home")

        user = request.user

        sub = UserSubscription.objects.filter(
            user=user,
            is_active=True
        ).select_related("plan").first()

        # No subscription at all
        if not sub:
            messages.error(request, "You don't have a subscription to use this tool.")
            return redirect("home")

        # Expired subscription
        if not sub.is_valid():
            messages.error(request, "Your subscription has expired.")
            return redirect("home")

        try:
            enforce(user, "import", sub.plan.import_limit_per_day)
        except PermissionDenied as e:
            messages.error(request, str(e))
            return redirect("home")

        history = History.objects.create(
            company=user,
            work="Import",
            data=file_path.name,
            status="processing",
        )
        
        import_data_task.delay(
            user.id,
            complete_path,
            model_name,
            history.id,
            list_id=list_id if model_name == "subscriber" else None,
        )

        messages.success(request, "Your data is in processing, you will be notified.")
        return redirect("home")

    return render(request, "home.html", {
        "models": all_models,
        "subscriber_lists": subscriber_lists
    })



#=========================Exporting view ===========================

@login_required(login_url="login")
def export(request):
    if request.method == "POST":
        model_name = request.POST.get("model_name")
        user = request.user

        sub = UserSubscription.objects.filter(
            user=user,
            is_active=True
        ).select_related("plan").first()

        # No subscription at all
        if not sub:
            messages.error(request, "You don't have a subscription to use this tool.")
            return redirect("export")

        # Expired subscription
        if not sub.is_valid():
            messages.error(request, "Your subscription has expired.")
            return redirect("export")

        try:
            enforce(user, "export", sub.plan.export_limit_per_day)
        except PermissionDenied as e:
            messages.error(request, str(e))
            return redirect("export")

        history = History.objects.create(
            company=user,
            work="Export",
            data=model_name,
            status="processing",

        )

        export_data_task.delay(user.id, model_name, history.id)

        messages.success(request, "Your data is in processing, you will be notified.")
        return redirect("export")

    all_models = get_all_models()
    return render(request, "export.html", {"models": all_models})
