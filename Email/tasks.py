from awd_main.celery import app
from Data_entry.utils import send_email_notification
from Data_entry.models import History
from Data_entry.limit import enforce_email_limit, record_usage
from Data_entry.models import CustomUser
#==================Email task =========================

@app.task(bind=True)
def send_email_task(self, user_id, mail_subject, msg, to_email, attachment, email_id, history_id):


    user = CustomUser.objects.get(id=user_id)

    enforce_email_limit(user)

    try:
        send_email_notification(mail_subject, msg, to_email, attachment, email_id)

        History.objects.filter(id=history_id).update(
            status="success",
            action=f"Email campaign completed: {mail_subject}"
        )

        record_usage(user, "emails_sent")
        return 'Email sending task success'

    except Exception as e:
        History.objects.filter(id=history_id).update(
            status="failed",
            action=str(e)
        )
        raise
