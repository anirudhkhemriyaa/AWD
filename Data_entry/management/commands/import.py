from django.core.management.base import BaseCommand , CommandError
from django.db import DataError
# from Data_entry.models import Student instead of this 
from django.apps import apps
import csv
from Data_entry.utils import check_csv_error
from Email.models import List



#=========================Import Command giving data to db===========================

class Command(BaseCommand):
    help = "Import CSV data into selected model"

    def add_arguments(self, parser):
        parser.add_argument('file_path', type=str)
        parser.add_argument('model_name', type=str)
        parser.add_argument('--list_id', type=int, default=None)
    

    def handle(self, *args, **options):
        file_path = options['file_path']
        model_name = options['model_name'].lower()
        list_id = options.get('list_id')

        model = check_csv_error(file_path, model_name)

        email_list = None
        if model_name == "subscriber":
            if not list_id:
                raise CommandError("Subscriber import requires --list_id")
            email_list = List.objects.get(id=list_id)

        with open(file_path, 'r', encoding='utf-8-sig', errors='ignore') as file:
            reader = csv.DictReader(file)

            for row in reader:
                if model_name == "subscriber":
                    row["email_list"] = email_list  # inject FK

                model.objects.create(**row)

        self.stdout.write(self.style.SUCCESS("Your file data is inserted"))
