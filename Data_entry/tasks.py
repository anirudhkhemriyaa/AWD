from awd_main.celery import app
import time
from django.core.management import call_command
from django.contrib import messages
from django.core.mail import EmailMessage
from django.conf import settings



@app.task
def celery_test_task():
    time.sleep(5)
    # Send an email
    mail_subject = 'Celery Task Completed'
    message = 'The Celery task has been executed successfully.' 
    from_email = settings.DEFAULT_FROM_EMAIL
    to_email = settings.DEFAULT_TO_EMAIL
    mail = EmailMessage(mail_subject , message , from_email , to=[to_email])
    mail.send()
    return "Email Send =>> "



@app.task
def import_data_task(complete_path , model_name):
    try:
        call_command('import',complete_path , model_name)
    except Exception as e:
        raise e
    
    return 'Data imported successfully'