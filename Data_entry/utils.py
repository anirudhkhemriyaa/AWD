from django.apps import apps

def get_all_models():
    default = ['Upload','ContentType' , 'Session','LogEntry' , 'Group','Permission', 'User']
    custom_model =[]
    for model in apps.get_models():
        if model.__name__ not in default:
            custom_model.append(model.__name__)
    print(model.__name__)
    return custom_model