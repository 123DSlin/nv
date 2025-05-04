"""
Element builder for creating network elements.
"""

from typing import Dict, List, Optional
from .network_model import Device, DeviceType, Interface

class ElementBuilder:
    """Builder class for creating network elements."""
    
    @staticmethod
    def create_device(
        name: str,
        device_type: DeviceType,
        interfaces: List[Dict[str, str]],
        config: Dict[str, any]
    ) -> Device:
        """
        Create a network device.
        
        Args:
            name: Device name
            device_type: Type of device
            interfaces: List of interface configurations
            config: Device configuration
            
        Returns:
            Created Device object
        """
        device_interfaces = []
        for iface_config in interfaces:
            interface = Interface(
                name=iface_config.get('name', ''),
                ip_address=iface_config.get('ip_address'),
                subnet_mask=iface_config.get('subnet_mask'),
                neighbor=iface_config.get('neighbor'),
                neighbor_interface=iface_config.get('neighbor_interface')
            )
            device_interfaces.append(interface)
        
        return Device(
            name=name,
            type=device_type,
            interfaces=device_interfaces,
            config=config
        ) 