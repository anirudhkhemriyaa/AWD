from awd_main.celery import app
from django.core.management import call_command
from django.conf import settings
from .utils import send_email_notification
from Data_entry.utils import generate_csv_file
from Email.models import List
from django.core.exceptions import PermissionDenied
from .models import UserSubscription , CustomUser, UserSubscription, History
from .limit import  record_usage, enforce
from celery import shared_task


#========================== Importing task in background ==================

@app.task(bind=True, autoretry_for=(Exception,), retry_kwargs={'max_retries': 3}, retry_backoff=True)
def import_data_task(self, user_id, complete_path, model_name, history_id, list_id=None):
    from django.utils import timezone

    user = CustomUser.objects.get(id=user_id)

    sub = UserSubscription.objects.select_related("plan").get(user=user)

    if not sub.is_valid():
        raise PermissionDenied("Subscription expired")


    enforce(user, "import", sub.plan.import_limit_per_day)

    model_name = model_name.lower()

    try:
        email_list = None
        if model_name == "subscriber":
            if not list_id:
                raise ValueError("Subscriber list is required.")
            email_list = List.objects.get(id=list_id)

        call_command('import', complete_path, model_name, list_id=email_list.id if email_list else None , user_id=user.id)

        History.objects.filter(id=history_id).update(
            status="success",
            completed_at=timezone.now()
        )

        send_email_notification(
            'Data Import Completed',
            f'Data import for model {model_name} completed successfully.',
            [settings.DEFAULT_TO_EMAIL]
        )

        record_usage(user, "imports_done")

        return 'Data imported successfully'

    except Exception as e:
        if self.request.retries < self.max_retries:
            History.objects.filter(id=history_id).update(
                status="retrying",
                retry_count=self.request.retries + 1,
                error_logs=str(e)
            )
        else:
            History.objects.filter(id=history_id).update(
                status="failed",
                error_logs=str(e),
                completed_at=timezone.now()
            )

        send_email_notification(
            'Data Import Failed',
            f'Import failed for model {model_name}.\n\nError: {str(e)}',
            [settings.DEFAULT_TO_EMAIL]
        )
        raise



#========================== Exporting task in background ==================

@app.task(bind=True, autoretry_for=(Exception,), retry_kwargs={'max_retries': 3}, retry_backoff=True)
def export_data_task(self, user_id, model_name, history_id):
    from django.utils import timezone

    user = CustomUser.objects.get(id=user_id)


    sub = UserSubscription.objects.select_related("plan").get(user=user)

    if not sub.is_valid():
        raise PermissionDenied("Subscription expired")

    enforce(user, "export", sub.plan.export_limit_per_day)

    try:
        file_path = generate_csv_file(model_name)
        call_command("export", model_name, user_id=user.id ,  file_path=file_path)


        History.objects.filter(id=history_id).update(
            status="success",
            data=file_path,
            completed_at=timezone.now()
        )

        send_email_notification(
            'Data Export Completed',
            f'The data export for model {model_name} has been completed successfully.',
            [settings.DEFAULT_TO_EMAIL],
            attachment=file_path
        )

        record_usage(user, "exports_done")
        return 'Data exported successfully'

    except Exception as e:
        if self.request.retries < self.max_retries:
            History.objects.filter(id=history_id).update(
                status="retrying",
                retry_count=self.request.retries + 1,
                error_logs=str(e)
            )
        else:
            History.objects.filter(id=history_id).update(
                status="failed",
                error_logs=str(e),
                completed_at=timezone.now()
            )

        send_email_notification(
            'Data Export Failed',
            f'Export failed for model {model_name}.\n\nError: {str(e)}',
            [settings.DEFAULT_TO_EMAIL]
        )
        raise
