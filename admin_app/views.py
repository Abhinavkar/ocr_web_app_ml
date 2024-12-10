from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login, logout
from django.contrib import messages
from .forms import AdminRegisterForm
from django.contrib.auth.decorators import login_required

def admin_register(request):
    if request.method == 'POST':
        form = AdminRegisterForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect('admin_app:admin_login')
    else:
        form = AdminRegisterForm()
    return render(request, 'admin_app/register.html', {'form': form})


def admin_login(request):
    """
    View to handle admin login.
    """
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        user = authenticate(request, username=username, password=password)

        if user is not None and user.is_staff:  # Ensure the user is an admin
            login(request, user)
            messages.success(request, f'Welcome back, {user.username}!')
            return redirect('admin_dashboard')  # Replace with your dashboard view name
        else:
            messages.error(request, 'Invalid credentials or you are not authorized as an admin.')

    return render(request, 'admin_app/login.html')


@login_required
def admin_dashboard(request):
    return render(request, 'admin_app/dashboard.html')



def admin_logout(request):
    logout(request)
    # Redirect to the admin login page after logout
    return redirect('admin_app:admin_login')