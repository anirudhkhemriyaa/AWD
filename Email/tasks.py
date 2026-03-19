from awd_main.celery import app
from Data_entry.utils import send_email_notification
from Data_entry.models import CustomUser , UserSubscription , History
from Data_entry.limit import enforce , record_usage
from django.core.exceptions import PermissionDenied

#==================Email task =========================
@app.task(bind=True, autoretry_for=(Exception,), retry_kwargs={'max_retries': 3}, retry_backoff=True)
def send_email_task(self, user_id, mail_subject, msg, to_email, attachment, email_id, history_id):
    from django.utils import timezone

    user = CustomUser.objects.get(id=user_id)

    History.objects.filter(id=history_id).update(
        status="processing",
        task_id=self.request.id,
    )

    sub = UserSubscription.objects.select_related("plan").get(user=user)

    if not sub.is_valid():
        History.objects.filter(id=history_id).update(
            status="failed",
            error_logs="Subscription expired",
            completed_at=timezone.now()
        )
        raise PermissionDenied("Subscription expired")

    enforce(user, "email", sub.plan.email_limit_per_day)

    try:
        send_email_notification(mail_subject, msg, to_email, attachment, email_id)

        History.objects.filter(id=history_id).update(
            status="success",
            completed_at=timezone.now()
        )

        record_usage(user, "emails_sent")
        return "Email sending task success"

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
        raise

