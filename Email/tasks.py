import logging
from awd_main.celery import app
from Data_entry.utils import send_email_notification
from Data_entry.models import CustomUser, UserSubscription, History
from django.core.exceptions import PermissionDenied
from django.conf import settings

logger = logging.getLogger(__name__)


#==================Email task =========================
@app.task(bind=True, autoretry_for=(Exception,), retry_kwargs={'max_retries': 3}, retry_backoff=True)
def send_email_task(self, user_id, mail_subject, msg, to_email, attachment, email_id, history_id):
    from django.utils import timezone

    user = CustomUser.objects.get(id=user_id)
    recipient_email = user.email if user.email else settings.DEFAULT_TO_EMAIL

    sub = UserSubscription.objects.select_related("plan").filter(user=user, is_active=True).first()
    if not sub or not sub.is_valid():
        History.objects.filter(id=history_id).update(
            status="failed",
            error_logs="Subscription expired or inactive",
            completed_at=timezone.now()
        )
        try:
            send_email_notification(
                f'Bulk Email Task Failed - {mail_subject}',
                f'<p>Hello {user.username},</p><p>Bulk email task "<strong>{mail_subject}</strong>" failed.</p><p><strong>Reason:</strong> Subscription expired or inactive.</p>',
                [recipient_email]
            )
        except Exception:
            pass
        raise PermissionDenied("Subscription expired")

    History.objects.filter(id=history_id).update(
        status="processing",
        started_at=timezone.now(),
        task_id=self.request.id,
    )

    try:
        send_email_notification(mail_subject, msg, to_email, attachment, email_id)

        History.objects.filter(id=history_id).update(
            status="success",
            data=f"Sent email '{mail_subject}' to {len(to_email)} recipient(s)",
            completed_at=timezone.now()
        )

        # Notify user of successful completion
        try:
            send_email_notification(
                f'Bulk Email Campaign Completed - {mail_subject}',
                f'<p>Hello {user.username},</p><p>Your bulk email campaign "<strong>{mail_subject}</strong>" has been sent successfully to {len(to_email)} recipient(s).</p>',
                [recipient_email]
            )
        except Exception as notify_err:
            print(f"[Bulk Email Notification Warning] {notify_err}")

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
            # Notify user of failure on final attempt
            try:
                send_email_notification(
                    f'Bulk Email Task Failed - {mail_subject}',
                    f'<p>Hello {user.username},</p><p>Bulk email task "<strong>{mail_subject}</strong>" failed after retries.</p><p><strong>Error:</strong> {str(e)}</p>',
                    [recipient_email]
                )
            except Exception as notify_err:
                print(f"[Bulk Email Failure Notification Error] {notify_err}")

        raise



