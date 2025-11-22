"""
VM Scheduler Cloud Function
Handles Pub/Sub messages to scale up/down Google Cloud VMs
"""

import os
import base64
import json
import logging
from google.cloud import compute_v1
import functions_framework

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class VMScheduler:
    """Manages VM operations for scaling"""
    
    def __init__(self, project_id):
        self.project_id = project_id or os.environ.get('GCP_PROJECT')
        self.instances_client = compute_v1.InstancesClient()
        
    def get_instances_by_labels(self, zones, labels):
        """Get all instances matching specified labels"""
        instances = []
        
        for zone in zones:
            try:
                request = compute_v1.ListInstancesRequest(
                    project=self.project_id,
                    zone=zone
                )
                
                for instance in self.instances_client.list(request=request):
                    # Check if instance has matching labels
                    if self._matches_labels(instance.labels, labels):
                        instances.append({
                            'name': instance.name,
                            'zone': zone,
                            'status': instance.status
                        })
                        
            except Exception as e:
                logger.error(f"Error listing instances in zone {zone}: {e}")
                
        return instances
    
    def _matches_labels(self, instance_labels, target_labels):
        """Check if instance labels match target labels"""
        if not instance_labels:
            return False
            
        for label in target_labels:
            key = label.get('key')
            value = label.get('value')
            if instance_labels.get(key) != value:
                return False
                
        return True
    
    def stop_instance(self, zone, instance_name):
        """Stop a VM instance"""
        try:
            request = compute_v1.StopInstanceRequest(
                project=self.project_id,
                zone=zone,
                instance=instance_name
            )
            
            operation = self.instances_client.stop(request=request)
            logger.info(f"Stopping instance {instance_name} in zone {zone}")
            return {'status': 'success', 'operation': operation.name}
            
        except Exception as e:
            logger.error(f"Error stopping instance {instance_name}: {e}")
            return {'status': 'error', 'message': str(e)}
    
    def start_instance(self, zone, instance_name):
        """Start a VM instance"""
        try:
            request = compute_v1.StartInstanceRequest(
                project=self.project_id,
                zone=zone,
                instance=instance_name
            )
            
            operation = self.instances_client.start(request=request)
            logger.info(f"Starting instance {instance_name} in zone {zone}")
            return {'status': 'success', 'operation': operation.name}
            
        except Exception as e:
            logger.error(f"Error starting instance {instance_name}: {e}")
            return {'status': 'error', 'message': str(e)}
    
    def suspend_instance(self, zone, instance_name):
        """Suspend a VM instance"""
        try:
            request = compute_v1.SuspendInstanceRequest(
                project=self.project_id,
                zone=zone,
                instance=instance_name
            )
            
            operation = self.instances_client.suspend(request=request)
            logger.info(f"Suspending instance {instance_name} in zone {zone}")
            return {'status': 'success', 'operation': operation.name}
            
        except Exception as e:
            logger.error(f"Error suspending instance {instance_name}: {e}")
            return {'status': 'error', 'message': str(e)}
    
    def resume_instance(self, zone, instance_name):
        """Resume a suspended VM instance"""
        try:
            request = compute_v1.ResumeInstanceRequest(
                project=self.project_id,
                zone=zone,
                instance=instance_name
            )
            
            operation = self.instances_client.resume(request=request)
            logger.info(f"Resuming instance {instance_name} in zone {zone}")
            return {'status': 'success', 'operation': operation.name}
            
        except Exception as e:
            logger.error(f"Error resuming instance {instance_name}: {e}")
            return {'status': 'error', 'message': str(e)}


def process_scale_action(action, project_id=None, vm_labels=None, zones=None):
    """Process scale up or scale down action"""
    
    # Get project ID from environment
    if not project_id:
        project_id = os.environ.get('GCP_PROJECT')
    
    if not project_id:
        logger.error('Project ID not configured')
        return {'error': 'Project ID not configured'}
    
    scheduler = VMScheduler(project_id)
    results = []
    
    # Get VM labels and zones from environment variables if not provided
    if not vm_labels:
        vm_labels_str = os.environ.get('VM_LABELS', 'auto-schedule:true')
        vm_labels = []
        for label in vm_labels_str.split(','):
            if ':' in label:
                key, value = label.split(':', 1)
                vm_labels.append({'key': key.strip(), 'value': value.strip()})
    
    if not zones:
        zones_str = os.environ.get('VM_ZONES', 'us-central1-a,us-central1-b')
        zones = [z.strip() for z in zones_str.split(',')]
    
    # Get instances using label-based discovery
    instances = scheduler.get_instances_by_labels(zones, vm_labels)
    
    if not instances:
        logger.warning('No instances found matching the specified labels')
        return {'processed': 0, 'results': [], 'message': 'No instances found'}
    
    # Perform action on each instance
    for instance in instances:
        zone = instance.get('zone')
        name = instance.get('name')
        status = instance.get('status')
        
        # Skip if instance is already in desired state
        if action == 'scale_down' and status in ['STOPPED', 'TERMINATED', 'SUSPENDED']:
            logger.info(f"Instance {name} already stopped/suspended, skipping")
            continue
        elif action == 'scale_up' and status == 'RUNNING':
            logger.info(f"Instance {name} already running, skipping")
            continue
        
        if action == 'scale_down':
            action_type = os.environ.get('SCALE_DOWN_ACTION', 'STOP')
            if action_type == 'SUSPEND':
                result = scheduler.suspend_instance(zone, name)
            else:
                result = scheduler.stop_instance(zone, name)
        elif action == 'scale_up':
            action_type = os.environ.get('SCALE_UP_ACTION', 'START')
            if action_type == 'RESUME':
                result = scheduler.resume_instance(zone, name)
            else:
                result = scheduler.start_instance(zone, name)
        else:
            result = {'status': 'error', 'message': f'Unknown action: {action}'}
        
        results.append({
            'instance': name,
            'zone': zone,
            'action': action,
            'result': result
        })
    
    return {'processed': len(results), 'results': results}


@functions_framework.cloud_event
def vm_scheduler(cloud_event):
    """
    Cloud Function triggered by Pub/Sub.
    Args:
        cloud_event: CloudEvent object containing Pub/Sub message
    """
    
    # Decode Pub/Sub message
    try:
        message_data = base64.b64decode(cloud_event.data["message"]["data"]).decode()
        data = json.loads(message_data)
    except Exception as e:
        logger.error(f'Error decoding message: {e}')
        data = {}
    
    # Get action from message (default to scale_down for backward compatibility)
    action = data.get('action', 'scale_down')
    project_id = data.get('project_id')
    vm_labels = data.get('vm_labels')
    zones = data.get('zones')
    
    logger.info(f'Processing action: {action}')
    
    # Process the action
    result = process_scale_action(action, project_id, vm_labels, zones)
    
    logger.info(f'Action completed: {result}')
    
    return result
