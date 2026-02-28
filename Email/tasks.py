from awd_main.celery import app
from Data_entry.utils import send_email_notification
from Data_entry.models import CustomUser , UserSubscription , History
from Data_entry.limit import enforce , record_usage
from django.core.exceptions import PermissionDenied

#==================Email task =========================
@app.task(bind=True)
def send_email_task(self, user_id, mail_subject, msg, to_email, attachment, email_id, history_id):

    user = CustomUser.objects.get(id=user_id)

    # mark real start time
    History.objects.filter(id=history_id).update(
        status="processing",
    )

    sub = UserSubscription.objects.select_related("plan").get(user=user)

    if not sub.is_valid():
        History.objects.filter(id=history_id).update(
            status="failed",
        )
        raise PermissionDenied("Subscription expired")

    enforce(user, "email", sub.plan.email_limit_per_day)

    try:
        send_email_notification(mail_subject, msg, to_email, attachment, email_id)

        History.objects.filter(id=history_id).update(
            status="success",
        )

        record_usage(user, "emails_sent")
        return "Email sending task success"

    except Exception as e:
        History.objects.filter(id=history_id).update(
            status="failed",
        )
        raise

