from django.contrib import admin
from serapis.models import UserProfile, Course, Assignment
from django.contrib.auth.models import Permission

# Register your models here.
#Built-in models
admin.site.register(Permission)

#Our models
admin.site.register(UserProfile)
admin.site.register(Course)
admin.site.register(Assignment)
