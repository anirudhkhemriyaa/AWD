from awd_main.celery import app
from Data_entry.utils import send_email_notification


@app.task
def send_email_task(mail_subject , msg , to_email , attachment):
    send_email_notification(mail_subject , msg , to_email , attachment)
    return 'Email sending task success'