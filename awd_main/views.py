from datetime import date
from django.shortcuts import render, redirect
from django.contrib import messages, auth
from django.contrib.auth.forms import AuthenticationForm
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.db.models import Avg, Count, Q, F
from django.utils import timezone
from Data_entry.models import CustomUser, DailyUsage, UserSubscription
from .forms import RegistrationForm

#============= Landing page ===========

def Base(request):
    return render(request, "base.html")


#========================= Registration view ====================

def register(request):
    if request.method == "POST":
        form = RegistrationForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, "Registration successful.")
            return redirect('login')
        else:
            messages.error(request, "Registration failed. Invalid information.")
            return redirect('register')
    else:
        form = RegistrationForm()
        context = {
            'form': form,
        }
    return render(request, "register.html", context)


#========================= Login view ==========================

def login(request):
    if request.method == 'POST':
        form = AuthenticationForm(request, request.POST)
        if form.is_valid():
            username = form.cleaned_data['username']
            password = form.cleaned_data['password']

            user = auth.authenticate(username=username, password=password)

            if user is not None:
                auth.login(request, user)
                return redirect('base')
        else:
            messages.error(request, 'Invalid Credentials')
            return redirect('login')

    else:
        form = AuthenticationForm()
        context = {
            'form': form,
        }
    return render(request, "login.html", context)


#========================= Logout view =======================

def logout(request):
    auth.logout(request)
    return redirect('login')


#========================= Profile view =======================

@login_required
def profile(request):
    user = request.user
    histories = user.histories.order_by('-created_at')[:20]

    subscription = UserSubscription.objects.filter(
        user=user,
        is_active=True
    ).select_related("plan").first()

    today = timezone.now().date()
    daily_usage, _ = DailyUsage.objects.get_or_create(
        user=user,
        date=today
    )

    remaining = {}
    if subscription and subscription.is_valid():
        plan = subscription.plan
        remaining = {
            "emails_left": max(plan.email_limit_per_day - daily_usage.emails_sent, 0),
            "imports_left": max(plan.import_limit_per_day - daily_usage.imports_done, 0),
            "exports_left": max(plan.export_limit_per_day - daily_usage.exports_done, 0),
        }

    context = {
        "profile": user,
        "histories": histories,
        "subscription": subscription,
        "daily_usage": daily_usage,
        "remaining": remaining,
        "today": timezone.now(),
    }

    return render(request, "profile.html", context)


#======================== Edit profile =======================

@login_required
def profile_edit(request):
    profile = request.user

    if request.method == "POST":
        profile.Name_of_Company = request.POST.get("Name_of_Company")
        profile.Name_of_Encharge = request.POST.get("Name_of_Encharge")
        profile.Sector = request.POST.get("Sector")
        profile.email = request.POST.get("email")
        profile.username = request.POST.get("username")
        profile.company_size = request.POST.get("company_size")
        profile.phone = request.POST.get("phone")
        profile.save()

        messages.success(request, "Profile updated successfully.")
        return redirect("profile")

    return render(request, "edit_profile.html", {"profile": profile})


@login_required
def jobs_api(request):
    histories = request.user.histories.all()

    total = histories.count()
    failed = histories.filter(status='failed').count()

    avg_dur = histories.filter(status='success', started_at__isnull=False, completed_at__isnull=False).aggregate(
        avg_processing_time=Avg(F('completed_at') - F('started_at'))
    )['avg_processing_time']

    avg_time_str = str(avg_dur).split('.')[0] if avg_dur else "0s"

    recent_jobs = histories.order_by('-created_at')[:20]
    results = []

    for job in recent_jobs:
        ptime = job.processing_time
        retries = job.retry_count
        results.append({
            "id": job.id,
            "work": job.work,
            "info": job.data or "—",
            "status": job.status,
            "retries": retries,
            "time": f"{round(ptime, 1)}s" if ptime else "-",
            "date": job.created_at.strftime("%b %d, %Y • %H:%M")
        })

    return JsonResponse({
        "metrics": {
            "total": total,
            "failed": failed,
            "avg_time": avg_time_str
        },
        "jobs": results
    })

