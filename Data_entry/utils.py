import logging
import csv
import datetime
import hashlib
import os
import time
from urllib.parse import quote
from bs4 import BeautifulSoup

from django.apps import apps
from django.conf import settings
from django.core.mail import EmailMessage
from django.core.management.base import CommandError
from django.db import DataError
from Email.models import Email, EmailTracking, Sent, Subscriber

logger = logging.getLogger(__name__)

#=======================Fetching all models in our project===========================

def get_all_models():
    excluded = {
        'List', 'Email', 'Sent', 'EmailTracking', 'Upload', 'ContentType',
        'Session', 'LogEntry', 'Group', 'Permission', 'User', 'History',
        'CustomUser', 'DailyUsage', 'SubscriptionPlan', 'UserSubscription'
    }
    custom_models = []
    for model in apps.get_models():
        if model.__name__ not in excluded:
            custom_models.append(model.__name__)
    return sorted(custom_models)


#======Checking Header error while importing the data whether field is correct or not=====

def check_csv_error(file_path, model_name):
    model = None
    target_name = model_name.lower()

    for app_config in apps.get_app_configs():
        for m in app_config.get_models():
            if m.__name__.lower() == target_name:
                model = m
                break
        if model:
            break

    if not model:
        raise CommandError(f"Model '{model_name}' not found.")

    # Fields that MUST come from CSV
    REQUIRED_FROM_CSV = {
        "subscriber": {"email_address"},
    }

    model_fields = {
        field.name for field in model._meta.fields
        if field.name not in ("id", "user", "email_list", "created_at", "updated_at")
    }

    with open(file_path, "r", encoding="utf-8-sig", errors="ignore") as file:
        reader = csv.DictReader(file)
        if not reader.fieldnames:
            raise DataError("CSV file is empty or missing headers.")
        csv_fields = set(reader.fieldnames)

    required = REQUIRED_FROM_CSV.get(target_name, model_fields)

    if not required.issubset(csv_fields):
        missing = required - csv_fields
        raise DataError(
            f"CSV must contain required columns: {', '.join(missing)}"
        )

    return model


#=================================Sending Email====================================

def send_email_notification(mail_subject, message, to_email, attachment=None, email_id=None):
    from_email = settings.DEFAULT_FROM_EMAIL

    email_obj = None
    if email_id:
        try:
            email_obj = Email.objects.select_related('email_list').get(pk=email_id)
        except Email.DoesNotExist:
            email_obj = None

    base_url = getattr(settings, "BASE_URL", "http://localhost:8000")

    for recipient in to_email:
        new_message = message

        if email_obj:
            subscriber = Subscriber.objects.filter(
                email_list=email_obj.email_list,
                email_address=recipient
            ).first()

            timestamp = str(time.time())
            data_to_hash = f"{recipient}{timestamp}"
            unique_id = hashlib.sha256(data_to_hash.encode()).hexdigest()

            EmailTracking.objects.create(
                email=email_obj,
                subscriber=subscriber,
                unique_id=unique_id,
            )

            click_tracking_url = f"{base_url}/Email/track/click/{unique_id}"
            open_tracking_url = f"{base_url}/Email/track/open/{unique_id}"

            soap = BeautifulSoup(message, 'html.parser')
            for a in soap.find_all('a', href=True):
                original = a['href']
                a['href'] = f"{click_tracking_url}?url={quote(original, safe='')}"

            open_tracking_image = f"<img src='{open_tracking_url}' width='1' height='1' style='display:none;' alt=''>"
            new_message = str(soap) + open_tracking_image

        try:
            mail = EmailMessage(mail_subject, new_message, from_email, to=[recipient])
            if attachment and os.path.exists(attachment):
                mail.attach_file(attachment)
            mail.content_subtype = "html"
            sent_count = mail.send(fail_silently=False)
            if sent_count == 0:
                raise RuntimeError(f"Failed to send email to {recipient}: backend returned 0 sent messages.")
        except Exception as e:
            logger.error(f"[Email Error] Failed to send email to '{recipient}' with subject '{mail_subject}': {e}", exc_info=True)
            raise e


    if email_obj:
        Sent.objects.create(
            email=email_obj,
            total_sent=len(to_email)
        )



#=======================generating csv file name and path for exporting data=================

def generate_csv_file(model_name):
    timestamp = datetime.datetime.now().strftime("%Y-%m-%d-%H-%M")
    export_dir = os.path.join(settings.MEDIA_ROOT, "exported_data")
    os.makedirs(export_dir, exist_ok=True)

    file_name = f"exported_data_of_{model_name}-{timestamp}.csv"
    file_path = os.path.join(export_dir, file_name)
    return file_path

