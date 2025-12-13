from django.apps import apps
from django.core.management.base import CommandError
import csv
from django.db import DataError




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


