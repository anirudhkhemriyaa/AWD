from django.http import HttpResponse
from django.shortcuts import render,redirect
from Data_entry.limit import enforce
from .forms import Email_form
from django.contrib import messages
from .models import EmailTracking, Sent, Subscriber, Email
from .tasks import send_email_task
from django.db.models import Sum
from django.utils import timezone
from django.contrib.auth.decorators import login_required
from Data_entry.models import History, UserSubscription
from django.core.exceptions import PermissionDenied
# Create your views here.

#=============================Send bulk email view===================
@login_required(login_url="login")
def send_email(request):
    if request.method == "POST":
        form = Email_form(request.POST, request.FILES)
        if form.is_valid():
            email = form.save()

            user = request.user
            sub = UserSubscription.objects.select_related("plan").get(user=user)

            if not sub.is_valid():
                messages.error(request, "Your subscription has expired.")
                return redirect("send_email")

            try:
                enforce(user, "email", sub.plan.email_limit_per_day)
            except PermissionDenied as e:
                messages.error(request, str(e))
                return redirect("send_email")

            mail_subject = email.subject
            msg = email.body
            email_list = email.email_list

            subscribers = Subscriber.objects.filter(email_list=email_list)
            to_email = [s.email_address for s in subscribers]

            attachment = email.attachment.path if email.attachment else None

            history = History.objects.create(
                company=user,
                work="Email_Send",
                data=f"{len(to_email)} recipients",
                status="processing",
            )

            send_email_task.delay(
                user.id,
                mail_subject,
                msg,
                to_email,
                attachment,
                email.id,
                history.id
            )

            messages.success(request, "Emails are being sent.")
            return redirect("send_email")

    form = Email_form()
    return render(request, "emails/send_email.html", {"form": form})







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