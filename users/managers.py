from django.contrib.auth.models import BaseUserManager
from django.db import models
from users.enums import UserTypeChoices


class AdminUserManager(BaseUserManager):
    def create_user(self, email, password=None, **extra_fields):
        if not email:
            raise ValueError('The Email field must be set')
        email = self.normalize_email(email)
        user = self.model(email=email, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, email, password=None, **extra_fields):
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)
        extra_fields.setdefault('type', UserTypeChoices.ADMIN)

        if extra_fields.get('is_staff') is not True:
            raise ValueError('Superuser must have is_staff=True.')
        if extra_fields.get('is_superuser') is not True:
            raise ValueError('Superuser must have is_superuser=True.')

        return self.create_user(email, password, **extra_fields)


class DriverManager(models.Manager):
    def get_queryset(self, *args, **kwargs):
        return super().get_queryset(*args, **kwargs).filter(type=UserTypeChoices.DRIVER)

    def create(self, **kwargs):
        kwargs.update({'type': UserTypeChoices.DRIVER})
        return super().create(**kwargs)


class GuardianManager(models.Manager):
    def get_queryset(self, *args, **kwargs):
        return super().get_queryset(*args, **kwargs).filter(type=UserTypeChoices.GUARDIAN)

    def create(self, **kwargs):
        kwargs.update({'type': UserTypeChoices.GUARDIAN})
        return super().create(**kwargs)
