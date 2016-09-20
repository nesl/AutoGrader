from django.contrib import admin
from serapis.models import UserProfile, Course, Assignment, CourseUserList, AssignmentTask, Submission, SubmissionFile
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
