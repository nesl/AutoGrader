from django.contrib import admin
from serapis.models import *
from django.contrib.auth.models import Permission, User, Group
from guardian.admin import GuardedModelAdmin
from guardian.shortcuts import assign_perm


# Register your models here.
#Built-in models
admin.site.register(Permission)

#Our models
admin.site.register(UserProfile)
admin.site.register(Course)
admin.site.register(Assignment)

class CourseUserListAdmin(admin.ModelAdmin):
    def save_model(self, request, obj, form, change):
        user = obj.user_fk
        course = obj.course_fk

        instructor_group_name = str(course.id) + "_Instructor_Group"
        student_group_name = str(course.id) + "_Student_Group"
        instructor_group = Group.objects.get(name=instructor_group_name)
        student_group = Group.objects.get(name=student_group_name)

        if obj.role == CourseUserList.ROLE_STUDENT:
            if instructor_group in user.groups.all():
                user.groups.remove(instructor_group)
            if student_group not in user.groups.all():
                user.groups.add(student_group)
        else:
            if instructor_group not in user.groups.all():
                user.groups.add(instructor_group)
            if student_group in user.groups.all():
                user.groups.remove(student_group)
        obj.save()


admin.site.register(CourseUserList, CourseUserListAdmin)
admin.site.register(AssignmentTask)
admin.site.register(Submission)
admin.site.register(SubmissionFile)
admin.site.register(TaskGradingStatus)
admin.site.register(AssignmentTaskFileSchema)
admin.site.register(AssignmentTaskFile)
admin.site.register(SubmissionFileSchema)
admin.site.register(TaskGradingStatusFileSchema)
admin.site.register(TaskGradingStatusFile)

admin.site.register(HardwareType)
admin.site.register(HardwareTypePin)
admin.site.register(HardwareDevice)
admin.site.register(Testbed)
admin.site.register(TestbedType)
admin.site.register(TestbedHardwareList)
admin.site.register(TestbedTypeWiring)
