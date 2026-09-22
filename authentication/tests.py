from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth.models import User

class RouteTests(TestCase):
    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(username="testuser", password="testpassword123", email="test@example.com")

    def test_public_routes(self):
        """Test public routes return 200"""
        public_urls = [
            'home',
            'Home',
            'issueForm',
            'devloperdashboard',
            'report-bug',
            'Bug-Tracker',
            'bug-tracker',
            'about',
            'add-website',
            'footer',
            'login',
            'register',
            'signup',
        ]
        for url_name in public_urls:
            response = self.client.get(reverse(url_name))
            self.assertEqual(response.status_code, 200, f"URL name '{url_name}' returned status {response.status_code} instead of 200")

    def test_auth_required_routes_redirect_when_logged_out(self):
        """Test auth-required routes redirect to login when not logged in"""
        auth_urls = [
            'dashboard',
            'profile',
        ]
        for url_name in auth_urls:
            response = self.client.get(reverse(url_name))
            self.assertEqual(response.status_code, 302, f"Auth required URL '{url_name}' did not redirect")
            self.assertIn('/login/', response.url)

    def test_auth_required_routes_when_logged_in(self):
        """Test auth-required routes return 200 when logged in"""
        self.client.login(username="testuser", password="testpassword123")
        auth_urls = [
            'dashboard',
            'profile',
        ]
        for url_name in auth_urls:
            response = self.client.get(reverse(url_name))
            self.assertEqual(response.status_code, 200, f"URL '{url_name}' returned status {response.status_code} instead of 200 when logged in")
