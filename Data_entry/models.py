from django.db import models

# Create your models here.


class Student(models.Model):
    Roll_no = models.CharField(max_length=10)
    name = models.CharField(max_length=20)
    age = models.IntegerField()

    def  __str__(self):
        return self.name
    


class Customer(models.Model):
    country = models.CharField(max_length=50)
    country_code = models.IntegerField()


    def __str__(self):
        return self.country
    


class Employee(models.Model):
    employee_id = models.IntegerField()
    employee_name = models.CharField(max_length=100)
    designation = models.CharField(max_length=200)
    salary = models.DecimalField(max_digits=50 , decimal_places=2)
    retirement = models.DecimalField(max_digits=50 , decimal_places=2)
    other_benefits = models.DecimalField(max_digits=50 , decimal_places=2)
    total_benefits = models.DecimalField(max_digits=50 , decimal_places=2)
    total_compensation = models.DecimalField(max_digits=50 , decimal_places=2)