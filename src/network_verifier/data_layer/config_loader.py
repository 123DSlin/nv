"""
Configuration loader for network devices.
"""

from typing import Dict, Any, List
import os
from pathlib import Path
import json
import re

class ConfigLoader:
    """Loads and processes network device configurations."""
    
    def __init__(self):
        """Initialize the config loader."""
        self.configs = {}
    
    def load_configs(self, file_path: str) -> Dict[str, Any]:
        """
        Load configuration from a file.
        
        Args:
            file_path: Path to the configuration file
            
        Returns:
            Dictionary containing the configuration
        """
        with open(file_path, 'r') as f:
            content = f.read()
        
        # Extract device name
        hostname_match = re.search(r'hostname\s+(\S+)', content)
        device_name = hostname_match.group(1) if hostname_match else Path(file_path).stem
        
        # Extract interfaces
        interfaces = self._extract_interfaces(content)
        
        # Extract BGP neighbors
        bgp_neighbors = self._extract_bgp_neighbors(content)
        
        # Update interfaces with neighbor information
        for interface in interfaces:
            for neighbor in bgp_neighbors:
                if interface.get('ip_address') == neighbor.get('local_ip'):
                    interface['neighbor'] = neighbor['neighbor_name']
                    interface['neighbor_interface'] = neighbor['neighbor_interface']
        
        # Build configuration
        config = {
            'device_type': 'Cisco',
            'interfaces': interfaces,
            'bgp': {
                'router_id': self._extract_bgp_router_id(content),
                'neighbors': bgp_neighbors
            }
        }
        
        self.configs[device_name] = config
        return self.configs
    
    def _extract_interfaces(self, content: str) -> List[Dict[str, str]]:
        """Extract interface information from configuration."""
        interfaces = []
        interface_pattern = r'interface\s+(\S+)\s*\n(.*?)(?=^!|\Z)'
        
        for match in re.finditer(interface_pattern, content, re.MULTILINE | re.DOTALL):
            interface_name = match.group(1)
            interface_config = match.group(2)
            
            # Skip loopback interfaces
            if 'Loopback' in interface_name:
                continue
            
            # Extract IP address
            ip_match = re.search(r'ip address\s+(\S+)\s+(\S+)', interface_config)
            if ip_match:
                interfaces.append({
                    'name': interface_name,
                    'ip_address': ip_match.group(1),
                    'subnet_mask': ip_match.group(2),
                    'status': 'up' if not 'shutdown' in interface_config else 'down'
                })
        
        return interfaces
    
    def _extract_bgp_neighbors(self, content: str) -> List[Dict[str, str]]:
        """Extract BGP neighbor information from configuration."""
        neighbors = []
        bgp_section = self._extract_bgp_section(content)
        
        if not bgp_section:
            return neighbors
        
        # Extract neighbor configurations
        neighbor_pattern = r'neighbor\s+(\S+)\s+peer-group\s+(\S+)'
        for match in re.finditer(neighbor_pattern, bgp_section):
            neighbor_ip = match.group(1)
            peer_group = match.group(2)
            
            # Extract remote AS
            as_pattern = rf'neighbor\s+{peer_group}\s+remote-as\s+(\d+)'
            as_match = re.search(as_pattern, bgp_section)
            remote_as = as_match.group(1) if as_match else 'unknown'
            
            # Extract update source
            source_pattern = rf'neighbor\s+{neighbor_ip}\s+update-source\s+(\S+)'
            source_match = re.search(source_pattern, bgp_section)
            update_source = source_match.group(1) if source_match else None
            
            neighbors.append({
                'neighbor_ip': neighbor_ip,
                'peer_group': peer_group,
                'remote_as': remote_as,
                'local_ip': update_source,
                'neighbor_name': f'as{remote_as}router',
                'neighbor_interface': 'Loopback0'
            })
        
        return neighbors
    
    def _extract_bgp_section(self, content: str) -> str:
        """Extract the BGP configuration section."""
        bgp_pattern = r'router bgp\s+\d+\s*\n(.*?)(?=^!|\Z)'
        match = re.search(bgp_pattern, content, re.MULTILINE | re.DOTALL)
        return match.group(1) if match else ''
    
    def _extract_bgp_router_id(self, content: str) -> str:
        """Extract BGP router ID from configuration."""
        router_id_pattern = r'bgp router-id\s+(\S+)'
        match = re.search(router_id_pattern, content)
        return match.group(1) if match else ''
    
    def create_snapshot(self, configs: Dict[str, Any], snapshot_name: str) -> str:
        """
        Create a snapshot of the configurations.
        
        Args:
            configs: Dictionary containing configurations
            snapshot_name: Name for the snapshot
            
        Returns:
            Path to the snapshot file
        """
        snapshot_dir = Path('snapshots')
        snapshot_dir.mkdir(exist_ok=True)
        
        snapshot_path = snapshot_dir / f'{snapshot_name}.json'
        with open(snapshot_path, 'w') as f:
            json.dump(configs, f, indent=2)
        
        return str(snapshot_path)
    
    def _detect_config_format(self, content: str) -> str:
        """Detect the format of the configuration file."""
        content = content.lower()
        
        # Cisco IOS format detection
        if any(keyword in content for keyword in ['cisco', 'ios', 'interface', 'ip address', 'router']):
            return 'Cisco'
        
        # Juniper Junos format detection
        if any(keyword in content for keyword in ['juniper', 'junos', 'set', 'interfaces', 'routing-options']):
            return 'Juniper'
        
        return 'Generic'
    
    def _parse_cisco_config(self, content: str) -> Dict[str, Any]:
        """Parse Cisco IOS configuration."""
        config = {
            'device_type': 'Cisco',
            'interfaces': [],
            'raw_config': content
        }
        
        # Parse interfaces
        interface_pattern = r'interface\s+(\S+)'
        ip_pattern = r'ip\s+address\s+(\d+\.\d+\.\d+\.\d+)\s+(\d+\.\d+\.\d+\.\d+)'
        
        current_interface = None
        for line in content.split('\n'):
            interface_match = re.match(interface_pattern, line.strip())
            if interface_match:
                current_interface = {
                    'name': interface_match.group(1),
                    'ip_address': None,
                    'subnet_mask': None
                }
                config['interfaces'].append(current_interface)
            elif current_interface:
                ip_match = re.match(ip_pattern, line.strip())
                if ip_match:
                    current_interface['ip_address'] = ip_match.group(1)
                    current_interface['subnet_mask'] = ip_match.group(2)
        
        return config
    
    def _parse_juniper_config(self, content: str) -> Dict[str, Any]:
        """Parse Juniper Junos configuration."""
        config = {
            'device_type': 'Juniper',
            'interfaces': [],
            'raw_config': content
        }
        
        # Parse interfaces
        interface_pattern = r'set\s+interfaces\s+(\S+)\s+unit\s+\d+\s+family\s+inet\s+address\s+(\d+\.\d+\.\d+\.\d+/\d+)'
        
        for line in content.split('\n'):
            match = re.match(interface_pattern, line.strip())
            if match:
                interface_name = match.group(1)
                ip_address = match.group(2).split('/')[0]
                subnet_mask = self._cidr_to_mask(int(match.group(2).split('/')[1]))
                
                config['interfaces'].append({
                    'name': interface_name,
                    'ip_address': ip_address,
                    'subnet_mask': subnet_mask
                })
        
        return config
    
    def _parse_generic_config(self, content: str) -> Dict[str, Any]:
        """Parse generic configuration format."""
        config = {
            'device_type': 'Generic',
            'interfaces': [],
            'raw_config': content
        }
        
        # Try to find IP addresses and interfaces
        ip_pattern = r'(\d+\.\d+\.\d+\.\d+)(?:/(\d+))?'
        interface_pattern = r'(?:interface|port|eth)\s*[:=]?\s*(\S+)'
        
        for line in content.split('\n'):
            # Look for interfaces
            interface_match = re.search(interface_pattern, line, re.IGNORECASE)
            if interface_match:
                interface = {
                    'name': interface_match.group(1),
                    'ip_address': None,
                    'subnet_mask': None
                }
                
                # Look for IP address in the same line
                ip_match = re.search(ip_pattern, line)
                if ip_match:
                    interface['ip_address'] = ip_match.group(1)
                    if ip_match.group(2):
                        interface['subnet_mask'] = self._cidr_to_mask(int(ip_match.group(2)))
                
                config['interfaces'].append(interface)
        
        return config
    
    def _cidr_to_mask(self, cidr: int) -> str:
        """Convert CIDR notation to subnet mask."""
        mask = (0xffffffff >> (32 - cidr)) << (32 - cidr)
        return f"{(mask >> 24) & 0xff}.{(mask >> 16) & 0xff}.{(mask >> 8) & 0xff}.{mask & 0xff}" 