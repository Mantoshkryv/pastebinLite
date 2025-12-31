from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from django.shortcuts import render, get_object_or_404
from django.http import Http404
from django.utils import timezone
from django.utils.html import escape
from .models import Paste
from .serializers import PasteCreateSerializer, PasteDetailSerializer
from datetime import datetime
import os


def get_current_time(request):
    if os.environ.get('TEST_MODE') == '1':
        test_now_ms = request.META.get('HTTP_X_TEST_NOW_MS')
        if test_now_ms:
            try:
                # Convert milliseconds to seconds for the timestamp
                timestamp_seconds = int(test_now_ms) / 1000
                return datetime.fromtimestamp(timestamp_seconds, tz=timezone.utc)
            except (ValueError, OSError):
                # If the header is malformed, just use real time
                pass
    
    return timezone.now()


class HealthCheckView(APIView):
    """
    Simple health check endpoint.
    
    Returns {"ok": true} if the app is running and can talk to the database.
    Used by deployment platforms and monitoring tools.
    """
    def get(self, request):
        try:
            # Quick database ping to make sure we can connect
            from django.db import connection
            with connection.cursor() as cursor:
                cursor.execute("SELECT 1")
            
            return Response({"ok": True}, status=status.HTTP_200_OK)
        except Exception as e:
            return Response(
                {"ok": False, "error": str(e)}, 
                status=status.HTTP_503_SERVICE_UNAVAILABLE
            )


class PasteCreateView(APIView):
    """
    Create a new paste.
    
    Accepts JSON with content and optional constraints (ttl_seconds, max_views).
    Returns the paste ID and a shareable URL.
    """
    def post(self, request):
        serializer = PasteCreateSerializer(data=request.data)
        
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        
        paste = serializer.save()
        
        # Build the full URL for this paste
        base_url = request.build_absolute_uri('/').rstrip('/')
        paste_url = f"{base_url}/p/{paste.id}"
        
        return Response({
            "id": paste.id,
            "url": paste_url
        }, status=status.HTTP_201_CREATED)


class PasteDetailView(APIView):
    """
    Fetch a paste via the API.
    
    Important: This endpoint COUNTS as a view, so it increments the view counter.
    We have to be careful to check expiration both before AND after incrementing,
    since the increment itself might push it over the limit.
    """
    def get(self, request, paste_id):
        # Try to find the paste
        try:
            paste = Paste.objects.get(pk=paste_id)
        except Paste.DoesNotExist:
            return Response(
                {"error": "Paste not found"}, 
                status=status.HTTP_404_NOT_FOUND
            )
        
        current_time = get_current_time(request)
        
        # First check: is it already expired?
        if paste.is_expired(current_time):
            return Response(
                {"error": "Paste not found"}, 
                status=status.HTTP_404_NOT_FOUND
            )
        
        # Count this as a view
        paste.increment_view()
        
        # Second check: did that view push it over the limit?
        # (e.g., if max_views was 1 and this was the first view)
        if paste.is_expired(current_time):
            return Response(
                {"error": "Paste not found"}, 
                status=status.HTTP_404_NOT_FOUND
            )
        
        # All good - return the paste data
        serializer = PasteDetailSerializer(paste)
        return Response(serializer.data, status=status.HTTP_200_OK)


def paste_view_html(request, paste_id):
    """
    Show a paste as an HTML page.
    
    Note: Unlike the API endpoint, this does NOT count as a view.
    We also escape the content to prevent XSS attacks.
    """
    try:
        paste = get_object_or_404(Paste, pk=paste_id)
    except Http404:
        return render(request, 'pastebin/not_found.html', status=404)
    
    current_time = get_current_time(request)
    
    # Check if it's expired
    if paste.is_expired(current_time):
        return render(request, 'pastebin/not_found.html', status=404)
    
    # Escape the content so it displays as text, not executable code
    safe_content = escape(paste.content)
    
    return render(request, 'pastebin/view.html', {
        'content': safe_content,
        'paste_id': paste.id
    })


def home_view(request):
    """Show the home page with the form to create a new paste"""
    return render(request, 'pastebin/home.html')