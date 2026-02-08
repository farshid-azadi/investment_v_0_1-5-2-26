from django.contrib.auth.models import BaseUserManager

class CustomUserManager(BaseUserManager):
    """
    Custom user manager where mobile is the unique identifier
    for authentication (optional) or just a required field.
    Here we keep username as main auth but ensure mobile is handled.
    """
    def create_user(self, username, mobile, password=None, **extra_fields):
        if not username:
            raise ValueError('The Username field must be set')
        if not mobile:
            raise ValueError('The Mobile field must be set')
        
        # نرمال‌سازی و ساخت آبجکت
        user = self.model(username=username, mobile=mobile, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, username, mobile, password=None, **extra_fields):
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)
        extra_fields.setdefault('is_active', True)

        if extra_fields.get('is_staff') is not True:
            raise ValueError('Superuser must have is_staff=True.')
        if extra_fields.get('is_superuser') is not True:
            raise ValueError('Superuser must have is_superuser=True.')

        return self.create_user(username, mobile, password, **extra_fields)
