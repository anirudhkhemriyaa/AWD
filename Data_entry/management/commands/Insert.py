from django.core.management.base import BaseCommand
from Data_entry.models import Student


#==================Inserting command only for testing purpose===============
class Command(BaseCommand):
    help = "Insert  Data "

    def handle(self , *args, **kwargs):
        dataset = [
            {'Roll_no':1 , 'name':'Soja' , 'age':19},
            {'Roll_no':2 , 'name':'Roja' , 'age':19},
            {'Roll_no':3 , 'name':'Moja' , 'age':19},
        ]
        
        for data in dataset:
            roll = data['Roll_no']
            is_exist = Student.objects.filter(Roll_no = roll).exists()

            if not is_exist:
                student = Student.objects.create(Roll_no=data['Roll_no'] , name=data['name'] , age=data['age'])

            else:
                self.stdout.write(self.style.WARNING("Data exists"))


        self.stdout.write(self.style.SUCCESS("Inserted Data"))