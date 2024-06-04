from django import forms
from django.contrib.auth.models import User
from django.contrib.auth.forms import UserCreationForm, UserChangeForm, PasswordChangeForm
from django.contrib.auth.forms import AuthenticationForm
from .models import *
from django.core.exceptions import ValidationError

# User Registration
class UserRegistrationForm(UserCreationForm):
    first_name = forms.CharField(max_length=30, required=True)
    last_name = forms.CharField(max_length=30, required=True)
    phone = forms.CharField(max_length=10, required=True)
    email = forms.EmailField(max_length=254, required=True)

    class Meta:
        model = User
        fields = ('username', 'first_name', 'last_name', 'email', 'password1', 'password2', 'phone')

    def save(self,commit=True):
        user=super(UserRegistrationForm, self).save(commit=False)
        user.first_name=self.cleaned_data['first_name']
        user.last_name=self.cleaned_data['last_name']
        user.phone=self.cleaned_data['phone']
        user.email=self.cleaned_data['email']

        if commit:
            user.save()
        return user

# User Login
class UserAuthenticationForm(AuthenticationForm):
    class Meta:
        model = User
        fields = ['username', 'password']

class EditProfileForm(UserChangeForm):
    class Meta:
        model = User
        fields=['email','first_name','last_name','password']


class UserProfileForm(forms.ModelForm):
    class Meta:
        model = UserProfile
        fields = ['phone']

class AdministratorForm(forms.Form):
    access_code = forms.IntegerField(label='Access Code')


