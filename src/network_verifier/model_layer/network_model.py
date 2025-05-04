"""
Network model implementation.
"""

from typing import Dict, List, Optional
from dataclasses import dataclass
from enum import Enum

class DeviceType(Enum):
    """Network device types."""
    ROUTER = "router"
    SWITCH = "switch"
    FIREWALL = "firewall"

@dataclass
class Interface:
    """Network interface representation."""
    name: str
    ip_address: Optional[str] = None
    subnet_mask: Optional[str] = None
    neighbor: Optional[str] = None
    neighbor_interface: Optional[str] = None

@dataclass
class Device:
    """Network device representation."""
    name: str
    type: DeviceType
    interfaces: List[Interface]
    config: Dict[str, any]

class NetworkModel:
    """Network model class for representing network topology and configurations."""
    
    def __init__(self):
        """Initialize the network model."""
        self.devices: Dict[str, Device] = {}
        self.topology: Dict[str, List[str]] = {}
    
    def add_device(self, device: Device) -> None:
        """
        Add a device to the network model.
        
        Args:
            device: Device to add
        """
        self.devices[device.name] = device
        self.topology[device.name] = []
        
        # Update topology with device connections
        for interface in device.interfaces:
            if interface.neighbor:
                self.topology[device.name].append(interface.neighbor)
    
    def get_device(self, device_name: str) -> Optional[Device]:
        """
        Get a device by name.
        
        Args:
            device_name: Name of the device
            
        Returns:
            Device if found, None otherwise
        """
        return self.devices.get(device_name)
    
    def get_topology(self) -> Dict[str, List[str]]:
        """
        Get the network topology.
        
        Returns:
            Dictionary representing the network topology
        """
        return self.topology
    
    def get_devices(self) -> List[Device]:
        """
        Get all devices in the network.
        
        Returns:
            List of all devices
        """
        return list(self.devices.values())
    
    def get_device_interfaces(self, device_name: str) -> List[Interface]:
        """
        Get interfaces of a device.
        
        Args:
            device_name: Name of the device
            
        Returns:
            List of device interfaces
        """
        device = self.get_device(device_name)
        return device.interfaces if device else [] 