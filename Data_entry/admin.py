from django.contrib import admin
from .models import Student , Customer , Employee , CustomUser , History
# Register your models here.

admin.site.register(Student)
admin.site.register(Customer)
admin.site.register(Employee)
admin.site.register(CustomUser)
admin.site.register(History)