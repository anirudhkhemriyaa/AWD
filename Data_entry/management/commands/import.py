from django.core.management.base import BaseCommand , CommandError
from django.db import DataError
# from Data_entry.models import Student instead of this 
from django.apps import apps
import csv
from Data_entry.utils import check_csv_error


class Command(BaseCommand):
    help = "You can upload csv file with relatable data and data is inserted automatically"

    def add_arguments(self, parser):
        parser.add_argument('file_path' , type=str , help="Path to file")
        parser.add_argument('model_name' , type=str , help="Enter model name")


    def handle(self , *args, **kwargs):
        file_path = kwargs['file_path']
        model_name = kwargs['model_name'].capitalize()

        model = check_csv_error(file_path , model_name)


        with open(file_path,'r') as file:
            reader = csv.DictReader(file)
            for row in reader:  
                model.objects.create(**row)
        self.stdout.write(self.style.SUCCESS('You file data is inserted'))