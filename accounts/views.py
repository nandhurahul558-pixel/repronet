from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from .models import User


def home_view(request):
    """Home/Landing page view"""
    if request.user.is_authenticated:
        if request.user.is_student:
            return redirect('student_dashboard')
        elif request.user.is_admin or request.user.is_superuser:
            return redirect('admin_dashboard')
    return render(request, 'accounts/home.html')


def student_signup_view(request):
    if request.user.is_authenticated:
        if request.user.is_student:
            return redirect('student_dashboard')
        return redirect('admin_dashboard')

    if request.method == 'POST':
        full_name = request.POST.get('full_name', '').strip()
        roll_number = request.POST.get('roll_number', '').strip()
        email = request.POST.get('email', '').strip()
        phone_number = request.POST.get('phone_number', '').strip()
        password = request.POST.get('password', '')
        confirm_password = request.POST.get('confirm_password', '')

        if not full_name:
            messages.error(request, 'Full name is required.')
            return render(request, 'accounts/student_signup.html')

        if not roll_number:
            messages.error(request, 'Roll number is required.')
            return render(request, 'accounts/student_signup.html')

        if password != confirm_password:
            messages.error(request, 'Passwords do not match.')
            return render(request, 'accounts/student_signup.html')

        if len(password) < 8:
            messages.error(request, 'Password must be at least 8 characters long.')
            return render(request, 'accounts/student_signup.html')

        if User.objects.filter(roll_number=roll_number).exists():
            messages.error(request, 'A student with this roll number already exists.')
            return render(request, 'accounts/student_signup.html')

        if email and User.objects.filter(email__iexact=email).exists():
            messages.error(request, 'An account with this email already exists.')
            return render(request, 'accounts/student_signup.html')

        name_parts = full_name.split(maxsplit=1)
        first_name = name_parts[0]
        last_name = name_parts[1] if len(name_parts) > 1 else ''

        user = User.objects.create_user(
            username=roll_number,
            first_name=first_name,
            last_name=last_name,
            email=email,
            roll_number=roll_number,
            phone_number=phone_number,
            is_student=True,
            is_admin=False,
            password=password,
        )

        login(request, user)
        messages.success(request, 'Account created successfully. Welcome!')
        return redirect('student_dashboard')

    return render(request, 'accounts/student_signup.html')

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
