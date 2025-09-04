from celery import shared_task
from django.utils import timezone
from django.db.models import Count, Q
from datetime import timedelta
import logging

from .models import RequestLog, SuspiciousIP, BlockedIP

logger = logging.getLogger(__name__)


@shared_task
def monitor_suspicious_ips():
    """
    Hourly task to monitor and flag suspicious IP activity.
    Flags IPs that:
    - Exceed 100 requests per hour
    - Access sensitive paths frequently
    - Show patterns of suspicious behavior
    """
    logger.info("Starting suspicious IP monitoring task")
    
    # Calculate time window (last hour)
    one_hour_ago = timezone.now() - timedelta(hours=1)
    
    try:
        # 1. Check for high volume requests (>100 per hour)
        high_volume_ips = check_high_volume_ips(one_hour_ago)
        
        # 2. Check for sensitive path access
        sensitive_path_ips = check_sensitive_path_access(one_hour_ago)
        
        # 3. Check for failed login attempts
        failed_login_ips = check_failed_login_attempts(one_hour_ago)
        
        # 4. Check for admin panel access attempts
        admin_access_ips = check_admin_access_attempts(one_hour_ago)
        
        # 5. Check for brute force patterns
        brute_force_ips = check_brute_force_patterns(one_hour_ago)
        
        # Summary
        total_flagged = len(high_volume_ips) + len(sensitive_path_ips) + len(failed_login_ips) + len(admin_access_ips) + len(brute_force_ips)
        
        logger.info(f"Suspicious IP monitoring completed. Flagged {total_flagged} IPs")
        
        return {
            'high_volume': len(high_volume_ips),
            'sensitive_paths': len(sensitive_path_ips),
            'failed_logins': len(failed_login_ips),
            'admin_access': len(admin_access_ips),
            'brute_force': len(brute_force_ips),
            'total': total_flagged
        }
        
    except Exception as e:
        logger.error(f"Error in suspicious IP monitoring task: {e}")
        raise


def check_high_volume_ips(since_time):
    """Check for IPs with more than 100 requests in the last hour."""
    logger.info("Checking for high volume IPs...")
    
    # Get IPs with >100 requests in the last hour
    high_volume = (
        RequestLog.objects
        .filter(timestamp__gte=since_time)
        .values('ip_address')
        .annotate(request_count=Count('id'))
        .filter(request_count__gt=100)
    )
    
    flagged_ips = []
    for item in high_volume:
        ip_address = item['ip_address']
        request_count = item['request_count']
        
        # Create or update SuspiciousIP record
        suspicious_ip, created = SuspiciousIP.objects.get_or_create(
            ip_address=ip_address,
            reason='high_volume',
            defaults={
                'details': f'IP made {request_count} requests in the last hour (threshold: 100)',
                'request_count': request_count,
            }
        )
        
        if not created:
            # Update existing record
            suspicious_ip.details = f'IP made {request_count} requests in the last hour (threshold: 100)'
            suspicious_ip.request_count = request_count
            suspicious_ip.is_active = True
            suspicious_ip.save()
        
        flagged_ips.append(ip_address)
        logger.warning(f"Flagged IP {ip_address} for high volume: {request_count} requests")
    
    return flagged_ips


def check_sensitive_path_access(since_time):
    """Check for IPs accessing sensitive paths frequently."""
    logger.info("Checking for sensitive path access...")
    
    # Define sensitive paths
    sensitive_paths = [
        '/admin/',
        '/api/login/',
        '/api/dashboard/',
        '/api/profile/',
        '/admin/login/',
    ]
    
    flagged_ips = []
    
    for path in sensitive_paths:
        # Get IPs that accessed this sensitive path multiple times
        sensitive_access = (
            RequestLog.objects
            .filter(
                timestamp__gte=since_time,
                path__startswith=path
            )
            .values('ip_address')
            .annotate(access_count=Count('id'))
            .filter(access_count__gt=5)  # More than 5 attempts to sensitive path
        )
        
        for item in sensitive_access:
            ip_address = item['ip_address']
            access_count = item['access_count']
            
            # Create or update SuspiciousIP record
            suspicious_ip, created = SuspiciousIP.objects.get_or_create(
                ip_address=ip_address,
                reason='sensitive_paths',
                defaults={
                    'details': f'IP accessed sensitive path {path} {access_count} times in the last hour',
                    'request_count': access_count,
                }
            )
            
            if not created:
                # Update existing record
                suspicious_ip.details = f'IP accessed sensitive path {path} {access_count} times in the last hour'
                suspicious_ip.request_count = access_count
                suspicious_ip.is_active = True
                suspicious_ip.save()
            
            if ip_address not in flagged_ips:
                flagged_ips.append(ip_address)
                logger.warning(f"Flagged IP {ip_address} for sensitive path access: {path} ({access_count} times)")
    
    return flagged_ips


def check_failed_login_attempts(since_time):
    """Check for IPs with multiple failed login attempts."""
    logger.info("Checking for failed login attempts...")
    
    # This would need to be implemented based on your login failure tracking
    # For now, we'll check for multiple POST requests to login endpoint
    failed_logins = (
        RequestLog.objects
        .filter(
            timestamp__gte=since_time,
            path='/api/login/'
        )
        .values('ip_address')
        .annotate(attempt_count=Count('id'))
        .filter(attempt_count__gt=10)  # More than 10 login attempts
    )
    
    flagged_ips = []
    for item in failed_logins:
        ip_address = item['ip_address']
        attempt_count = item['attempt_count']
        
        # Create or update SuspiciousIP record
        suspicious_ip, created = SuspiciousIP.objects.get_or_create(
            ip_address=ip_address,
            reason='failed_logins',
            defaults={
                'details': f'IP made {attempt_count} login attempts in the last hour',
                'request_count': attempt_count,
            }
        )
        
        if not created:
            # Update existing record
            suspicious_ip.details = f'IP made {attempt_count} login attempts in the last hour'
            suspicious_ip.request_count = attempt_count
            suspicious_ip.is_active = True
            suspicious_ip.save()
        
        flagged_ips.append(ip_address)
        logger.warning(f"Flagged IP {ip_address} for failed login attempts: {attempt_count} attempts")
    
    return flagged_ips


