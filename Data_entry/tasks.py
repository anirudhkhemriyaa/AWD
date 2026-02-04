from awd_main.celery import app
from django.core.management import call_command
from django.conf import settings
from .utils import send_email_notification
from Data_entry.utils import generate_csv_file
from Data_entry.models import  History
from Email.models import List
from django.utils import timezone
from django.core.exceptions import PermissionDenied
from redis import Redis
from .models import UserSubscription , CustomUser
from .limit import enforce_export_limit,enforce_import_limit, record_usage


#========================== Importing task in background ==================
@app.task(bind=True)
def import_data_task(self, user_id, complete_path, model_name, history_id, list_id=None):

    user = CustomUser.objects.get(id=user_id)

    enforce_import_limit(user)

    model_name = model_name.lower()

    try:
        email_list = None
        if model_name == "subscriber":
            if not list_id:
                raise ValueError("Subscriber list is required.")
            email_list = List.objects.get(id=list_id)

        call_command('import', complete_path, model_name, list_id=email_list.id if email_list else None)

        History.objects.filter(id=history_id).update(status="success")

        send_email_notification(
            'Data Import Completed',
            f'Data import for model {model_name} completed successfully.',
            [settings.DEFAULT_TO_EMAIL]
        )
        record_usage(user, "imports_done")

        return 'Data imported successfully'

    except Exception as e:
        History.objects.filter(id=history_id).update(status="failed")

        send_email_notification(
            'Data Import Failed',
            f'Import failed for model {model_name}.\n\nError: {str(e)}',
            [settings.DEFAULT_TO_EMAIL]
        )

        raise



#========================== Exporting task in background ==================
@app.task(bind=True)
def export_data_task(self, user_id, model_name, history_id):


    user = CustomUser.objects.get(id=user_id)

    enforce_export_limit(user) 

    try:
        call_command('export', model_name)

        file_path = generate_csv_file(model_name)

        History.objects.filter(id=history_id).update(
            status="success",
            data=file_path
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
        History.objects.filter(id=history_id).update(
            status="failed",
            action=str(e)
        )

        send_email_notification(
            'Data Export Failed',
            f'Export failed for model {model_name}.\n\nError: {str(e)}',
            [settings.DEFAULT_TO_EMAIL]
        )
        raise
