import threading
import os  # Add this for the widget script function
from django.shortcuts import render, redirect, get_object_or_404
from django.http import JsonResponse, HttpResponse
from django.views.decorators.csrf import csrf_exempt
from rest_framework.parsers import JSONParser
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework import status
from .models import Issue, Website
from .serializers import IssueSerializer, WebsiteSerializer
# Import both async and sync handlers
from .issueHandler import handle_new_issue, handle_issue_sync
from django.conf import settings
from django.contrib.auth.models import User
from django.contrib import messages
from django.contrib.auth import login
from django.contrib.auth.decorators import login_required
from django.core.exceptions import ValidationError
import uuid

# Create your views here.

def run_async_task(func, *args, **kwargs):
    """Run a synchronous task in a background thread."""
    threading.Thread(target=func, args=args, kwargs=kwargs, daemon=True).start()

@csrf_exempt  # Exempt from CSRF for cross-origin requests
@api_view(['POST'])
def create_issue(request):
    """Create a new issue from JSON data"""
    if request.method == 'POST':
        data = request.data.copy()
        
        # Remove site_key from data before passing to serializer
        site_key = data.pop('site_key', None)
        if site_key:
            try:
                uuid.UUID(str(site_key))
                website = Website.objects.get(site_key=site_key)
                data['website'] = website.id
            except (Website.DoesNotExist, ValueError, ValidationError, AttributeError, TypeError):
                return Response({"error": "Invalid site key"}, status=status.HTTP_400_BAD_REQUEST)
        
        serializer = IssueSerializer(data=data)
        if serializer.is_valid():
            issue = serializer.save()
            
            # Process the issue using the synchronous handler
            run_async_task(handle_issue_sync, issue.id)
            
            return Response({
                "message": "Issue created successfully and being processed",
                "issue": serializer.data
            }, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

@api_view(['GET', 'POST'])
def website_list(request):
    """
    List all websites or create a new website
    """
    if request.method == 'GET':
        if request.user.is_authenticated:
            # If user is authenticated, show only their websites
            websites = Website.objects.filter(user=request.user)
        else:
            # Otherwise show all (you might want to restrict this)
            websites = Website.objects.all()
            
        serializer = WebsiteSerializer(websites, many=True)
        return Response(serializer.data)
    
    elif request.method == 'POST':
        serializer = WebsiteSerializer(data=request.data)
        if serializer.is_valid():
            website = serializer.save()
            
            # Associate with user if authenticated
            if request.user.is_authenticated:
                website.user = request.user
                website.save()   
            return Response({
                'message': 'Website created successfully',
                'website': WebsiteSerializer(website).data
            }, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

def get_widget_script(request, site_key):
    try:
        Website.objects.get(site_key=site_key)
        script_path = os.path.join(settings.BASE_DIR, 'static', 'main.js')
        with open(script_path, 'r', encoding='utf-8') as f:
            script = f.read()
        return HttpResponse(script, content_type='application/javascript')
    except Website.DoesNotExist:
        return HttpResponse('console.error("Invalid site key");', content_type='application/javascript')
    except FileNotFoundError:
        return HttpResponse('console.error("Widget script not found");', content_type='application/javascript')

def register_view(request):
    """
    View for handling user registration
    """
    if request.user.is_authenticated:
        return redirect('dashboard')  # Redirect if already logged in
    
    if request.method == "POST":
        username = request.POST.get('username')
        email = request.POST.get('email')
        password1 = request.POST.get('password1')
        password2 = request.POST.get('password2')
        terms = request.POST.get('terms')
        
        # Validation
        if not terms:
            messages.error(request, "You must accept the Terms of Service and Privacy Policy.")
            return render(request, 'register.html')
            
        if password1 != password2:
            messages.error(request, "Passwords don't match.")
            return render(request, 'register.html')
        
        if len(password1) < 8:
            messages.error(request, "Password must be at least 8 characters long.")
            return render(request, 'register.html')
        
        if User.objects.filter(username=username).exists():
            messages.error(request, "Username is already taken.")
            return render(request, 'register.html')
        
        if User.objects.filter(email=email).exists():
            messages.error(request, "Email is already registered.")
            return render(request, 'register.html')
        
        # Create user
        try:
            user = User.objects.create_user(username=username, email=email, password=password1)
            
            # Log the user in
            login(request, user)
            messages.success(request, "Registration successful! Welcome to BugHead.")
            return redirect('dashboard')
        except Exception as e:
            messages.error(request, f"An error occurred during registration: {str(e)}")
    
    return render(request, 'register.html')

@login_required
def dashboard(request):
    """
    Dashboard view for authenticated users to manage and view all websites
    """
    # Get all websites (not just the user's)
    all_websites = Website.objects.all().order_by('-create_at')
    print(all_websites)
    return render(request, 'dashboard.html', {
        'all_websites': all_websites
    })

@login_required
def website_detail(request, site_key):
    """
    View for managing a specific website and getting embed code
    """
    website = get_object_or_404(Website, site_key=site_key, user=request.user)
    
    # Get all issues reported for this website
    # Using 'id' for ordering instead of 'created_at'
    issues = Issue.objects.filter(website=website).order_by('-id')  # Changed from 'created_at' to 'id'
    
    # Generate widget embed code for this website
    embed_code = f'''
    <link rel="stylesheet" href="main.css">
    <div id="issue-tracker" data-site-key="{site_key}"></div>
  <script src="main.js"></script>
'''
    
    return render(request, 'websiteDetail.html', {
        'website': website,
        'issues': issues,
        'embed_code': embed_code
    })

@login_required
def add_website(request):
    """
    View for adding a new website
    """
    if request.method == "POST":
        owner = request.POST.get('owner')
        website_link = request.POST.get('website_link')
        github_repo = request.POST.get('github_repo')
        
        # Validate inputs
        if not all([owner, website_link, github_repo]):
            messages.error(request, "All fields are required.")
            return render(request, 'add_website.html')
        
        try:
            # Create new website
            website = Website.objects.create(
                user=request.user,
                owner=owner,
                websitelink=website_link,
                gitHubRepo=github_repo
            )
            
            messages.success(request, f"Website added successfully! Your site key is: {website.site_key}")
            return redirect('website_detail', site_key=website.site_key)
        
        except Exception as e:
            messages.error(request, f"An error occurred: {str(e)}")
    
    return render(request, 'add_website.html')

@login_required
def delete_website(request, site_key):
    """
    View for deleting a website
    """
    website = get_object_or_404(Website, site_key=site_key, user=request.user)
    
    if request.method == "POST":
        website_name = website.websitelink
        website.delete()
        messages.success(request, f"Website '{website_name}' has been deleted.")
        return redirect('dashboard')
    
    return render(request, 'delete_website_confirm.html', {
        'website': website
    })

# def website_list(request):
#     websites = Website.objects.all()
#     return render(request, 'website_list.html', {'websites': websites})