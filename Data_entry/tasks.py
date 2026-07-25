import logging
import os
from awd_main.celery import app
from django.core.management import call_command
from .utils import generate_csv_file, send_email_notification
from .models import CustomUser, UserSubscription, History
from Email.models import List
from django.core.exceptions import PermissionDenied
from django.conf import settings

logger = logging.getLogger(__name__)

# ========================== Importing task in background ==================

@app.task(bind=True, autoretry_for=(Exception,), retry_kwargs={'max_retries': 3}, retry_backoff=True)
def import_data_task(self, user_id, complete_path, model_name, history_id, list_id=None):
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
                f'Data Import Failed - {model_name}',
                f'<p>Hello {user.username},</p><p>Data import task for model <strong>{model_name}</strong> failed.</p><p><strong>Reason:</strong> Subscription expired or inactive.</p>',
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

    model_name = model_name.lower()

    try:
        email_list = None
        if model_name == "subscriber":
            if not list_id:
                raise ValueError("Subscriber list is required.")
            email_list = List.objects.get(id=list_id)

        call_command('import', complete_path, model_name, list_id=email_list.id if email_list else None, user_id=user.id)

        # 1. Send SUCCESS email to user.email
        send_email_notification(
            f'Data Import Completed - {model_name}',
            f'<p>Hello {user.username},</p><p>Data import for model <strong>{model_name}</strong> has been completed successfully.</p>',
            [recipient_email]
        )

        # 2. Update History status to success
        History.objects.filter(id=history_id).update(
            status="success",
            data=f"Imported {model_name} for {recipient_email}",
            completed_at=timezone.now()
        )

        return 'Data imported successfully'

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

            # Send FAILURE email on final retry
            try:
                send_email_notification(
                    f'Data Import Failed - {model_name}',
                    f'<p>Hello {user.username},</p><p>Data import for model <strong>{model_name}</strong> failed after all retries.</p><p><strong>Error:</strong> {str(e)}</p>',
                    [recipient_email]
                )
            except Exception as notify_err:
                print(f"[Import Failure Notification Error] {notify_err}")

        raise


# ========================== Exporting task in background ==================

@app.task(bind=True, autoretry_for=(Exception,), retry_kwargs={'max_retries': 3}, retry_backoff=True)
def export_data_task(self, user_id, model_name, history_id):
    import os
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
                f'Data Export Failed - {model_name}',
                f'<p>Hello {user.username},</p><p>Export task for model <strong>{model_name}</strong> failed.</p><p><strong>Reason:</strong> Subscription expired or inactive.</p>',
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

    file_path = None
    try:
        # 1. Generate export CSV file
        file_path = generate_csv_file(model_name)
        call_command("export", model_name, user_id=user.id, file_path=file_path)

        if not file_path or not os.path.exists(file_path) or os.path.getsize(file_path) == 0:
            raise FileNotFoundError(f"Export file for model '{model_name}' was not generated or is empty.")

        # 2. Send SUCCESS email with attachment directly to user.email
        subject = f"Data Export Completed - {model_name}"
        body = (
            f"<p>Hello {user.username},</p>"
            f"<p>Your requested data export for model <strong>{model_name}</strong> "
            f"has been generated successfully and is attached to this email.</p>"
        )

        send_email_notification(
            subject,
            body,
            [recipient_email],
            attachment=file_path
        )

        # 3. Update History status to success
        History.objects.filter(id=history_id).update(
            status="success",
            data=f"Exported {model_name} to {recipient_email}",
            completed_at=timezone.now()
        )

        # 4. Clean up temporary export file ONLY AFTER successful email delivery
        if os.path.exists(file_path):
            try:
                os.remove(file_path)
            except Exception as cleanup_err:
                print(f"[Export Cleanup Warning] Could not remove temp file {file_path}: {cleanup_err}")

        return f'Data exported successfully and sent to {recipient_email}'

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

            # Send FAILURE email on final retry
            try:
                send_email_notification(
                    f'Data Export Failed - {model_name}',
                    f'<p>Hello {user.username},</p><p>Export task for model <strong>{model_name}</strong> failed after retries.</p><p><strong>Error:</strong> {str(e)}</p>',
                    [recipient_email]
                )
            except Exception as notify_err:
                print(f"[Export Failure Notification Error] {notify_err}")

            # Clean up file on final failure if present
            if file_path and os.path.exists(file_path):
                try:
                    os.remove(file_path)
                except Exception:
                    pass

        raise
