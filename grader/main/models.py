from __future__ import unicode_literals
#from django.contrib.auth.models import User
from django.db import models

from django.db import models
from django.contrib.auth.models import (
    BaseUserManager, AbstractBaseUser
)


class MyUserManager(BaseUserManager):
    def create_user(self, email, uid, name, password):
        """
        Creates and saves a User with the given email, date of
        birth and password.
        """
        if not uid:
            raise ValueError('Users must have a university id')

        user = self.model(
            email = email,
            uid = uid,
            name = name,
        )
        user.is_admin = False

        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, uid, name, password):
        """
        Creates and saves a superuser with the given email, date of
        birth and password.
        """
        user = self.create_user(
            email,
            uid,
            name,
            password=password,
        )
        user.is_admin = True
        user.save(using=self._db)
        return user


class MyUser(AbstractBaseUser):
    email = models.EmailField(unique=True)
    uid = models.CharField(
        verbose_name='university id',
        max_length=9,
        unique=True,
    )
    name = models.CharField(max_length=50)
    is_active = models.BooleanField(default=True)
    is_admin = models.BooleanField()

    objects = MyUserManager()

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['name', 'uid']

    def get_full_name(self):
        # The user is identified by their email address
        return self.name

   # def get_short_name(self):
        # The user is identified by their email address
       # return self.first_name

    def __str__(self):              # __unicode__ on Python 2
        return self.email

    def has_perm(self, perm, obj=None):
        "Does the user have a specific permission?"
        # Simplest possible answer: Yes, always
        return True

    def has_module_perms(self, app_label):
        "Does the user have permissions to view the app `app_label`?"
        # Simplest possible answer: Yes, always
        return True

    @property
    def is_staff(self):
        "Is the user a teacher or a student?"
        # Simplest possible answer: All admins are staff
        return self.is_admin
    
# Create your models here.
