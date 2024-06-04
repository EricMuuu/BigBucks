from django import forms
from django.contrib.auth.models import User
from django.contrib.auth.forms import UserCreationForm, UserChangeForm, PasswordChangeForm
from django.contrib.auth.forms import AuthenticationForm
from .models import *
from django.core.exceptions import ValidationError

class BuySellForm(forms.Form):
    symbol = forms.CharField(label='Symbol', max_length=10)
    share_num = forms.IntegerField(label='Number of Shares')
