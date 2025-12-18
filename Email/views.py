from django.http import HttpResponse
from django.shortcuts import render,redirect
from .forms import Email_form
from django.contrib import messages
from Data_entry.utils import send_email_notification
from django.conf import settings
from .models import EmailTracking, Sent, Subscriber
from .tasks import send_email_task
from .models import Email
from django.db.models import Sum
from django.utils import timezone
# Create your views here.

#=============================Send bulk email view===================
def send_email(request):
    if request.method == "POST":
        form = Email_form(request.POST , request.FILES)
        if form.is_valid():
            email = form.save()
            mail_subject = request.POST.get('subject')
            msg = request.POST.get('body')
            email_list = request.POST.get('email_list')
            email_list = email.email_list 

            # Extract email address from subscriber model
            subscribers = Subscriber.objects.filter(email_list=email_list)
            to_email=[email.email_address for email in subscribers ]

            if email.attachment:
                attachment = email.attachment.path
            else:
                attachment=None

            email_id = email.id

            send_email_task.delay(mail_subject , msg , to_email , attachment , email_id)

            messages.success(request , 'Email sent successfully')
            return redirect('send_email')

    else:
        form = Email_form()
        context = {
            'form':form
        }
    return render(request , 'emails/send_email.html' , context)







def track_open(request, unique_id):
    print("tracking open...")
    try:
        email_tracking = EmailTracking.objects.get(unique_id=unique_id)

        if not email_tracking.opened_at:
            email_tracking.opened_at = timezone.now()
            email_tracking.save()
            print("saved")
            return HttpResponse("hello") 
        else:
            return HttpResponse("already opened")

    except EmailTracking.DoesNotExist:
        return HttpResponse("bye-bye")
          # do NOT expose state

    



def track_click(request , unique_id):
    try:
        email_tracking = EmailTracking.objects.get(unique_id=unique_id)
        original_url = request.GET.get('url')
        if not email_tracking.clicked_at:
            email_tracking.clicked_at = timezone.now()
            email_tracking.save()
        # Redirect to the original URL
        return redirect(original_url)
    except:
        return HttpResponse("Invalid tracking link.")

#=========================tracking dashboard view=========================

def tracking_dashboard(request):
    emails = Email.objects.all().annotate(total_sent=Sum('sent__total_sent')).order_by('-sent_at')
    context = {
        'emails':emails
    }
    return render(request , 'emails/track_dashboard.html',context)



def track_stats(request , unique_id):
    email = Email.objects.get(id=unique_id)
    sent = Sent.objects.filter(email=email)

    context = {
        'email':email,
        'total_sent':sent
    }
    return render(request , 'emails/track_stats.html' , context)