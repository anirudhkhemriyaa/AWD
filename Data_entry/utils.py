import hashlib
from django.apps import apps
from django.core.management.base import CommandError
import csv
from django.db import DataError
from django.core.mail import EmailMessage
from django.conf import settings
import datetime
import os
from Email.models import Email, EmailTracking , Sent, Subscriber
import time
from bs4 import BeautifulSoup

#=======================Fetching all models in our project===========================

def get_all_models():
    default = ['Upload','ContentType' , 'Session','LogEntry' , 'Group','Permission', 'User']
    custom_model =[]
    for model in apps.get_models():
        if model.__name__ not in default:
            custom_model.append(model.__name__)
    return custom_model



#======Checking Header error while importing the data whether field is correct or not=====

def check_csv_error(file_path , model_name):
    model = None
    for app_config in apps.get_app_configs():
        try:
            model = apps.get_model(app_config.label , model_name)
            break
        except LookupError:
            continue 

    if not model:
        raise CommandError(f'Model {model_name} not found' )
    else:
        model_fields = [field.name for field in model._meta.fields if field.name != 'id']
    

    try:
        with open(file_path , 'r') as file:
            reader = csv.DictReader(file)
            csv_header = reader.fieldnames

            if csv_header != model_fields:
                raise DataError(f"csv file doesn't match with the {model_name} table fields")
                
    except Exception as e:
        raise e
    
    return model

 
 #=================================Sending Eamil======================= =============

def send_email_notification(mail_subject , message , to_email , attachment=None , email_id=None): 
    try:
        from_email = settings.DEFAULT_FROM_EMAIL


        for recipient in to_email:
             #-----tracking record----
            new_message=message
            if email_id:
                email = Email.objects.get(pk=email_id)
                subscriber = Subscriber.objects.get(email_list=email.email_list , email_address=recipient)
                timestamp = str(time.time())
                data_to_hash = f"{recipient}-{timestamp}"
                unique_id = hashlib.sha256(data_to_hash.encode()).hexdigest()
                email_tracking = EmailTracking.objects.create(
                    email=email,
                    subscriber=subscriber,
                    unique_id = unique_id,
                )

                #---------generate the tracking pixel url
                base = settings.BASE_URL
                click_tracking_url = f"{base}/Email/track/click/{unique_id}"
                open_tracking_url = f"{base}/Email/track/open/{unique_id}"
                print(f'open link >> {open_tracking_url}')
                #------------search for link in msg-------
                soap = BeautifulSoup(message , 'html.parser')
                urls = [ a['href'] for a in soap.find_all('a' , href=True)]

                if urls:
                    for url in urls:
                        tracked_url = f"{click_tracking_url}?url={url}"
                        new_message = message.replace(f"{url}" , f"{tracked_url}")
                else:
                    print("No links found in the email message.")

                open_tracking_image=f"<img src='{open_tracking_url}' width='1' height='1'>"
                new_message += open_tracking_image
                
            mail = EmailMessage(mail_subject , new_message , from_email , to=[recipient])
            if attachment is not None:
                mail.attach_file(attachment)
            mail.content_subtype = "html"
            mail.send()
        #---------------------------- Count to email sent ---------------------------
        if email:
            sent = Sent()
            sent.email = email
            sent.total_sent = email.email_list.count_emails()
            sent.save()

    except Exception as e:
        raise e
        

#=======================Generating csv file name and path for exporting data=================

def generate_csv_file(model_name):
    timestamp = datetime.datetime.now().strftime("%Y-%m-%d-%H-%M")

    export_dir = 'exported_data'

    file_name = f'exported_data_of_{model_name}-{timestamp}.csv'
    file_path = os.path.join(settings.MEDIA_ROOT , export_dir , file_name)
    return file_path