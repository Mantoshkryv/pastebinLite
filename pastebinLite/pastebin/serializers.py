from rest_framework import serializers
from .models import Paste
from django.utils import timezone
from datetime import timedelta


class PasteCreateSerializer(serializers.Serializer):
    """
    Handles validation and creation of new pastes.
    
    This serializer ensures that:
    - Content is present and not just whitespace
    - TTL (if provided) is at least 1 second
    - Max views (if provided) is at least 1
    
    Both ttl_seconds and max_views are optional. If neither is provided,
    the paste will never expire.
    """
    
    content = serializers.CharField(
        required=True, 
        allow_blank=False,
        trim_whitespace=False,  # Keep original formatting
        help_text="The text content of the paste"
    )
    
    ttl_seconds = serializers.IntegerField(
        required=False,
        min_value=1,
        help_text="Time-to-live in seconds (optional)"
    )
    
    max_views = serializers.IntegerField(
        required=False,
        min_value=1,
        help_text="Maximum number of API views allowed (optional)"
    )
    
    def validate_content(self, value):
        """
        Make sure the content isn't empty or just whitespace.
        
        Even though we set allow_blank=False, we also check for whitespace-only
        content since that's not very useful for a paste.
        """
        if not value or not value.strip():
            raise serializers.ValidationError("Content cannot be empty")
        return value
    
    def validate_ttl_seconds(self, value):
        """
        Validate TTL is a positive integer.
        
        The min_value=1 in the field definition already handles this,
        but we keep this method in case we want to add more validation later
        (e.g., maximum TTL limits).
        """
        if value is not None and value < 1:
            raise serializers.ValidationError("TTL must be at least 1 second")
        return value
    
    def validate_max_views(self, value):
        """
        Validate max_views is a positive integer.
        
        Similar to TTL validation - the field definition handles the basics,
        but this gives us a place to add more complex rules if needed.
        """
        if value is not None and value < 1:
            raise serializers.ValidationError("Max views must be at least 1")
        return value
    
    def validate(self, data):
        """
        Cross-field validation (runs after individual field validation).
        
        Currently we don't have any cross-field rules, but this is where you'd
        add them. For example, you might want to limit TTL based on whether
        max_views is set, or vice versa.
        """
        # Could add rules like:
        # - Don't allow TTL > 30 days if max_views is unlimited
        # - Require at least one constraint (TTL or max_views)
        # But for now, we allow any combination including no constraints
        return data
    
    def create(self, validated_data):
        """
        Create a new paste with the validated data.
        
        This is where we convert ttl_seconds into an actual expiration timestamp.
        The Paste model will automatically generate a unique ID when we save.
        """
        content = validated_data['content']
        ttl_seconds = validated_data.get('ttl_seconds')
        max_views = validated_data.get('max_views')
        
        # Create the paste object (but don't save yet)
        paste = Paste(content=content, max_views=max_views)
        
        # If TTL is set, calculate the exact expiration time
        # We use timezone.now() to get a timezone-aware datetime
        if ttl_seconds:
            paste.expires_at = timezone.now() + timedelta(seconds=ttl_seconds)
        
        # Save to database (this triggers ID generation in the model)
        paste.save()
        
        return paste


class PasteDetailSerializer(serializers.ModelSerializer):
    """
    Formats paste data for API responses.
    
    This is used when fetching a paste via GET /api/pastes/:id
    We return:
    - The paste content
    - How many views are remaining (null if unlimited)
    - When it expires (null if no TTL)
    
    Note: We don't include view_count or max_views directly. Instead we
    calculate "remaining_views" which is more useful to clients.
    """
    
    remaining_views = serializers.SerializerMethodField()
    
    # Format the timestamp to match the spec exactly
    # The format string produces: 2026-01-01T00:00:00.000Z
    expires_at = serializers.DateTimeField(
        format='%Y-%m-%dT%H:%M:%S.%fZ',
        allow_null=True,
        required=False
    )
    
    class Meta:
        model = Paste
        fields = ['content', 'remaining_views', 'expires_at']
        # We explicitly list fields rather than using '__all__' or exclude
        # This makes it clear exactly what we're exposing in the API
    
    def get_remaining_views(self, obj):
        """
        Get how many views are left before the paste expires.
        
        We delegate this to the model's method to avoid duplicating the calculation logic.
        The model already handles the calculation and ensures we never return negative values.
        """
        return obj.get_remaining_views()


class PasteListSerializer(serializers.ModelSerializer):
    """
    Lighter serializer for listing pastes (if we add a list endpoint later).
    
    Not required for the assignment, but useful if you want to add a feature
    to show all active pastes or let users see their paste history.
    """
    
    is_expired = serializers.SerializerMethodField()
    views_used = serializers.IntegerField(source='view_count', read_only=True)
    
    class Meta:
        model = Paste
        fields = ['id', 'created_at', 'expires_at', 'max_views', 'views_used', 'is_expired']
    
    def get_is_expired(self, obj):
        """Check if the paste is currently expired"""
        return obj.is_expired()