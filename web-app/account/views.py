from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required

from .forms import *
from django.http import *
from django.views.decorators.csrf import csrf_exempt
from django.contrib import messages
from django.contrib.auth import authenticate, logout
from django.contrib.auth import login as auth_login

from django.urls import reverse
from account.models import UserProfile
from django.db.models import Q
from account.views import *

import config
from config import administrator_key


# Allow users to register
@csrf_exempt
def user_register(request):
    if request.method == 'POST':
        form = UserRegistrationForm(request.POST)
        if form.is_valid():
            # Create a User object
            user = form.save()
            password = form.cleaned_data.get('password1')
            user=authenticate(username=user.username, password=password)
            if user is not None:
                auth_login(request, user)
            
            # Create a UserProfile object
            UserProfile.objects.create(
                user=user,
                username=user.username,
                first_name=form.cleaned_data['first_name'],
                last_name=form.cleaned_data['last_name'],
                phone=form.cleaned_data['phone'],
                email=form.cleaned_data['email'],
            )
            messages.success(request, "You have successfully registered")

            return redirect('login')
    else:
        form = UserRegistrationForm()

    return render(request, 'account/register.html', {'form':form})


# Allow users to sign-in -> authentication
@csrf_exempt
def user_login(request):
    if request.method == 'POST':
        form = UserAuthenticationForm(request, data = request.POST)
        if form.is_valid():
            username = form.cleaned_data['username']
            password = form.cleaned_data['password']
            user = authenticate(request, username=username, password=password)
            print("User authenticated:", user is not None)
            if user is not None:
                auth_login(request, user)
                print("User logged in")
                return redirect('dashboard')
    else:
        form = UserAuthenticationForm()

    return render(request, 'account/login.html', {'form': form})

# Allow user to logout in the dashboard
@login_required
@csrf_exempt    
def user_logout(request):
    if request.method == 'POST':
        logout(request)
        return redirect('login')
    else:
        return render(request, 'account/login.html')

@login_required
@csrf_exempt
def userprofile(request):
    user_profile = UserProfile.objects.get(user=request.user)
    context = {
        'user': request.user,
        'user_profile': user_profile
    }
    return render(request, 'account/userprofile.html', context)


@login_required
@csrf_exempt
def edit_user_profile(request):
    if request.method == 'POST':
        user_form = EditProfileForm(request.POST, instance=request.user)
        profile_form = UserProfileForm(request.POST, instance=request.user.userprofile)
        if user_form.is_valid() and profile_form.is_valid():
            # Save the User form
            updated_user = user_form.save()
            # Sync the fields from User to UserProfile if they are updated
            profile_instance = profile_form.instance
            if 'first_name' in user_form.changed_data:
                profile_instance.first_name = updated_user.first_name
            if 'last_name' in user_form.changed_data:
                profile_instance.last_name = updated_user.last_name
            if 'email' in user_form.changed_data:
                profile_instance.email = updated_user.email
            # Save the UserProfile form
            profile_form.save()
            return redirect('userprofile')
    else:
        user_form = EditProfileForm(instance=request.user)
        profile_form = UserProfileForm(instance=request.user.userprofile)
    return render(request, 'account/edit_user_profile.html', {
        'user_form': user_form,
        'profile_form': profile_form
    })

@login_required
@csrf_exempt
def dashboard_view(request):
    user_profile = UserProfile.objects.get(user=request.user)
    return render(request, 'account/dashboard.html', {'user_profile': user_profile})

@login_required
@csrf_exempt
def administrator_register(request):
    user_profile = UserProfile.objects.get(user=request.user)
    if user_profile.is_administrator == True:
        messages.success(request, 'You are already an administrator')
        return redirect('dashboard')
    if request.method == 'POST':
        form = AdministratorForm(request.POST)
        if form.is_valid() and form.cleaned_data['access_code'] == administrator_key:
            user_profile = UserProfile.objects.get(user=request.user)
            user_profile.is_administrator = True
            user_profile.save()
            messages.success(request, 'Registration as an administrator was successful!')
            messages.success(request, 'Please switch to the administrator view when needed')
            return redirect('dashboard')
        else:
            messages.error(request, 'Wrong Access Code')
    else:
        form = AdministratorForm()
    return render(request, 'account/administrator_register.html', {'form': form})


