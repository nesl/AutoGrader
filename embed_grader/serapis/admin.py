from django.contrib import admin
from serapis.models import UserProfile, Course, Assignment

# Register your models here.
admin.site.register(UserProfile)
admin.site.register(Course)
admin.site.register(Assignment)
