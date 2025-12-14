from django.apps import apps
from django.core.management.base import CommandError
import csv
from django.db import DataError
from django.core.mail import EmailMessage
from django.conf import settings
import datetime
import os





def get_all_models():
    default = ['Upload','ContentType' , 'Session','LogEntry' , 'Group','Permission', 'User']
    custom_model =[]
    for model in apps.get_models():
        if model.__name__ not in default:
            custom_model.append(model.__name__)
    print(model.__name__)
    return custom_model





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

 


def send_email_notification(mail_subject , message , to_email , attachment=None):  
    try:
        from_email = settings.DEFAULT_FROM_EMAIL
        mail = EmailMessage(mail_subject , message , from_email , to=[to_email])
        if attachment is not None:
            mail.attach_file(attachment)
        mail.send()
    except Exception as e:
        raise e
        



def generate_csv_file(model_name):
    timestamp = datetime.datetime.now().strftime("%Y-%m-%d-%H-%M")

        # define file path

    export_dir = 'exported_data'

    file_name = f'exported_data_of_{model_name}-{timestamp}.csv'
    file_path = os.path.join(settings.MEDIA_ROOT , export_dir , file_name)
    return file_path