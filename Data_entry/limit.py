from datetime import datetime, time, timedelta
from django.utils import timezone
from django.core.exceptions import PermissionDenied
from redis import Redis
from .models import DailyUsage


redis = Redis()

LIMIT_LUA = """
local current = redis.call("INCR", KEYS[1])
if current == 1 then
  redis.call("EXPIRE", KEYS[1], ARGV[1])
end
if current > tonumber(ARGV[2]) then
  redis.call("DECR", KEYS[1])
  return -1
end
return current
"""

limit_script = redis.register_script(LIMIT_LUA)

def seconds_until_midnight():
    now = timezone.now()
    tomorrow = (now + timedelta(days=1)).date()
    midnight = datetime.combine(tomorrow, time.min).astimezone(now.tzinfo)
    return int((midnight - now).total_seconds())



def enforce(user, action, daily_limit):
    today = timezone.now().date()
    key = f"{action}:{user.id}:{today}"

    ttl = seconds_until_midnight()

    result = limit_script(
        keys=[key],
        args=[ttl, daily_limit],
    )

    if result == -1:
        raise PermissionDenied(f"Daily {action} limit exceeded")




def record_usage(user, field):
    today = timezone.now().date()
    usage, _ = DailyUsage.objects.get_or_create(user=user, date=today)

    setattr(usage, field, getattr(usage, field) + 1)
    usage.save(update_fields=[field])
