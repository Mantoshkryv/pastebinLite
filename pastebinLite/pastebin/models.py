"""
Paste model for Pastebin-Lite application.

This module defines the core Paste model with support for:
- Unique paste identification
- Content storage
- Time-based expiration (TTL)
- View-count based expiration
- Atomic view counting
"""

from django.db import models
from django.utils import timezone
from django.db.models import F
import uuid
import secrets
import string


def generate_paste_id():
    alphabet = string.ascii_letters + string.digits
    return ''.join(secrets.choice(alphabet) for _ in range(12))


class Paste(models.Model):
    id = models.CharField(
        max_length=22,
        primary_key=True,
        editable=False,
        help_text="Unique identifier for the paste"
    )
    
    content = models.TextField(
        help_text="The text content of the paste"
    )
    
    created_at = models.DateTimeField(
        auto_now_add=True,
        db_index=True,
        help_text="Timestamp when paste was created"
    )
    
    expires_at = models.DateTimeField(
        null=True,
        blank=True,
        db_index=True,
        help_text="Optional expiration timestamp (TTL)"
    )
    
    max_views = models.IntegerField(
        null=True,
        blank=True,
        help_text="Optional maximum number of views allowed"
    )
    
    view_count = models.IntegerField(
        default=0,
        help_text="Number of times paste has been viewed via API"
    )
    
    class Meta:
        db_table = 'pastes'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['expires_at'], name='paste_expires_idx'),
            models.Index(fields=['created_at'], name='paste_created_idx'),
        ]
        verbose_name = 'Paste'
        verbose_name_plural = 'Pastes'
    
    def save(self, *args, **kwargs):
        if not self.id:
            # Generate unique ID
            while True:
                new_id = generate_paste_id()
                if not Paste.objects.filter(id=new_id).exists():
                    self.id = new_id
                    break
        
        super().save(*args, **kwargs)
    
    def is_expired(self, current_time=None):
        # Use provided time or current time
        now = current_time or timezone.now()
        
        # Check time-based expiration (TTL)
        if self.expires_at is not None:
            if now >= self.expires_at:
                return True
        
        # Check view-count based expiration
        if self.max_views is not None:
            if self.view_count >= self.max_views:
                return True
        
        # Paste is still available
        return False
    
    def increment_view(self):
        # Atomic increment in database
        Paste.objects.filter(pk=self.id).update(view_count=F('view_count') + 1)
        
        # Refresh instance to get updated view_count
        self.refresh_from_db()
    
    def get_remaining_views(self):
        if self.max_views is None:
            return None
        
        remaining = self.max_views - self.view_count
        return max(0, remaining)  # Never return negative
    
    def is_ttl_expired(self, current_time=None):
        if self.expires_at is None:
            return False
        
        now = current_time or timezone.now()
        return now >= self.expires_at
    
    def is_view_limit_exceeded(self):
        if self.max_views is None:
            return False
        
        return self.view_count >= self.max_views
    
    def __str__(self):
        status = "active"
        if self.is_expired():
            status = "expired"
        
        views_info = f"{self.view_count}"
        if self.max_views is not None:
            views_info += f"/{self.max_views}"
        else:
            views_info += "/unlimited"
        
        return f"Paste {self.id} - {status} - views: {views_info}"
    
    def __repr__(self):
        return (
            f"<Paste id={self.id} "
            f"created={self.created_at.isoformat() if self.created_at else 'None'} "
            f"expires={self.expires_at.isoformat() if self.expires_at else 'None'} "
            f"views={self.view_count}/{self.max_views or 'unlimited'}>"
        )