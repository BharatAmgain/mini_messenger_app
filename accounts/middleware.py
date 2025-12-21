from django.shortcuts import redirect
from django.conf import settings


class AuthRedirectMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        # Check if request is trying to access /auth/login/
        if request.path == '/auth/login/' or request.path.startswith('/auth/login/'):
            # Redirect to our custom login page
            next_url = request.GET.get('next', '')
            if next_url:
                return redirect(f'/accounts/login/?next={next_url}')
            else:
                return redirect('/accounts/login/')

        response = self.get_response(request)
        return response