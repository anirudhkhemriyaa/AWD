from django.db import models

# Create your models here.


class Student(models.Model):
    name = models.CharField(max_length=20)
    Roll_no = models.CharField(max_length=10)
    age = models.IntegerField()

    def  __str__(self):
        return self.name
    


class Customer(models.Model):
    country = models.CharField(max_length=50)
    country_code = models.IntegerField()


    def __str__(self):
        return self.country