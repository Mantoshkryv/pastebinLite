"""
URL configuration for the pastes app.

This defines all the routes for our pastebin application:
- Home page with create form
- API endpoints for health check, creating, and fetching pastes
- HTML view for sharing pastes
"""

from django.urls import path
from .views import (
    HealthCheckView,
    PasteCreateView,
    PasteDetailView,
    paste_view_html,
    home_view
)

# App name for namespacing (useful if you have multiple apps)
app_name = 'pastebin'

urlpatterns = [
    # Home page - shows the form to create a new paste
    path('', home_view, name='home'),
    
    # Health check endpoint - required by the assignment
    # Returns {"ok": true} if the app is running and database is accessible
    path('api/healthz', HealthCheckView.as_view(), name='healthz'),
    
    # Create a new paste (POST request with JSON body)
    # Request: {"content": "...", "ttl_seconds": 60, "max_views": 5}
    # Response: {"id": "abc123", "url": "https://.../p/abc123"}
    path('api/pastes', PasteCreateView.as_view(), name='paste-create'),
    
    # Fetch a paste via API (GET request)
    # This COUNTS as a view and increments the view counter
    # Response: {"content": "...", "remaining_views": 4, "expires_at": "..."}
    path('api/pastes/<str:paste_id>', PasteDetailView.as_view(), name='paste-detail'),
    
    # View a paste as HTML (GET request)
    # This does NOT count as a view - it's just for displaying in the browser
    # Returns an HTML page with the paste content
    path('p/<str:paste_id>', paste_view_html, name='paste-view'),
]