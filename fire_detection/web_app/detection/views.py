from django.shortcuts import render, redirect
from django.http import HttpResponse
from django.contrib.auth.forms import UserCreationForm

from django.contrib.auth import authenticate, login, logout
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from django.shortcuts import get_object_or_404, redirect

from .forms import CreateUserForm

from .filters import DetectionFilter

from .models import UploadAlert

from rest_framework.authtoken.models import Token

import os

from django.conf import settings

# Handles the registration page
def registerPage(request):

    if request.user.is_authenticated:
        return redirect('home')
    else:
        form = CreateUserForm()
        if request.method == 'POST':
            form = CreateUserForm(request.POST)
            if form.is_valid():
                form.save()
                user = form.cleaned_data.get('username')
                messages.success(request, 'Account was successfully created for ' + user)

                return redirect('login')

        context = {'form':form}
        return render(request, 'detection/register.html', context)

# Handles the login page
def loginPage(request):
    if request.user.is_authenticated:
        return redirect('home')
    else:
        if request.method == 'POST':
            username = request.POST.get('username')
            password =request.POST.get('password')

            user = authenticate(request, username=username, password=password)

            if user is not None:
                login(request, user)
                return redirect('home')
            else:
                messages.info(request, 'Username OR password is incorrect')

        context = {}
        return render(request, 'detection/login.html', context)

# Handles the logout
def logoutUser(request):
    logout(request)
    return redirect('login')

# Handles the dashboard page
@login_required(login_url='login')
def home(request):


    token = Token.objects.get(user=request.user)

    uploadAlert = UploadAlert.objects.filter(user_ID = token)

    myFilter = DetectionFilter(request.GET, queryset=uploadAlert)
    uploadAlert = myFilter.qs

    context = {'myFilter':myFilter, 'uploadAlert':uploadAlert}

    return render(request, 'detection/dashboard.html', context)

# Handles the alert page
def alert(request,pk):
    print("OK")
    uploadAlert = UploadAlert.objects.filter(image = str(pk) + ".jpg")
    myFilter = DetectionFilter(request.GET, queryset=uploadAlert)
    uploadAlert = myFilter.qs

    context = {'myFilter':myFilter, 'uploadAlert':uploadAlert}
    print("Context:",context)
    return render(request, 'detection/alert.html', context)

def delete_alert(request, pk):
    alert = get_object_or_404(UploadAlert, id=pk)
    image_filename = str(alert.image) 
    image_path = os.path.join(settings.MEDIA_ROOT, image_filename)
    print(image_path)
    if os.path.exists(image_path):
        os.remove(image_path)
        print('Image deleted successfully!')
    else:
        print('Image does not exist!')
    if request.method == 'POST':

        alert.delete()
        messages.success(request, 'Delete Success!')
    return redirect('home')