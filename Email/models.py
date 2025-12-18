from django.db import models
from ckeditor.fields import RichTextField
# Create your models here.

#=======================List model set of user belongs to which list (e.g. customer , student)

class List(models.Model):
    email_list = models.CharField(max_length=25)

    def __str__(self):
        return self.email_list
    
    def count_emails(self):
        count = Subscriber.objects.filter(email_list=self).count()
        return count
    

#============================ Email address of user belonging to particular list========

class Subscriber(models.Model):
    email_list = models.ForeignKey(List , on_delete=models.CASCADE)
    email_address = models.EmailField(max_length=50)

    def __str__(self):
        return self.email_address

#=====================================Email part composing email========================

class Email(models.Model):
    email_list = models.ForeignKey(List , on_delete=models.CASCADE )
    subject = models.CharField(max_length=50)
    body = RichTextField()
    attachment = models.FileField(upload_to='email_attachment/' , blank=True)
    sent_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.subject
    
    def open_rate(self):
        total_sent = self.email_list.count_emails()
        total_opened = EmailTracking.objects.filter(email=self , opened_at__isnull=False).count()
        if total_sent>0:
            open_rate =  (total_opened/total_sent)*100
        else:
            open_rate=0
        return round(open_rate,2)
    
    def click_rate(self):
        total_sent = self.email_list.count_emails()
        total_clicked = EmailTracking.objects.filter(email=self , clicked_at__isnull=False).count()
        if total_sent>0:
            click_rate =  (total_clicked/total_sent)*100
        else:
            click_rate=0
        return round(click_rate,2)

#===================================Number of sent to email (count)=====================

class Sent(models.Model):
    email = models.ForeignKey(Email , on_delete=models.CASCADE , null=True, blank=True)
    total_sent = models.IntegerField()

    def __str__(self):
        return f"Sent: {self.email.subject} at {self.total_sent}"


#===================Email track (when opened,clicked to link)====================

class EmailTracking(models.Model):
    email = models.ForeignKey(Email , on_delete=models.CASCADE)
    subscriber = models.ForeignKey(Subscriber , on_delete=models.CASCADE , null=True, blank=True)
    unique_id = models.CharField(max_length=100 ,unique=True)
    opened_at = models.DateTimeField(null=True, blank=True)
    clicked_at = models.DateTimeField(null=True, blank=True)

    def __str__(self):
        return f"Tracking for {self.email.subject}"