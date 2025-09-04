from django.db import models
from django.utils import timezone

class RequestLog(models.Model):
    """
    Model to store request tracking information.
    """
    ip_address = models.GenericIPAddressField(
        verbose_name="IP Address",
        help_text="The IP address of the client making the request"
    )
    timestamp = models.DateTimeField(
        verbose_name="Timestamp",
        default=timezone.now,
        help_text="When the request was made"
    )
    path = models.CharField(
        max_length=255,
        verbose_name="Request Path",
        help_text="The URL path that was requested"
    )
    country = models.CharField(
        max_length=100,
        verbose_name="Country",
        blank=True,
        null=True,
        help_text="Country where the IP address is located"
    )
    city = models.CharField(
        max_length=100,
        verbose_name="City",
        blank=True,
        null=True,
        help_text="City where the IP address is located"
    )
    
    class Meta:
        verbose_name = "Request Log"
        verbose_name_plural = "Request Logs"
        ordering = ['-timestamp']
        indexes = [
            models.Index(fields=['-timestamp']),
            models.Index(fields=['ip_address']),
            models.Index(fields=['path']),
            models.Index(fields=['country']),
            models.Index(fields=['city']),
        ]
    
    def __str__(self):
        location = f" ({self.city}, {self.country})" if self.city and self.country else ""
        return f"{self.ip_address} - {self.path} - {self.timestamp}{location}"
    
    def __repr__(self):
        return f"<RequestLog: {self.ip_address} at {self.timestamp}>"


class BlockedIP(models.Model):
    """
    Model to store blocked IP addresses.
    """
    ip_address = models.GenericIPAddressField(
        verbose_name="Blocked IP Address",
        help_text="The IP address that is blocked from accessing the site",
        unique=True
    )
    created_at = models.DateTimeField(
        verbose_name="Blocked At",
        default=timezone.now,
        help_text="When this IP was blocked"
    )
    reason = models.TextField(
        verbose_name="Block Reason",
        blank=True,
        help_text="Optional reason for blocking this IP"
    )
    
    class Meta:
        verbose_name = "Blocked IP"
        verbose_name_plural = "Blocked IPs"
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['ip_address']),
            models.Index(fields=['-created_at']),
        ]
    
    def __str__(self):
        return f"{self.ip_address} - Blocked at {self.created_at}"
    
    def __repr__(self):
        return f"<BlockedIP: {self.ip_address}>"


class IPGeolocationCache(models.Model):
    """
    Cache for IP geolocation data to avoid repeated API calls.
    """
    ip_address = models.GenericIPAddressField(
        verbose_name="IP Address",
        help_text="The IP address for which geolocation data is cached",
        unique=True
    )
    country = models.CharField(
        max_length=100,
        verbose_name="Country",
        blank=True,
        null=True,
        help_text="Country where the IP address is located"
    )
    city = models.CharField(
        max_length=100,
        verbose_name="City",
        blank=True,
        null=True,
        help_text="City where the IP address is located"
    )
    cached_at = models.DateTimeField(
        verbose_name="Cached At",
        default=timezone.now,
        help_text="When this geolocation data was cached"
    )
    
    class Meta:
        verbose_name = "IP Geolocation Cache"
        verbose_name_plural = "IP Geolocation Caches"
        ordering = ['-cached_at']
        indexes = [
            models.Index(fields=['ip_address']),
            models.Index(fields=['cached_at']),
        ]
    
    def __str__(self):
        location = f" ({self.city}, {self.country})" if self.city and self.country else " (Unknown location)"
        return f"{self.ip_address}{location}"
    
    def __repr__(self):
        return f"<IPGeolocationCache: {self.ip_address}>"
    
    def is_expired(self, hours=24):
        """Check if the cache entry has expired (default: 24 hours)."""
        from django.utils import timezone
        from datetime import timedelta
        return timezone.now() > self.cached_at + timedelta(hours=hours)


class SuspiciousIP(models.Model):
    """
    Model to store IP addresses flagged for suspicious activity.
    """
    SUSPICIOUS_REASONS = [
        ('high_volume', 'High Request Volume'),
        ('sensitive_paths', 'Accessing Sensitive Paths'),
        ('failed_logins', 'Multiple Failed Login Attempts'),
        ('admin_access', 'Admin Panel Access Attempts'),
        ('brute_force', 'Brute Force Attack Pattern'),
    ]
    
    ip_address = models.GenericIPAddressField(
        verbose_name="Suspicious IP Address",
        help_text="The IP address flagged for suspicious activity"
    )
    reason = models.CharField(
        max_length=50,
        choices=SUSPICIOUS_REASONS,
        verbose_name="Suspicious Activity Reason",
        help_text="The reason why this IP was flagged"
    )
    details = models.TextField(
        verbose_name="Additional Details",
        blank=True,
        help_text="Additional details about the suspicious activity"
    )
    request_count = models.PositiveIntegerField(
        verbose_name="Request Count",
        default=0,
        help_text="Number of requests that triggered this flag"
    )
    first_seen = models.DateTimeField(
        verbose_name="First Seen",
        default=timezone.now,
        help_text="When this IP was first flagged"
    )
    last_seen = models.DateTimeField(
        verbose_name="Last Seen",
        auto_now=True,
        help_text="When this IP was last flagged"
    )
    is_active = models.BooleanField(
        verbose_name="Active Flag",
        default=True,
        help_text="Whether this suspicious activity flag is still active"
    )
    
    class Meta:
        verbose_name = "Suspicious IP"
        verbose_name_plural = "Suspicious IPs"
        ordering = ['-last_seen']
        indexes = [
            models.Index(fields=['ip_address']),
            models.Index(fields=['reason']),
            models.Index(fields=['is_active']),
            models.Index(fields=['-last_seen']),
        ]
        unique_together = ['ip_address', 'reason']
    
    def __str__(self):
        return f"{self.ip_address} - {self.get_reason_display()}"
    
    def __repr__(self):
        return f"<SuspiciousIP: {self.ip_address} - {self.reason}>"
    
    def get_reason_display(self):
        """Get the human-readable reason."""
        return dict(self.SUSPICIOUS_REASONS).get(self.reason, self.reason)
