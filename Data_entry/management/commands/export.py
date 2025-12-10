import csv
from django.core.management.base import BaseCommand
from Data_entry.models import Student
from django.apps import apps


import datetime

class Command(BaseCommand):
    help = "Export data"

    def add_arguments(self, parser):
        parser.add_argument('model_name' , type=str , help="Enter model name")

    def handle(self , *args, **kwargs):
        #fetch data from db 
        model_name = kwargs['model_name'].capitalize()

        model = None
        for app_config in apps.get_app_configs():
            try:
                model = apps.get_model(app_config.label , model_name)
                break
            except LookupError:
                continue


        if model is not None:
            dataset = model.objects.all()
        print("Fetching the data....")

        timestamp = datetime.datetime.now().strftime("%Y-%m-%d-%H-%M")

        # define file path
        file_path = f'exported_data_of_{model_name}-{timestamp}.csv'

        # open file and write file

        with open(file_path , 'w' , newline='') as file:
            writer = csv.writer(file)

            # write csv header 
            writer.writerow([field.name for field in model._meta.fields])
  
            for data in dataset:
                writer.writerow(getattr(data , field.name) for field in model._meta.fields )

        self.stdout.write(self.style.SUCCESS("Data extracted successfully"))    