from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from .models import User

def student_login_view(request):
    if request.user.is_authenticated:
        if request.user.is_student:
            return redirect('student_dashboard')
        return redirect('admin_dashboard')

    if request.method == 'POST':
        roll_number = request.POST.get('roll_number')
        password = request.POST.get('password')
        
        # We can authenticate by username, so we must map roll_number to username
        try:
            user = User.objects.get(roll_number=roll_number, is_student=True)
            auth_user = authenticate(request, username=user.username, password=password)
            if auth_user is not None:
                login(request, auth_user)
                return redirect('student_dashboard')
            else:
                messages.error(request, 'Invalid credentials.')
        except User.DoesNotExist:
            messages.error(request, 'Student with this roll number does not exist.')
            
    return render(request, 'accounts/student_login.html')

def admin_login_view(request):
    if request.user.is_authenticated:
        if request.user.is_admin or request.user.is_superuser:
            return redirect('admin_dashboard')
        return redirect('student_dashboard')

    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        
        auth_user = authenticate(request, username=username, password=password)
        if auth_user is not None and (auth_user.is_admin or auth_user.is_superuser):
            login(request, auth_user)
            return redirect('admin_dashboard')
        else:
            messages.error(request, 'Invalid admin credentials.')
            
    return render(request, 'accounts/admin_login.html')

def logout_view(request):
    logout(request)
    return redirect('student_login')
