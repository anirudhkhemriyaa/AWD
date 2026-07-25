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

    def handle(self, *args, **kwargs):
        from django.contrib.auth import get_user_model
        User = get_user_model()

        user = User.objects.get(id=kwargs["user_id"])
        model_name = kwargs['model_name'].strip()

        model = None
        for app_config in apps.get_app_configs():
            for m in app_config.get_models():
                if m.__name__.lower() == model_name.lower():
                    model = m
                    break
            if model:
                break

        if model is None:
            raise CommandError(f"Model {model_name} not found")

        fields = [field for field in model._meta.fields]
        field_names = [f.name for f in fields]

        if "user" in field_names:
            dataset = model.objects.filter(user=user)
        else:
            dataset = model.objects.all()

        file_path = kwargs["file_path"]

        with open(file_path, 'w', newline='', encoding='utf-8') as file:
            writer = csv.writer(file)
            writer.writerow(field_names)

            for data in dataset:
                row = []
                for field in fields:
                    val = getattr(data, field.name)
                    row.append(str(val) if val is not None else "")
                writer.writerow(row)

        self.stdout.write(self.style.SUCCESS(f"Data extracted successfully to {file_path}"))