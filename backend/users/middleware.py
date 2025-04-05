from django.shortcuts import redirect
from django.urls import reverse

class AuthenticationMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        # Code to be executed for each request before the view is called

        # List of URLs that should not be accessible to logged-in users
        restricted_urls = [
            reverse('landing_page'),  # Use the correct URL name here
            reverse('login'),
            reverse('register'),
        ]

        # Check if the user is authenticated and trying to access restricted URLs
        if request.user.is_authenticated and request.path in restricted_urls:
            return redirect('profile')

        response = self.get_response(request)
        return response