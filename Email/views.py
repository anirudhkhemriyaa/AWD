from django.http import HttpResponse, HttpResponseRedirect
from django.shortcuts import get_object_or_404, render, redirect
from django.contrib import messages
from django.db.models import Sum
from django.db.models.functions import Coalesce
from django.utils import timezone
from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied
from Data_entry.limit import enforce
from Data_entry.models import History, UserSubscription
from .forms import Email_form
from .models import EmailTracking, Sent, Subscriber, Email
from .tasks import send_email_task

#=============================Send bulk email view===================
@login_required(login_url="login")
def send_email(request):
    if request.method == "POST":
        form = Email_form(request.POST, request.FILES)
        if form.is_valid():
            email = form.save(commit=False)
            email.company = request.user
            email.save()

            user = request.user

            sub = UserSubscription.objects.filter(
                user=user,
                is_active=True
            ).select_related("plan").first()

            if not sub:
                messages.error(request, "You don't have an active subscription to use this tool.")
                return redirect("send_email")

            if not sub.is_valid():
                messages.error(request, "Your subscription has expired.")
                return redirect("send_email")

            subscribers = Subscriber.objects.filter(email_list=email.email_list)
            to_email = [s.email_address for s in subscribers]
            recipient_count = len(to_email)

            if recipient_count == 0:
                messages.error(request, "The selected subscriber list has no active email addresses.")
                return redirect("send_email")

            try:
                enforce(user, "email", sub.plan.email_limit_per_day, count=recipient_count)
            except PermissionDenied as e:
                messages.error(request, str(e))
                return redirect("send_email")

            mail_subject = email.subject
            msg = email.body
            attachment = email.attachment.path if email.attachment else None

            history = History.objects.create(
                company=user,
                work="Email_Send",
                data=f"{email.subject} ({recipient_count} recipients)",
                status="pending",
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

            messages.success(request, f"Emails are queued for sending to {recipient_count} recipients.")
            return redirect("send_email")

    form = Email_form()
    return render(request, "emails/send_email.html", {"form": form})


PIXEL_GIF = (
    b'\x47\x49\x46\x38\x39\x61\x01\x00\x01\x00\x80\x00\x00\xff\xff\xff'
    b'\x00\x00\x00\x21\xf9\x04\x01\x00\x00\x00\x00\x2c\x00\x00\x00\x00'
    b'\x01\x00\x01\x00\x00\x02\x02\x44\x01\x00\x3b'
)


def track_open(request, unique_id):
    try:
        email_tracking = EmailTracking.objects.get(unique_id=unique_id)
        if not email_tracking.opened_at:
            email_tracking.opened_at = timezone.now()
            email_tracking.save(update_fields=['opened_at'])
    except EmailTracking.DoesNotExist:
        pass

    return HttpResponse(PIXEL_GIF, content_type="image/gif")


def track_click(request, unique_id):
    original_url = request.GET.get('url', '/')
    try:
        email_tracking = EmailTracking.objects.get(unique_id=unique_id)
        if not email_tracking.clicked_at:
            email_tracking.clicked_at = timezone.now()
            email_tracking.save(update_fields=['clicked_at'])
    except EmailTracking.DoesNotExist:
        pass

    return HttpResponseRedirect(original_url)


#=========================tracking dashboard view=========================

@login_required(login_url="login")
def tracking_dashboard(request):
    emails = Email.objects.filter(
        company=request.user
    ).annotate(
        total_sent=Coalesce(Sum('sent__total_sent'), 0)
    ).order_by('-sent_at')

    context = {
        'emails': emails
    }
    return render(request, 'emails/track_dashboard.html', context)


@login_required(login_url="login")
def track_stats(request, email_id):
    email = get_object_or_404(
        Email,
        id=email_id,
        company=request.user
    )
    sent = Sent.objects.filter(email=email)

    context = {
        'email': email,
        'total_sent': sent
    }
    return render(request, 'emails/track_stats.html', context)