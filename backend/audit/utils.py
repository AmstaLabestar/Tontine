from .models import AuditEvent


def log_audit_event(group, event_type, actor, description="", target_type="", target_id="", metadata=None, ip_address=None, device_id=""):
    """Create an immutable audit event."""
    return AuditEvent.objects.create(
        group=group,
        event_type=event_type,
        actor=actor,
        description=description,
        target_type=target_type,
        target_id=target_id,
        metadata=metadata or {},
        ip_address=ip_address,
        device_id=device_id,
    )
