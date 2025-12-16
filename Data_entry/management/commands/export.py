import csv
from django.core.management.base import BaseCommand
from Data_entry.models import Student
from django.apps import apps
from Data_entry.utils import generate_csv_file

#=============================Export data from any model (except some) to csv file ===============================

class Command(BaseCommand):
    help = "Export data"

    def add_arguments(self, parser):
        parser.add_argument('model_name' , type=str , help="Enter model name")

    def handle(self , *args, **kwargs):
        model_name = kwargs['model_name'].capitalize()

        model = None
        for app_config in apps.get_app_configs():
            try:
                model = apps.get_model(app_config.label , model_name)
                break
            except LookupError:
                pass

        if model is not None:
            dataset = model.objects.all()

        file_path = generate_csv_file(model_name)

        with open(file_path , 'w' , newline='') as file:
            writer = csv.writer(file)

            writer.writerow([field.name for field in model._meta.fields])
  
            for data in dataset:
                writer.writerow(getattr(data , field.name) for field in model._meta.fields)

        self.stdout.write(self.style.SUCCESS("Data extracted successfully"))    