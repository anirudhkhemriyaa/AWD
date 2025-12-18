from awd_main.celery import app
import time
from django.core.management import call_command
from django.contrib import messages
from django.core.mail import EmailMessage
from django.conf import settings
from .utils import send_email_notification
from Data_entry.utils import generate_csv_file



#============================test task ===========================
@app.task
def celery_test_task():
    time.sleep(5)
    # Send an email
    mail_subject = 'Celery Task Completed'
    message = 'The Celery task has been executed successfully.' 
    to_email = settings.DEFAULT_TO_EMAIL
    send_email_notification(mail_subject , message , to_email)
    return f"Email Send =>> {{to_mail}} "



#==========================importing task in background==================

@app.task
def import_data_task(complete_path , model_name):
    try:
        call_command('import',complete_path , model_name)
    except Exception as e:
        raise e
    mail_subject = 'Data Import Completed'
    message = f'The data import for model {model_name} has been completed successfully.'
    to_email = settings.DEFAULT_TO_EMAIL
    send_email_notification(mail_subject , message , [to_email])
    
    return 'Data imported successfully'

#==========================Exporting task in background==================

@app.task
def export_data_task(model_name):
    try:
        call_command('export' , model_name)
    except Exception as e:
        raise e
    file_path = generate_csv_file(model_name)
    mail_subject = 'Data Export Completed'
    message = f'The data export for model {model_name} has been completed successfully.'
    to_email = settings.DEFAULT_TO_EMAIL
    send_email_notification(mail_subject , message , [to_email] , attachment=file_path)
    return 'Data exported successfully'