def check_admin_access_attempts(since_time):
    """Check for IPs attempting to access admin panel."""
    logger.info("Checking for admin access attempts...")
    
    admin_access = (
        RequestLog.objects
        .filter(
            timestamp__gte=since_time,
            path__startswith='/admin/'
        )
        .values('ip_address')
        .annotate(access_count=Count('id'))
        .filter(access_count__gt=3)  # More than 3 admin access attempts
    )
    
    flagged_ips = []
    for item in admin_access:
        ip_address = item['ip_address']
        access_count = item['access_count']
        
        # Create or update SuspiciousIP record
        suspicious_ip, created = SuspiciousIP.objects.get_or_create(
            ip_address=ip_address,
            reason='admin_access',
            defaults={
                'details': f'IP attempted admin access {access_count} times in the last hour',
                'request_count': access_count,
            }
        )
        
        if not created:
            # Update existing record
            suspicious_ip.details = f'IP attempted admin access {access_count} times in the last hour'
            suspicious_ip.request_count = access_count
            suspicious_ip.is_active = True
            suspicious_ip.save()
        
        flagged_ips.append(ip_address)
        logger.warning(f"Flagged IP {ip_address} for admin access attempts: {access_count} attempts")
    
    return flagged_ips


def check_brute_force_patterns(since_time):
    """Check for brute force attack patterns."""
    logger.info("Checking for brute force patterns...")
    
    # Look for IPs with rapid successive requests (potential automated attacks)
    # This is a simplified check - in production you might want more sophisticated pattern detection
    
    # Get IPs with very high request rates (more than 200 requests per hour)
    brute_force_candidates = (
        RequestLog.objects
        .filter(timestamp__gte=since_time)
        .values('ip_address')
        .annotate(request_count=Count('id'))
        .filter(request_count__gt=200)  # Very high volume
    )
    
    flagged_ips = []
    for item in brute_force_candidates:
        ip_address = item['ip_address']
        request_count = item['request_count']
        
        # Check if this IP is already flagged for high volume
        if not SuspiciousIP.objects.filter(ip_address=ip_address, reason='high_volume').exists():
            # Create or update SuspiciousIP record
            suspicious_ip, created = SuspiciousIP.objects.get_or_create(
                ip_address=ip_address,
                reason='brute_force',
                defaults={
                    'details': f'IP shows brute force pattern with {request_count} requests in the last hour',
                    'request_count': request_count,
                }
            )
            
            if not created:
                # Update existing record
                suspicious_ip.details = f'IP shows brute force pattern with {request_count} requests in the last hour'
                suspicious_ip.request_count = request_count
                suspicious_ip.is_active = True
                suspicious_ip.save()
            
            flagged_ips.append(ip_address)
            logger.warning(f"Flagged IP {ip_address} for brute force pattern: {request_count} requests")
    
    return flagged_ips


@shared_task
def cleanup_old_suspicious_flags():
    """
    Daily task to clean up old suspicious IP flags.
    Deactivates flags older than 7 days.
    """
    logger.info("Starting cleanup of old suspicious IP flags...")
    
    seven_days_ago = timezone.now() - timedelta(days=7)
    
    try:
        # Deactivate old flags
        old_flags = SuspiciousIP.objects.filter(
            last_seen__lt=seven_days_ago,
            is_active=True
        )
        
        count = old_flags.count()
        old_flags.update(is_active=False)
        
        logger.info(f"Deactivated {count} old suspicious IP flags")
        
        return {'deactivated_count': count}
        
    except Exception as e:
        logger.error(f"Error in cleanup task: {e}")
        raise


@shared_task
def auto_block_suspicious_ips():
    """
    Task to automatically block IPs with severe suspicious activity.
    Blocks IPs that have been flagged multiple times for different reasons.
    """
    logger.info("Starting automatic blocking of severely suspicious IPs...")
    
    try:
        # Find IPs flagged for multiple reasons
        severely_suspicious = (
            SuspiciousIP.objects
            .filter(is_active=True)
            .values('ip_address')
            .annotate(flag_count=Count('reason'))
            .filter(flag_count__gte=3)  # Flagged for 3 or more different reasons
        )
        
        blocked_count = 0
        for item in severely_suspicious:
            ip_address = item['ip_address']
            
            # Check if IP is already blocked
            if not BlockedIP.objects.filter(ip_address=ip_address).exists():
                # Get all reasons for this IP
                reasons = SuspiciousIP.objects.filter(
                    ip_address=ip_address,
                    is_active=True
                ).values_list('reason', flat=True)
                
                reason_text = ', '.join([dict(SuspiciousIP.SUSPICIOUS_REASONS)[r] for r in reasons])
                
                # Create blocked IP record
                BlockedIP.objects.create(
                    ip_address=ip_address,
                    reason=f"Auto-blocked due to multiple suspicious activities: {reason_text}"
                )
                
                blocked_count += 1
                logger.warning(f"Auto-blocked IP {ip_address} for multiple suspicious activities: {reason_text}")
        
        logger.info(f"Auto-blocked {blocked_count} severely suspicious IPs")
        
        return {'blocked_count': blocked_count}
        
    except Exception as e:
        logger.error(f"Error in auto-blocking task: {e}")
        raise
