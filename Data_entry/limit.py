from django.utils import timezone
from django.core.exceptions import PermissionDenied
from redis import Redis
from .models import UserSubscription

redis = Redis()

def enforce_import_limit(user):
    sub = UserSubscription.objects.select_related('plan').get(user=user)

    if not sub.is_valid():
        raise PermissionDenied("Subscription expired")

    today = timezone.now().date()
    key = f"import:{user.id}:{today}"

    count = redis.incr(key)
    redis.expire(key, 86400)

    if count > sub.plan.import_limit_per_day:
        redis.decr(key)
        raise PermissionDenied("Daily import limit exceeded")
    



def enforce_export_limit(user):
    sub = UserSubscription.objects.select_related('plan').get(user=user)

    if not sub.is_valid():
        raise PermissionDenied("Subscription expired")

    today = timezone.now().date()
    key = f"export:{user.id}:{today}"

    count = redis.incr(key)
    redis.expire(key, 86400)

    if count > sub.plan.export_limit_per_day:
        redis.decr(key)
        raise PermissionDenied("Daily export limit exceeded")




def enforce_email_limit(user):
    sub = UserSubscription.objects.select_related('plan').get(user=user)

    if not sub.is_valid():
        raise PermissionDenied("Subscription expired")

    today = timezone.now().date()
    key = f"email:{user.id}:{today}"

    count = redis.incr(key)
    redis.expire(key, 86400)

    if count > sub.plan.email_limit_per_day:
        redis.decr(key)
        raise PermissionDenied("Daily email limit exceeded")
    


from django.utils import timezone
from .models import DailyUsage

def record_usage(user, field):
    today = timezone.now().date()
    usage, _ = DailyUsage.objects.get_or_create(user=user, date=today)

    setattr(usage, field, getattr(usage, field) + 1)
    usage.save(update_fields=[field])
