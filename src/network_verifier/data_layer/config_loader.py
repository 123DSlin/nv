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
        
        # Update interfaces with neighbor information (BGP neighbor IP match)
        for interface in interfaces:
            for neighbor in bgp_neighbors:
                if interface.get('ip_address') == neighbor.get('ip'):
                    interface['neighbor'] = neighbor
        
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
        
        # --- IP邻居自动推断 ---
        # 只有所有设备都加载完后再调用此逻辑（假设多次load_configs后再用self.configs）
        # 这里每次只处理当前设备，但会遍历self.configs中所有设备
        for this_dev, this_conf in self.configs.items():
            for iface in this_conf.get('interfaces', []):
                ip1 = iface.get('ip_address')
                mask1 = iface.get('subnet_mask')
                if not ip1 or not mask1:
                    continue
                # 跳过已有neighbor的接口（如BGP或手动指定）
                if iface.get('neighbor') and iface['neighbor']:
                    continue
                for other_dev, other_conf in self.configs.items():
                    if other_dev == this_dev:
                        continue
                    for oiface in other_conf.get('interfaces', []):
                        ip2 = oiface.get('ip_address')
                        mask2 = oiface.get('subnet_mask')
                        if not ip2 or not mask2:
                            continue
                        if self._is_same_subnet(ip1, mask1, ip2, mask2):
                            # 互为neighbor
                            iface['neighbor'] = {
                                'device': other_dev,
                                'interface': oiface.get('name', ''),
                                'ip_address': ip2
                            }
                            # 对端也加上neighbor（如果还没有）
                            if not oiface.get('neighbor'):
                                oiface['neighbor'] = {
                                    'device': this_dev,
                                    'interface': iface.get('name', ''),
                                    'ip_address': ip1
                                }
        return self.configs
    
    def _extract_interfaces(self, content: str) -> List[Dict[str, Any]]:
        """Extract interface information from configuration."""
        interfaces = []
        current_interface = None
        
        for line in content.split('\n'):
            line = line.strip()
            
            # Start of interface configuration
            if line.startswith('interface'):
                if current_interface:
                    interfaces.append(current_interface)
                current_interface = {
                    'name': line.split()[1],
                    'ip_address': '',
                    'subnet_mask': '',
                    'neighbor': {},
                    'status': 'down'
                }
            
            # Interface IP address
            elif current_interface and line.startswith('ip address'):
                parts = line.split()
                if len(parts) >= 4:
                    # 标准写法 ip address <ip> <mask>
                    current_interface['ip_address'] = parts[2]
                    current_interface['subnet_mask'] = parts[3]
                    current_interface['status'] = 'up'
                elif len(parts) == 3 and '/' in parts[2]:
                    # 支持 ip address <ip>/<prefix>
                    ip, prefix = parts[2].split('/')
                    current_interface['ip_address'] = ip
                    current_interface['subnet_mask'] = self._cidr_to_mask(int(prefix))
                    current_interface['status'] = 'up'
            
            # BGP neighbor configuration
            elif current_interface and line.startswith('neighbor'):
                parts = line.split()
                if len(parts) >= 2:
                    current_interface['neighbor'] = {
                        'device': parts[1],
                        'interface': parts[1].split('.')[-1] if '.' in parts[1] else ''
                    }
            
            # End of interface configuration
            elif line == '!' and current_interface:
                interfaces.append(current_interface)
                current_interface = None
        
        # Add the last interface if exists
        if current_interface:
            interfaces.append(current_interface)
        
        return interfaces
    
    def _extract_bgp_neighbors(self, content: str) -> List[Dict[str, Any]]:
        """Extract BGP neighbor information from configuration."""
        neighbors = []
        in_bgp_section = False
        
        for line in content.split('\n'):
            line = line.strip()
            
            # Start of BGP configuration
            if line.startswith('router bgp'):
                in_bgp_section = True
                continue
            
            # End of BGP configuration
            elif line == '!' and in_bgp_section:
                in_bgp_section = False
                continue
            
            # BGP neighbor configuration
            elif in_bgp_section and line.startswith('neighbor'):
                parts = line.split()
                if len(parts) >= 2:
                    neighbor = {
                        'ip': parts[1],
                        'as': '',
                        'interface': ''
                    }
                    
                    # Look for AS number
                    for next_line in content.split('\n'):
                        if f'neighbor {neighbor["ip"]}' in next_line and 'remote-as' in next_line:
                            neighbor['as'] = next_line.split('remote-as')[1].strip()
                            break
                    
                    # Find interface with matching IP
                    for interface in self._extract_interfaces(content):
                        if interface['ip_address'] == neighbor['ip']:
                            neighbor['interface'] = interface['name']
                            break
                    
                    neighbors.append(neighbor)
        
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
    
    def _is_same_subnet(self, ip1: str, mask1: str, ip2: str, mask2: str) -> bool:
        """Check if two IP addresses are in the same subnet."""
        try:
            ip1_parts = [int(x) for x in ip1.split('.')]
            mask1_parts = [int(x) for x in mask1.split('.')]
            ip2_parts = [int(x) for x in ip2.split('.')]
            mask2_parts = [int(x) for x in mask2.split('.')]
            net1 = [ip1_parts[i] & mask1_parts[i] for i in range(4)]
            net2 = [ip2_parts[i] & mask2_parts[i] for i in range(4)]
            return net1 == net2
        except:
            return False 