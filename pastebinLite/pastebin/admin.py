from django.contrib import admin

# Register your models here.
from .models import Paste


@admin.register(Paste)
class PasteAdmin(admin.ModelAdmin):
    """
    Admin interface for managing pastes.
    
    Shows the most useful info at a glance and makes key fields searchable.
    """
    list_display = ['id', 'created_at', 'expires_at', 'max_views', 'view_count', 'is_active']
    list_filter = ['created_at', 'expires_at']
    search_fields = ['id', 'content']
    readonly_fields = ['id', 'created_at', 'view_count']
    
    def is_active(self, obj):
        """Show a green checkmark if the paste is still available"""
        return not obj.is_expired()
    
    is_active.boolean = True
    is_active.short_description = 'Active'