from django.contrib import admin
from .models import Student , Customer , Employee , CustomUser , History , UserSubscription,SubscriptionPlan,DailyUsage
# Register your models here.

admin.site.register(Student)
admin.site.register(Customer)
admin.site.register(Employee)
admin.site.register(CustomUser)
admin.site.register(History)
admin.site.register(UserSubscription)
admin.site.register(SubscriptionPlan)
admin.site.register(DailyUsage)