from django.utils import timezone
from django.db import models
from django.contrib.auth.models import AbstractUser
from phonenumber_field.modelfields import PhoneNumberField

# Create your models here.


class CustomUser(AbstractUser):

    SIZE_CHOICES = [
        ("<100", "<100"),
        ("100-200", "100-200"),
        (">200", ">200"),
    ]

    Name_of_Company = models.CharField(max_length=50)
    Name_of_Encharge = models.CharField(max_length=20)
    phone = PhoneNumberField()
    Sector = models.CharField(max_length=50)
    company_size = models.CharField(max_length=10, choices=SIZE_CHOICES)


    def __str__(self):
        return f"{self.Name_of_Company} -- {self.Name_of_Encharge}"




class Student(models.Model):
    user = models.ForeignKey(CustomUser , on_delete=models.CASCADE)
    Roll_no = models.CharField(max_length=10)
    name = models.CharField(max_length=20)
    age = models.IntegerField()

    def  __str__(self):
        return self.name
    




class Employee(models.Model):
    user = models.ForeignKey(CustomUser , on_delete=models.CASCADE)
    employee_id = models.IntegerField()
    employee_name = models.CharField(max_length=100)
    designation = models.CharField(max_length=200)
    salary = models.DecimalField(max_digits=50 , decimal_places=2)
    retirement = models.DecimalField(max_digits=50 , decimal_places=2)
    other_benefits = models.DecimalField(max_digits=50 , decimal_places=2)
    total_benefits = models.DecimalField(max_digits=50 , decimal_places=2)
    total_compensation = models.DecimalField(max_digits=50 , decimal_places=2)


    def __str__(self):
        return f"{self.employee_id} -- {self.employee_name}"




class History(models.Model):

    TOOL_CHOICES = [
        ('Import', 'Import'),
        ('Export', 'Export'),
        ('Email_Send', 'Email Send'),
    ]

    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('processing', 'Processing'),
        ('retrying', 'Retrying'),
        ('success', 'Success'),
        ('failed', 'Failed'),
    ]
    
    company = models.ForeignKey(
        CustomUser,
        on_delete=models.CASCADE,
        related_name="histories"
    )

    work = models.CharField(max_length=100, choices=TOOL_CHOICES)

    data = models.TextField(
        blank=True,
        null=True,
        help_text="Optional: file name, email, record id, etc."
    )

    status = models.CharField(
        max_length=10,
        choices=STATUS_CHOICES,
        default="success"
    )
    task_id = models.CharField(max_length=255, null=True, blank=True)
    retry_count = models.IntegerField(default=0)
    error_logs = models.TextField(null=True, blank=True)
    started_at = models.DateTimeField(null=True, blank=True)
    completed_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    @property
    def processing_time(self):
        if self.started_at and self.completed_at:
            return (self.completed_at - self.started_at).total_seconds()
        elif self.started_at and self.status in ['processing', 'retrying']:
            from django.utils import timezone
            return (timezone.now() - self.started_at).total_seconds()
        return 0

    def __str__(self):
        return f"{self.company} - {self.work} - {self.created_at}"




class SubscriptionPlan(models.Model):
    name = models.CharField(max_length=50)
    price = models.DecimalField(max_digits=8, decimal_places=2)
    duration_days = models.IntegerField()

    email_limit_per_day = models.IntegerField()
    import_limit_per_day = models.IntegerField()
    export_limit_per_day = models.IntegerField()

    is_active = models.BooleanField(default=True)

    def __str__(self):
        return self.name



class UserSubscription(models.Model):
    user = models.OneToOneField(CustomUser, on_delete=models.CASCADE)
    plan = models.ForeignKey(SubscriptionPlan, on_delete=models.PROTECT)

    start_date = models.DateTimeField(auto_now_add=True)
    end_date = models.DateTimeField()
    is_active = models.BooleanField(default=True)

    def is_valid(self):
        return self.is_active and self.end_date > timezone.now()






class DailyUsage(models.Model):
    user = models.ForeignKey(CustomUser, on_delete=models.CASCADE)
    date = models.DateField()

    emails_sent = models.IntegerField(default=0)
    imports_done = models.IntegerField(default=0)
    exports_done = models.IntegerField(default=0)

    class Meta:
        unique_together = ('user', 'date')


    def __str__(self):
        return f"{self.user} -- {self.date}"

