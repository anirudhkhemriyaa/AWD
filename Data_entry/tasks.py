from awd_main.celery import app
from django.core.management import call_command
from django.conf import settings
from .utils import send_email_notification
from Data_entry.utils import generate_csv_file
from Data_entry.models import  History
from Email.models import List

#========================== Importing task in background ==================
@app.task(bind=True)
def import_data_task(self, complete_path, model_name, history_id, list_id=None):

    model_name = model_name.lower()
    try:
        email_list = None
        if model_name == "subscriber":
            if not list_id:
                raise ValueError("Subscriber list is required.")
            email_list = List.objects.get(id=list_id)

        call_command('import', complete_path, model_name, list_id=email_list.id if email_list else None)

        History.objects.filter(id=history_id).update(status="success")

        mail_subject = 'Data Import Completed'
        message = f'Data import for model {model_name} completed successfully.'
        send_email_notification(mail_subject, message, [settings.DEFAULT_TO_EMAIL])

        return 'Data imported successfully'

    except Exception as e:
        History.objects.filter(id=history_id).update(status="failed")

        mail_subject = 'Data Import Failed'
        message = f'Import failed for model {model_name}.\n\nError: {str(e)}'
        send_email_notification(mail_subject, message, [settings.DEFAULT_TO_EMAIL])

        raise



#========================== Exporting task in background ==================

@app.task(bind=True)
def export_data_task(self, model_name, history_id):
    from .models import History

    try:
        call_command('export', model_name)

        file_path = generate_csv_file(model_name)


        History.objects.filter(id=history_id).update(
            status="success",
            data=file_path
        )

        mail_subject = 'Data Export Completed'
        message = f'The data export for model {model_name} has been completed successfully.'
        to_email = settings.DEFAULT_TO_EMAIL
        send_email_notification(
            mail_subject,
            message,
            [to_email],
            attachment=file_path
        )

        return 'Data exported successfully'

    except Exception as e:
        History.objects.filter(id=history_id).update(
            status="failed",
            action=str(e)
        )

        mail_subject = 'Data Export Failed'
        message = f'Export failed for model {model_name}.\n\nError: {str(e)}'
        send_email_notification(mail_subject, message, [settings.DEFAULT_TO_EMAIL])

        raise
