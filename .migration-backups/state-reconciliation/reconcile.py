"""One-time reconciliation explicitly requested by the user on 2026-10-13."""
import json
from pathlib import Path

from django.db import transaction
from django.utils import timezone
from apps.common.models import Device
from apps.device.models import DeviceRemoval, DeviceRemovalCode
from apps.agent.models import AgentEvent, AgentHealth, AgentSession


def snapshot():
    return {
        'devices': list(Device.objects.values('id', 'organization_id', 'pc_id',
            'enrollment_status', 'is_active', 'revoked_at', 'removal_state', 'agent_allocation_active')),
        'removals': list(DeviceRemoval.objects.values('id', 'device_id', 'state', 'completed_at')),
        'codes': list(DeviceRemovalCode.objects.values('id', 'device_id', 'used_at', 'invalidated_at')),
        'health': list(AgentHealth.objects.values('id', 'device_id', 'state', 'loss_reported', 'pause_until')),
        'pending_sessions': list(AgentSession.objects.filter(status='pending').values('id', 'device_id', 'status', 'expires_at')),
    }


folder = Path('.migration-backups/state-reconciliation')
folder.mkdir(parents=True, exist_ok=True)
now = timezone.now()
stamp = now.strftime('%Y%m%dT%H%M%S%fZ')
reason = 'User explicitly confirmed that no agent is installed anywhere; manual state reconciliation, not an agent completion acknowledgement.'
with transaction.atomic():
    devices = list(Device.objects.select_for_update().filter(pk__in=[12, 15]))
    assert len(devices) == 2
    assert all(d.pc_id == 'b1806902-e17b-4ae4-a505-ba79e4f1595e' for d in devices)
    (folder / f'{stamp}-before.json').write_text(json.dumps(snapshot(), default=str, indent=2), encoding='utf-8')
    for device in devices:
        if device.removal_state == 'removed' and not device.is_active and not device.agent_allocation_active:
            continue
        before = {'removal_state': device.removal_state, 'is_active': device.is_active,
            'agent_allocation_active': device.agent_allocation_active}
        device.is_active = False
        device.revoked_at = device.revoked_at or now
        device.removal_state = 'removed'
        device.agent_allocation_active = False
        device.save(update_fields=['is_active', 'revoked_at', 'removal_state', 'agent_allocation_active', 'updated_at'])
        DeviceRemoval.objects.filter(device=device, state='removal_pending').update(state='removed', completed_at=now)
        DeviceRemovalCode.objects.filter(device=device, used_at__isnull=True, invalidated_at__isnull=True).update(invalidated_at=now)
        AgentSession.objects.filter(device=device, status='pending').update(status='expired', expires_at=now,
            fingerprint_challenge=None, fingerprint_challenge_expires=now)
        AgentHealth.objects.filter(device=device).update(state='stopped', loss_reported=False, pause_until=None)
        AgentEvent.objects.create(device=device, organization=device.organization, device_key=device.pk,
            kind='manual_removal_reconciliation', actor='user-confirmed reconciliation',
            device_snapshot={'pc_id': device.pc_id, 'platform': device.platform, 'location': device.location},
            details={'reason': reason, 'before': before, 'after': {'removal_state': 'removed',
                'is_active': False, 'agent_allocation_active': False}})
    assert not Device.objects.filter(is_active=True, enrollment_status='agent_enrolled').exists()
    assert not Device.objects.filter(agent_allocation_active=True).exists()
    assert not DeviceRemoval.objects.filter(state='removal_pending').exists()
(folder / f'{stamp}-after.json').write_text(json.dumps(snapshot(), default=str, indent=2), encoding='utf-8')
print(json.dumps({'updated_devices': [d.pk for d in devices], 'backup_stamp': stamp,
    'active_enrolled_agents': Device.objects.filter(is_active=True, enrollment_status='agent_enrolled').count(),
    'allocated_agents': Device.objects.filter(agent_allocation_active=True).count(),
    'pending_removals': DeviceRemoval.objects.filter(state='removal_pending').count()}, indent=2))
