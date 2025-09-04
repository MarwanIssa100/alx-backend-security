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
    
    class Meta:
        verbose_name = "Request Log"
        verbose_name_plural = "Request Logs"
        ordering = ['-timestamp']
        indexes = [
            models.Index(fields=['-timestamp']),
            models.Index(fields=['ip_address']),
            models.Index(fields=['path']),
        ]
    
    def __str__(self):
        return f"{self.ip_address} - {self.path} - {self.timestamp}"
    
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
