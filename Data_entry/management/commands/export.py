import csv
from django.core.management.base import BaseCommand, CommandError
from django.apps import apps

#=============================Export data from any model (except some) to csv file ===============================

class Command(BaseCommand):
    help = "Export data"

    def add_arguments(self, parser):
        parser.add_argument("model_name", type=str)
        parser.add_argument("--user_id", type=int, required=True)
        parser.add_argument("--file_path", type=str, required=True)

    def handle(self , *args, **kwargs):
        from django.contrib.auth import get_user_model
        User = get_user_model()

        user = User.objects.get(id=kwargs["user_id"])
        model_name = kwargs['model_name'].capitalize()

        model = None
        for app_config in apps.get_app_configs():
            try:
                model = apps.get_model(app_config.label , model_name)
                break
            except LookupError:
                pass

        if model is None:
            raise CommandError(f"Model {model_name} not found")

        dataset = model.objects.filter(user=user)

        file_path = kwargs["file_path"]


        with open(file_path , 'w' , newline='') as file:
            writer = csv.writer(file)

            writer.writerow([field.name for field in model._meta.fields])
  
            for data in dataset:
                writer.writerow(getattr(data , field.name) for field in model._meta.fields)

        self.stdout.write(self.style.SUCCESS("Data extracted successfully"))    