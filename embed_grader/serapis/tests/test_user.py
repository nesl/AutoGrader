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

        self.defaultUser = defaultUser
        self.defaultUserProfile = defaultUserProfile


    def test_creating_user_with_duplicate_username_should_fail(self):
        self.assertRaises(IntegrityError, User.objects.create_user, 'xihan94', email='xihanmeow@ucla.edu', password='biubiubiu')

    def test_creating_user_with_empty_username_should_fail(self):
        self.assertRaises(ValueError, User.objects.create_user, '', email='xihanmeow@ucla.edu', password='biubiubiu')

    # These checks are done in form level
    # def test_creating_user_with_duplicate_email_should_fail(self):
    # def test_creating_user_with_empty_email_should_fail(self):

    def test_creating_user_profile_with_none_user_object_should_fail(self):
        anotherUserProfile = UserProfile(user=None, uid='135798642')
        self.assertRaises(IntegrityError, anotherUserProfile.save)

    def test_creating_user_profile_with_none_uid_should_fail(self):
        anotherUser = User.objects.create_user('dummyuser', email='dummyuser@ucla.edu', password='biubiubiu');
        anotherUser.first_name = 'Dummy'
        anotherUser.last_name = 'User'
        anotherUser.save()

        anotherUserProfile = UserProfile(user=anotherUser, uid=None)
        self.assertRaises(IntegrityError, anotherUserProfile.save)

    def test_linking_multiple_profiles_to_a_user_should_fail(self):
        anotherUserProfile = UserProfile(user=self.defaultUser, uid='135798642')
        self.assertRaises(IntegrityError, anotherUserProfile.save)

    def test_creating_user_with_duplicate_uid_should_fail(self):
        anotherUser = User.objects.create_user('dummyuser', email='dummyuser@ucla.edu', password='biubiubiu');
        anotherUser.first_name = 'Dummy'
        anotherUser.last_name = 'User'
        anotherUser.save()

        anotherUserProfile = UserProfile(user=anotherUser, uid='504136747')
        self.assertRaises(IntegrityError, anotherUserProfile.save)