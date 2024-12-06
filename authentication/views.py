from django.shortcuts import render, redirect
from django.contrib.auth.models import User
from django.contrib.auth import authenticate, login, logout
from django.contrib import messages

def register_user(request):
    if request.method == 'POST':
        username = request.POST['username']
        email = request.POST['email']
        password = request.POST['password']
        confirm_password = request.POST['confirm_password']

        if password == confirm_password:
            if User.objects.filter(username=username).exists():
                messages.error(request, "Username already exists.")
            elif User.objects.filter(email=email).exists():
                messages.error(request, "Email already registered.")
            else:
                user = User.objects.create_user(username=username, email=email, password=password)
                user.save()
                messages.success(request, "Registration successful. Please log in.")
                return redirect('login')
        else:
            messages.error(request, "Passwords do not match.")
    return render(request, 'authentication/register.html')

def login_user(request):
    if request.method == 'POST':
        username = request.POST['username']
        password = request.POST['password']
        user = authenticate(request, username=username, password=password)
        if user is not None:
            login(request, user)
            return redirect('home')  # Redirect to the QA app's home page
        else:
            messages.error(request, "Invalid username or password.")
    return render(request, 'authentication/login.html')

def logout_view(request):
    logout(request)
    messages.success(request, "You have been logged out.")
    return redirect('login')
