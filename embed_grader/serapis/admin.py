from django.contrib import admin
from serapis.models import *
from django.contrib.auth.models import Permission

# Register your models here.
#Built-in models
admin.site.register(Permission)

#Our models
admin.site.register(UserProfile)
admin.site.register(Course)
admin.site.register(Assignment)
admin.site.register(CourseUserList)
admin.site.register(AssignmentTask)
admin.site.register(Submission)
admin.site.register(SubmissionFile)
admin.site.register(TaskGradingStatus)

admin.site.register(HardwareType)
admin.site.register(HardwareTypePin)
admin.site.register(HardwareDevice)
admin.site.register(Testbed)
admin.site.register(TestbedType)
admin.site.register(TestbedHardwareList)
admin.site.register(TestbedTypeWiring)
