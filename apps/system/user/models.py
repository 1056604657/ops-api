from django.db import models
from django.contrib.auth.models import (BaseUserManager, AbstractBaseUser)


class UserInfoManager(BaseUserManager):
    def create_user(self, password=None, **kwargs):
        if not kwargs:
            raise ValueError('Users must have an username address')

        user = self.model(**kwargs)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, **kwargs):
        user = self.create_user(**kwargs)
        user.is_admin = True
        user.save(using=self._db)
        return user


class UserInfo(AbstractBaseUser):
    username = models.CharField(verbose_name='username', max_length=128, unique=True)
    email = models.EmailField(verbose_name='email', max_length=255, null=True, blank=True, unique=True)
    name = models.CharField(max_length=128, null=True, blank=True)
    is_active = models.BooleanField(verbose_name='是否可用', default=True)
    is_admin = models.BooleanField(verbose_name='是否管理员', default=False)
    create_date = models.DateTimeField(auto_now_add=True, blank=True, null=True)
    update_date = models.DateTimeField(blank=True, null=True, auto_now=True)
    objects = UserInfoManager()

    USERNAME_FIELD = 'username'
    REQUIRED_FIELDS = ['name', 'email']

    def get_full_name(self):
        return self.username

    def get_short_name(self):
        return self.username

    def __unicode__(self):  # __unicode__ on Python 2
        return self.username

    def has_perm(self, perm, obj=None):
        if self.is_active and self.is_admin:
            return True

    def has_perms(self, perm, obj=None):
        return True

    def has_module_perms(self, app_label):
        return True

    @property
    def is_staff(self):
        return self.is_admin

    class Meta:
        db_table = 'system_user'