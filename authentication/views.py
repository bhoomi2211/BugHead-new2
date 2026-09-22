from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login, logout
from django.contrib import messages
from django.contrib.auth.models import User
from django.contrib.auth.decorators import login_required
from django.views.decorators.csrf import ensure_csrf_cookie
from Issuecreator.models import Website

# Create your views here.
def login_view(request):
    """
    View for handling user login
    """
    if request.user.is_authenticated:
        return redirect('dashboard')  # Redirect if already logged in
    
    if request.method == "POST":
        username = request.POST.get('username')
        password = request.POST.get('password')
        remember_me = request.POST.get('remember_me')
        
        user = authenticate(request, username=username, password=password)
        
        if user is not None:
            login(request, user)
            
            # Set session expiry if remember_me is not checked
            if not remember_me:
                request.session.set_expiry(0)
                
            # Redirect to next parameter if provided, otherwise dashboard
            next_url = request.GET.get('next', 'dashboard')
            return redirect(next_url)
        else:
            messages.error(request, "Invalid username or password.")
    
    return render(request, 'login.html')

def register_view(request):
    """
    View for handling user registration
    """
    template_name = 'signup.html' if request.path.rstrip('/').endswith('signup') else 'register.html'

    if request.user.is_authenticated:
        return redirect('dashboard')

    if request.method == "POST":
        username = request.POST.get('username') or request.POST.get('name')
        email = request.POST.get('email')
        password1 = request.POST.get('password1') or request.POST.get('password')
        password2 = request.POST.get('password2') or request.POST.get('confirm-password')

        if not username or not email or not password1 or not password2:
            messages.error(request, "All fields are required.")
            return render(request, template_name)

        if password1 != password2:
            messages.error(request, "Passwords don't match.")
            return render(request, template_name)

        if User.objects.filter(username=username).exists():
            messages.error(request, "Username is already taken.")
            return render(request, template_name)

        if User.objects.filter(email=email).exists():
            messages.error(request, "Email is already registered.")
            return render(request, template_name)

        user = User.objects.create_user(username=username, email=email, password=password1)
        login(request, user)
        messages.success(request, "Registration successful!")
        return redirect('dashboard')

    return render(request, template_name)

def logout_view(request):
    """
    View for handling user logout
    """
    logout(request)
    messages.success(request, "You have been logged out.")
    return redirect('login')

@login_required
def dashboard(request):
    """
    Dashboard view (requires login)
    """
    # Fetch websites added by the current user
    websites = Website.objects.filter(user=request.user).order_by('-create_at')
    return render(request, 'dashboard.html', {
        'user': request.user,
        'websites': websites
    })

@login_required
def profile(request):
    """
    User profile view (requires login)
    """
    if request.method == "POST":
        # Update profile logic here
        user = request.user
        user.first_name = request.POST.get('first_name', user.first_name)
        user.last_name = request.POST.get('last_name', user.last_name)
        user.email = request.POST.get('email', user.email)
        user.save()
        
        messages.success(request, "Profile updated successfully!")
        return redirect('profile')
    
    return render(request, 'profile.html', {
        'user': request.user
    })


