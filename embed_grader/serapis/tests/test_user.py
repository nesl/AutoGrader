from django.test import TestCase
from django.contrib.auth.models import User
from serapis.models import UserProfile
from django.db.utils import IntegrityError

class UserTestCase(TestCase):
    def setUp(self):
        defaultUser = User.objects.create_user('xihan94', email='xihan94@ucla.edu', password='biubiubiu');
        defaultUser.first_name = 'Xi'
        defaultUser.last_name = 'Han'
        defaultUser.save()

        defaultUserProfile = UserProfile(user=defaultUser, uid='504136747')
        defaultUserProfile.save()

        defaultUser.is_active = True
        defaultUser.save()


    def test_creating_user_with_duplicate_username_should_fail(self):
        self.assertRaises(IntegrityError, User.objects.create_user, 'xihan94', email='xihanmeow@ucla.edu', password='biubiubiu')

    def test_creating_user_with_empty_username_should_fail(self):
        self.assertRaises(ValueError, User.objects.create_user, '', email='xihanmeow@ucla.edu', password='biubiubiu')

    # These checks are done in form level
    # def test_creating_user_with_duplicate_email_should_fail(self):
    # def test_creating_user_with_empty_email_should_fail(self):  