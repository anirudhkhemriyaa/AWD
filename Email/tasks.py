from awd_main.celery import app
from Data_entry.utils import send_email_notification


#==================Email task =========================

@app.task(bind=True)
def send_email_task(self, mail_subject, msg, to_email, attachment, email_id, history_id):
    from .models import History

    try:
        send_email_notification(mail_subject, msg, to_email, attachment, email_id)

        History.objects.filter(id=history_id).update(
            status="success",
            action=f"Email campaign completed: {mail_subject}"
        )

        return 'Email sending task success'

    except Exception as e:
        History.objects.filter(id=history_id).update(
            status="failed",
            action=str(e)
        )
        raise
