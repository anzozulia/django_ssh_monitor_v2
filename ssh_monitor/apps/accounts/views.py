"""
Authentication views for SSH Monitor.

Provides login and logout functionality using Django's built-in auth system.
"""

from django.contrib.auth import login, logout
from django.contrib.auth.forms import AuthenticationForm
from django.shortcuts import redirect, render
from django.views import View


class LoginView(View):
    """Handle user login with username/password authentication."""

    template_name = "accounts/login.html"

    def get(self, request):
        """Display the login form."""
        if request.user.is_authenticated:
            return redirect("servers:dashboard")

        form = AuthenticationForm()
        return render(request, self.template_name, {"form": form})

    def post(self, request):
        """Process login form submission."""
        form = AuthenticationForm(request, data=request.POST)

        if form.is_valid():
            user = form.get_user()
            login(request, user)

            # Redirect to next URL if provided, otherwise to dashboard
            next_url = request.GET.get("next", "servers:dashboard")
            return redirect(next_url)

        return render(request, self.template_name, {"form": form})


class LogoutView(View):
    """Handle user logout."""

    def get(self, request):
        """Log out the user and redirect to login page."""
        logout(request)
        return redirect("accounts:login")

    def post(self, request):
        """Log out the user (POST for CSRF protection in forms)."""
        logout(request)
        return redirect("accounts:login")
