from django.db import models
from django.contrib.auth.models import User

# Create your models here.
class UserProfile(models.Model):
    # django内置了User，可能不需要再定义这么多？
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    username = models.CharField(max_length=20)
    first_name = models.CharField(max_length=20, default='Bob')
    last_name = models.CharField(max_length=20, default='Allen')
    phone = models.CharField(max_length=10, default='1234567890')
    email = models.EmailField(default='example@example.com')
    cash = models.BigIntegerField(default=1000000)
    is_administrator = models.BooleanField(default=False)

    
    def __str__(self):
        return self.user.username