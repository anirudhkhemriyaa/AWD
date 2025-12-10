from django.core.management.base import BaseCommand


class Command(BaseCommand):
    help = "Going to print hello world"

    def add_arguments(self, parser):
        parser.add_argument('name' , type=str , help="Enter user name")

    def handle(self ,  *args, **kwargs):
        name = kwargs['name']
        self.stdout.write(self.style.SUCCESS(f'hello {name}'))