import asyncio
import threading
import os  # Add this for the widget script function
from django.shortcuts import render
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
from asgiref.sync import sync_to_async

# Create your views here.

def run_async_task(coroutine):
    """Helper function to run an async task in the background"""
    async def wrapper():
        await coroutine
    
    loop = asyncio.new_event_loop()
    threading.Thread(target=lambda: asyncio.run(wrapper())).start()

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
                website = Website.objects.get(site_key=site_key)
                data['website'] = website.id  # Add website ID to data
            except Website.DoesNotExist:
                return Response({"error": "Invalid site key"}, status=status.HTTP_400_BAD_REQUEST)
        
        serializer = IssueSerializer(data=data)
        if serializer.is_valid():
            issue = serializer.save()
            
            # Process the issue using the synchronous handler
            run_async_task(sync_to_async(handle_issue_sync)(issue.id))
            
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
        website = Website.objects.get(site_key=site_key)
        
        # Read the widget template
        with open(os.path.join(settings.BASE_DIR, 'static', 'js', 'widget-template.js'), 'r') as f:
            script_template = f.read()
            
        # Replace placeholder with actual site key
        script = script_template.replace('{{site_key}}', str(site_key))
        
        return HttpResponse(script, content_type='application/javascript')
    except Website.DoesNotExist:
        return HttpResponse('console.error("Invalid site key");', content_type='application/javascript')
