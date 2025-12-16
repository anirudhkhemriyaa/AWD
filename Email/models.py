from django.db import models
from ckeditor.fields import RichTextField
# Create your models here.


class List(models.Model):
    email_list = models.CharField(max_length=25)

    def __str__(self):
        return self.email_list
    
    def count_emails(self):
        count = Subscriber.objects.filter(email_list=self.email_list).count()
        return count
    



class Subscriber(models.Model):
    email_list = models.ForeignKey(List , on_delete=models.CASCADE)
    email_address = models.EmailField(max_length=50)

    def __str__(self):
        return self.email_address



class Email(models.Model):
    email_list = models.ForeignKey(List , on_delete=models.CASCADE )
    subject = models.CharField(max_length=50)
    body = RichTextField()
    attachment = models.FileField(upload_to='email_attachment/' , blank=True)
    sent_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.subject
    

class Sent(models.Model):
    email = models.ForeignKey(Email , on_delete=models.CASCADE)
    total_sent = models.IntegerField()

    def __str__(self):
        return f"Sent: {self.email.subject} at {self.total_sent}"


class EmailTracking(models.Model):
    email = models.ForeignKey(Email , on_delete=models.CASCADE)
    subscriber = models.ForeignKey(Subscriber , on_delete=models.CASCADE , null=True, blank=True)
    unique_id = models.CharField(max_length=100 ,unique=True)
    opened = models.BooleanField(null=True,default=False)
    clicked = models.BooleanField(null=True,default=False)

    def __str__(self):
        return f"Tracking for {self.email.subject}"