from django.contrib.auth.models import User, Group, Permission, ContentType

g1=Group.objects.get(name='Instructor')
g2=Group.objects.get(name='TA')
g3=Group.objects.get(name='Student')
g4=Group.objects.get(name='Grader')


ct1=ContentType.objects.get(app_label='auth', model='user')
ct2=ContentType.objects.get(app_label='serapis', model='course')
ct3=ContentType.objects.get(app_label='serapis', model='assignment')

p1=Permission.objects.get(codename='view_membership', name='Can View Membership', content_type=ct1)
p2=Permission.objects.get(codename='add_course', name='Can Modify Courses', content_type=ct2)
p3=Permission.objects.get(codename='add_assignment', name='Can Modify Assignments', content_type=ct3)

g1.permissions.add(p1,p2,p3)
g2.permissions.add(p1)
