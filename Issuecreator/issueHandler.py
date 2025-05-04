import os
import json
import logging
from typing import Dict, List, Any, Optional
import requests
import google.generativeai as genai
from django.conf import settings
from .models import Issue, Website
from asgiref.sync import sync_to_async  # Add this import

# Configure logging
logger = logging.getLogger(__name__)

# Configure API keys
GITHUB_TOKEN = os.environ.get('GITHUB_TOKEN') or settings.GITHUB_TOKEN
GEMINI_API_KEY = os.environ.get('GEMINI_API_KEY') or settings.GEMINI_API_KEY

# Configure Gemini
genai.configure(api_key=GEMINI_API_KEY)

class IssueHandler:
    """
    Utility class to handle issue processing and GitHub integration
    """
    
    @staticmethod
    def extract_repo_info(github_url: str) -> tuple:
        """
        Extract owner and repo name from GitHub URL
        
        Args:
            github_url: GitHub repository URL
            
        Returns:
            tuple: (owner, repo_name)
        """
        logger.debug(f"Extracting repo info from URL: {github_url}")
        # Remove trailing slash if present
        if github_url.endswith('/'):
            github_url = github_url[:-1]
            
        # Extract owner and repo from URL
        parts = github_url.split('/')
        if 'github.com' in parts:
            idx = parts.index('github.com')
            if len(parts) >= idx + 3:
                owner, repo = parts[idx + 1], parts[idx + 2]
                logger.debug(f"Successfully extracted owner: {owner}, repo: {repo}")
                return owner, repo
        
        # Return None if unable to parse
        logger.warning(f"Failed to extract repo info from URL: {github_url}")
        return None, None
    
    @staticmethod
    async def enhance_issue_with_ai(issue_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Use Gemini AI to enhance issue description and generate tags
        
        Args:
            issue_data: Dictionary containing issue data
            
        Returns:
            Dict with enhanced description and suggested tags
        """
        logger.info(f"Enhancing issue with AI: {issue_data.get('bugArea')}")
        
        # Construct a prompt for Gemini
        prompt = f"""
        I have a bug report with the following details:
        
        Bug Area: {issue_data.get('bugArea', 'Not specified')}
        Priority: {issue_data.get('priority', 'Not specified')}
        Issue Detail: {issue_data.get('IssueDetail', 'Not specified')}
        Device: {issue_data.get('Device', 'Not specified')}
        Browser: {issue_data.get('Browse', 'Not specified')}
        Operating System: {issue_data.get('OperatingSystem', 'Not specified')}
        
        Please:
        1. Write a clear and detailed GitHub issue description based on this information
        2. Suggest 2-4 appropriate tags/labels for categorizing this issue
        3. Assign a severity level (low, medium, high, critical)
        
        Format your response as JSON with keys: "description", "tags", "severity"
        """
        
        try:
            logger.debug("Sending request to Gemini AI")
            # Generate response from Gemini
            model = genai.GenerativeModel('gemini-1.5-pro')
            response = await model.generate_content_async(prompt)
            logger.debug("Received response from Gemini AI")
            
            # Parse the JSON response
            try:
                logger.debug(f"Parsing AI response: {response.text[:100]}...")
                result = json.loads(response.text)
                enhanced_data = {
                    'enhanced_description': result.get('description', issue_data.get('IssueDetail', '')),
                    'suggested_tags': result.get('tags', []),
                    'severity': result.get('severity', 'medium')
                }
                logger.info(f"AI enhancement successful. Tags: {enhanced_data['suggested_tags']}, Severity: {enhanced_data['severity']}")
                return enhanced_data
            except json.JSONDecodeError:
                logger.error(f"Failed to parse AI response as JSON: {response.text[:200]}")
                # Fallback if AI doesn't return valid JSON
                return {
                    'enhanced_description': issue_data.get('IssueDetail', ''),
                    'suggested_tags': ['bug'],
                    'severity': 'medium'
                }
                
        except Exception as e:
            logger.error(f"Error with AI enhancement: {str(e)}", exc_info=True)
            # Return original data if AI processing fails
            return {
                'enhanced_description': issue_data.get('IssueDetail', ''),
                'suggested_tags': ['bug'],
                'severity': 'medium'
            }
    
    @staticmethod
    def create_github_issue(repo_owner: str, repo_name: str, issue_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Create an issue in GitHub repository
        
        Args:
            repo_owner: GitHub repository owner
            repo_name: GitHub repository name
            issue_data: Enhanced issue data including description and tags
            
        Returns:
            Dict with response from GitHub API
        """
        logger.info(f"Creating GitHub issue in {repo_owner}/{repo_name}")
        url = f"https://api.github.com/repos/{repo_owner}/{repo_name}/issues"
        
        # Prepare headers for GitHub API
        headers = {
            'Authorization': f'token {GITHUB_TOKEN}',
            'Accept': 'application/vnd.github.v3+json'
        }
        
        # Format and enhance the issue title
        device_info = f" ({issue_data.get('Device', '')}/{issue_data.get('Browse', '')})"
        title = f"{issue_data.get('bugArea', 'Bug Report')}: {issue_data.get('IssueDetail', '')[:50]}"
        logger.debug(f"Issue title: {title}")
        
        # Prepare the issue body with enhanced description and device details
        body = f"""
## Description
{issue_data.get('enhanced_description', issue_data.get('IssueDetail', ''))}

## Environment
- **Device:** {issue_data.get('Device', 'Not specified')}
- **Browser:** {issue_data.get('Browse', 'Not specified')}
- **OS:** {issue_data.get('OperatingSystem', 'Not specified')}

## Priority
{issue_data.get('priority', 'Not specified')}

## Severity
{issue_data.get('severity', 'medium')}

---
*This issue was automatically created by BugHead.*
        """
        
        # Prepare the payload for GitHub API
        payload = {
            'title': title,
            'body': body,
            'labels': issue_data.get('suggested_tags', ['bug'])
        }
        logger.debug(f"GitHub API payload prepared with labels: {payload['labels']}")
        
        try:
            # Send request to GitHub API
            logger.debug(f"Sending request to GitHub API: {url}")
            response = requests.post(url, headers=headers, json=payload)
            
            if response.status_code >= 400:
                logger.error(f"GitHub API error: {response.status_code} - {response.text}")
                return {'error': f"GitHub API error: {response.status_code} - {response.text}"}
                
            response.raise_for_status()
            result = response.json()
            logger.info(f"GitHub issue created successfully: {result.get('html_url')}")
            return result
        except requests.exceptions.RequestException as e:
            logger.error(f"Error creating GitHub issue: {str(e)}", exc_info=True)
            if hasattr(e, 'response') and e.response:
                logger.error(f"Response: {e.response.text}")
            return {'error': str(e)}

    @classmethod
    async def process_issue(cls, issue_id: int) -> Dict[str, Any]:
        """
        Process an issue by enhancing it with AI and creating a GitHub issue
        
        Args:
            issue_id: ID of the issue in the database
            
        Returns:
            Dict with results of the processing
        """
        logger.info(f"Processing issue with ID: {issue_id}")
        try:
            # Get the issue from the database - use sync_to_async
            issue = await sync_to_async(Issue.objects.get)(id=issue_id)
            logger.debug(f"Found issue: {issue.bugArea}")
            
            # Get the associated website using the website foreign key - make it async
            website = None
            if hasattr(issue, 'site_key') and issue.site_key:
                try:
                    logger.debug(f"Looking up website by site_key: {issue.site_key}")
                    website = await sync_to_async(Website.objects.get)(site_key=issue.site_key)
                except Website.DoesNotExist:
                    logger.warning(f"Website with site_key {issue.site_key} not found")
                    pass
            
            # If no website found by site_key, use the website foreign key
            if not website:
                # Use sync_to_async for accessing the related website
                if not await sync_to_async(lambda: issue.website)(None):
                    logger.error("Issue is not associated with a website")
                    return {'error': 'Issue is not associated with a website'}
                
                # Get the website object safely
                website = await sync_to_async(lambda: issue.website)()
                logger.debug(f"Using website from foreign key: {website.owner}")
        
            # Extract repository information
            logger.debug(f"Extracting repo info from: {website.gitHubRepo}")
            repo_owner, repo_name = cls.extract_repo_info(website.gitHubRepo)
            if not repo_owner or not repo_name:
                logger.error(f"Invalid GitHub repository URL: {website.gitHubRepo}")
                return {'error': 'Invalid GitHub repository URL'}
            
            # Prepare issue data
            issue_data = {
                'bugArea': issue.bugArea,
                'priority': issue.priority,
                'IssueDetail': issue.IssueDetail,
                'Device': issue.Device,
                'Browse': issue.Browse,
                'OperatingSystem': issue.OperatingSystem
            }
            logger.debug(f"Prepared issue data: {issue_data}")
            
            # Enhance issue with AI
            logger.info("Enhancing issue with AI")
            enhanced_data = await cls.enhance_issue_with_ai(issue_data)
            issue_data.update(enhanced_data)
            
            logger.debug(f"Enhanced issue data: {enhanced_data}")
            
            # Create GitHub issue - wrap with sync_to_async if it contains any DB operations
            logger.info(f"Creating GitHub issue in {repo_owner}/{repo_name}")
            github_response = cls.create_github_issue(repo_owner, repo_name, issue_data)
            
            # Update issue with GitHub issue URL if successful
            if 'html_url' in github_response:
                github_url = github_response['html_url']
                logger.info(f"GitHub issue created successfully: {github_url}")
                # If you need to update the issue with the GitHub URL:
                # await sync_to_async(lambda: setattr(issue, 'github_url', github_url))()
                # await sync_to_async(issue.save)()
                return {
                    'success': True,
                    'message': 'GitHub issue created successfully',
                    'github_issue_url': github_url
                }
            else:
                error_msg = github_response.get('error', 'Unknown error')
                logger.error(f"Failed to create GitHub issue: {error_msg}")
                return {
                    'success': False,
                    'message': 'Failed to create GitHub issue',
                    'error': error_msg
                }
                
        except Issue.DoesNotExist:
            logger.error(f"Issue with ID {issue_id} not found")
            return {'error': f'Issue with ID {issue_id} not found'}
        except Website.DoesNotExist:
            logger.error("Associated website not found")
            return {'error': 'Associated website not found'}
        except Exception as e:
            logger.exception(f"Unexpected error processing issue {issue_id}: {str(e)}")
            return {'error': str(e)}


# Function to be called from views or tasks
async def handle_new_issue(issue_id):
    """
    Handle a newly created issue
    
    Args:
        issue_id: ID of the issue in the database
        
    Returns:
        Dict with results of the processing
    """
    logger.info(f"Handling new issue with ID: {issue_id}")
    result = await IssueHandler.process_issue(issue_id)
    logger.info(f"Issue processing completed: {result}")
    return result

# Create a synchronous version of the handler
def handle_issue_sync(issue_id):
    """
    Synchronous handler for issues
    """
    try:
        issue = Issue.objects.get(id=issue_id)
        website = issue.website
        
        if not website:
            logger.error("Issue is not associated with a website")
            return {'error': 'Issue is not associated with a website'}
            
        # Extract repository information
        logger.debug(f"Extracting repo info from: {website.gitHubRepo}")
        repo_owner, repo_name = IssueHandler.extract_repo_info(website.gitHubRepo)
        if not repo_owner or not repo_name:
            logger.error(f"Invalid GitHub repository URL: {website.gitHubRepo}")
            return {'error': 'Invalid GitHub repository URL'}
        
        # Prepare issue data
        issue_data = {
            'bugArea': issue.bugArea,
            'priority': issue.priority,
            'IssueDetail': issue.IssueDetail,
            'Device': issue.Device,
            'Browse': issue.Browse,
            'OperatingSystem': issue.OperatingSystem
        }
        logger.debug(f"Prepared issue data: {issue_data}")
        
        # Skip AI enhancement in synchronous function
        # We can't call an async function directly
        enhanced_data = {
            'enhanced_description': issue_data.get('IssueDetail', ''),
            'suggested_tags': ['bug'],
            'severity': 'medium'
        }
        issue_data.update(enhanced_data)
        
        logger.debug(f"Using basic issue data without AI enhancement")
        
        # Create GitHub issue
        logger.info(f"Creating GitHub issue in {repo_owner}/{repo_name}")
        github_response = IssueHandler.create_github_issue(repo_owner, repo_name, issue_data)
        
        # Update issue with GitHub issue URL if successful
        if 'html_url' in github_response:
            github_url = github_response['html_url']
            logger.info(f"GitHub issue created successfully: {github_url}")
            # If you need to update the issue with the GitHub URL:
            # issue.github_url = github_url
            # issue.save()
            return {
                'success': True,
                'message': 'GitHub issue created successfully',
                'github_issue_url': github_url
            }
        else:
            error_msg = github_response.get('error', 'Unknown error')
            logger.error(f"Failed to create GitHub issue: {error_msg}")
            return {
                'success': False,
                'message': 'Failed to create GitHub issue',
                'error': error_msg
            }
            
    except Exception as e:
        logger.exception(f"Error processing issue: {str(e)}")
        return {'error': str(e)}

# In your views.py, call it wrapped with sync_to_async
# @csrf_exempt
# @api_view(['POST'])
# def create_issue(request):
#     # ...
#     if serializer.is_valid():
#         issue = serializer.save()
        
#         # Run in background thread
#         run_async_task(sync_to_async(handle_issue_sync)(issue.id))
        
#         return Response({
#             "message": "Issue created successfully and being processed",
#             "issue": serializer.data
#         }, status=status.HTTP_201_CREATED)