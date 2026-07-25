import os
from datetime import datetime, time, timedelta
from django.utils import timezone
from django.core.exceptions import PermissionDenied
from django.db.models import F
from redis import Redis
from .models import DailyUsage


LIMIT_LUA = """
local current = redis.call("INCRBY", KEYS[1], ARGV[3])
if current == tonumber(ARGV[3]) then
  redis.call("EXPIRE", KEYS[1], ARGV[1])
end
if current > tonumber(ARGV[2]) then
  redis.call("DECRBY", KEYS[1], ARGV[3])
  return -1
end
return current
"""

ACTION_FIELD_MAP = {
    "import": "imports_done",
    "export": "exports_done",
    "email": "emails_sent",
}


def get_redis():
    redis_url = os.getenv("REDIS_URL")
    if not redis_url:
        raise RuntimeError("REDIS_URL is not set")
    return Redis.from_url(redis_url)


def get_limit_script():
    redis = get_redis()
    return redis.register_script(LIMIT_LUA)


def seconds_until_midnight():
    now = timezone.now()
    tomorrow = (now + timedelta(days=1)).date()
    midnight = datetime.combine(tomorrow, time.min).astimezone(now.tzinfo)
    return int((midnight - now).total_seconds())


def get_db_usage(user, today, action):
    field = ACTION_FIELD_MAP.get(action, action)
    usage = DailyUsage.objects.filter(user=user, date=today).first()
    if usage:
        return getattr(usage, field, 0)
    return 0


def enforce(user, action, daily_limit, count=1):
    if count <= 0:
        return

    today = timezone.now().date()
    key = f"{action}:{user.id}:{today}"
    ttl = seconds_until_midnight()

    redis = get_redis()
    limit_script = get_limit_script()

    # Cold start check: if key does not exist in Redis, sync from DB first
    if not redis.exists(key):
        db_usage = get_db_usage(user, today, action)
        if db_usage > 0:
            redis.set(key, db_usage, ex=ttl)

    result = limit_script(
        keys=[key],
        args=[ttl, daily_limit, count],
    )

    if result == -1:
        raise PermissionDenied(f"Daily {action} limit exceeded")

    # Atomically sync PostgreSQL DailyUsage immediately
    field = ACTION_FIELD_MAP.get(action, action)
    record_usage(user, field, count=count)


def record_usage(user, field, count=1):
    if count <= 0:
        return
    today = timezone.now().date()
    DailyUsage.objects.get_or_create(user=user, date=today)
    DailyUsage.objects.filter(user=user, date=today).update(**{field: F(field) + count})