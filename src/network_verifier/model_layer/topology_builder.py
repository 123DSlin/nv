"""
Topology builder for network visualization.
"""

from typing import Dict, List, Any
import networkx as nx
import json
import logging

logger = logging.getLogger(__name__)

class TopologyBuilder:
    """Builds network topology from configuration data."""
    
    def __init__(self):
        self.graph = nx.Graph()
        self.node_counter = 0
        self.edge_counter = 0
        self.configs = {}
    
    def infer_group(self, device_name: str) -> str:
        name = device_name.lower()
        if 'core' in name:
            return 'core'
        if 'border' in name:
            return 'border'
        if 'dist' in name:
            return 'dist'
        if 'dept' in name:
            return 'dept'
        if 'host' in name:
            return 'host'
        return 'Unknown'

    def build_topology(self, configs: Dict[str, Any]) -> Dict[str, List[Dict[str, Any]]]:
        """
        Build network topology from configuration data.
        
        Args:
            configs: Dictionary containing network device configurations
            
        Returns:
            Dictionary containing nodes and edges for visualization
        """
        # 自动为每个设备分配 group 字段
        for device_name, config in configs.items():
            config['group'] = self.infer_group(device_name)
        self._reset()
        self.configs = configs
        self._process_configs(configs)
        return self._format_for_visualization()
    
    def _reset(self):
        """Reset the builder state."""
        self.graph = nx.Graph()
        self.node_counter = 0
        self.edge_counter = 0
    
    def _process_configs(self, configs: Dict[str, Any]):
        """Process configuration data and build the graph."""
        # First pass: add all devices
        for device_name, config in configs.items():
            self._add_device_node(device_name, config)
        
        # Second pass: process interfaces and connections
        for device_name, config in configs.items():
            if 'interfaces' in config:
                for interface in config['interfaces']:
                    self._process_interface(device_name, interface)
    
    def _add_device_node(self, device_name: str, config: Dict[str, Any]):
        """Add a device node to the graph."""
        try:
            # Count interfaces and extract key information
            interface_count = len(config.get('interfaces', []))
            ip_addresses = [
                intf.get('ip_address')
                for intf in config.get('interfaces', [])
                if intf.get('ip_address')
            ]
            
            # Build detailed device information
            device_info = {
                'id': device_name,  # Use device name as ID
                'label': device_name,
                'title': (
                    f"Device: {device_name}\n"
                    f"Type: {config.get('device_type', 'Unknown')}\n"
                    f"Interfaces: {interface_count}\n"
                    f"IP Addresses: {', '.join(ip_addresses) if ip_addresses else 'None'}"
                ),
                'group': config.get('group', 'Unknown'),
                'value': interface_count
            }
            
            self.graph.add_node(device_name, **device_info)
            
        except Exception as e:
            logger.error(f"Error adding device node {device_name}: {str(e)}")
    
    def _process_interface(self, device_name: str, interface: Dict[str, Any]) -> None:
        """Process interface details and connections."""
        try:
            # Extract interface information
            interface_name = interface.get('name', '')
            ip_address = interface.get('ip_address', '')
            subnet_mask = interface.get('subnet_mask', '')
            neighbor = interface.get('neighbor', {})
            
            # Add edge if neighbor information is available
            if neighbor and 'device' in neighbor:
                neighbor_device = neighbor['device']
                neighbor_interface = neighbor.get('interface', '')
                
                # Create edge ID
                edge_id = f"{device_name}_{interface_name}-{neighbor_device}_{neighbor_interface}"
                
                # Add edge to graph
                self.graph.add_edge(
                    device_name,
                    neighbor_device,
                    id=edge_id,
                    label=f"{interface_name}-{neighbor_interface}",
                    title=f"IP: {ip_address}\nNeighbor: {neighbor_device}"
                )
                
            # If no neighbor info but has IP, try to find potential connections
            elif ip_address and subnet_mask:
                # Look for other devices with interfaces in the same subnet
                for other_device, other_config in self.configs.items():
                    if other_device != device_name:
                        for other_interface in other_config.get('interfaces', []):
                            other_ip = other_interface.get('ip_address', '')
                            other_mask = other_interface.get('subnet_mask', '')
                            
                            if other_ip and other_mask and self._is_same_subnet(ip_address, subnet_mask, other_ip, other_mask):
                                # Create edge ID
                                edge_id = f"{device_name}_{interface_name}-{other_device}_{other_interface['name']}"
                                
                                # Add edge to graph
                                self.graph.add_edge(
                                    device_name,
                                    other_device,
                                    id=edge_id,
                                    label=f"{interface_name}-{other_interface['name']}",
                                    title=f"IP: {ip_address}\nConnected to: {other_ip}"
                                )
                                
        except Exception as e:
            logger.error(f"Error processing interface {interface_name} for device {device_name}: {str(e)}")
    
    def _is_same_subnet(self, ip1: str, mask1: str, ip2: str, mask2: str) -> bool:
        """Check if two IP addresses are in the same subnet."""
        try:
            # Convert IP and mask to integers
            ip1_parts = [int(x) for x in ip1.split('.')]
            mask1_parts = [int(x) for x in mask1.split('.')]
            ip2_parts = [int(x) for x in ip2.split('.')]
            mask2_parts = [int(x) for x in mask2.split('.')]
            
            # Calculate network addresses
            net1 = [ip1_parts[i] & mask1_parts[i] for i in range(4)]
            net2 = [ip2_parts[i] & mask2_parts[i] for i in range(4)]
            
            return net1 == net2
        except:
            return False
    
    def _get_node_id(self, device_name: str) -> int:
        """Get the node ID for a device name."""
        for node_id, data in self.graph.nodes(data=True):
            if data['label'] == device_name:
                return node_id
        return None
    
    def _format_for_visualization(self) -> Dict[str, List[Dict[str, Any]]]:
        """Format the graph data for visualization."""
        try:
            nodes = []
            edges = []
            
            # Extract nodes
            for node_id, data in self.graph.nodes(data=True):
                node = {
                    'id': node_id,
                    'label': data.get('label', node_id),
                    'title': data.get('title', ''),
                    'group': data.get('group', 'Unknown'),
                    'value': data.get('value', 1)
                }
                nodes.append(node)
            
            # Extract edges
            for source, target, data in self.graph.edges(data=True):
                edge = {
                    'id': data.get('id', f"{source}-{target}"),
                    'from': source,
                    'to': target,
                    'label': data.get('label', ''),
                    'title': data.get('title', '')
                }
                edges.append(edge)
            
            return {'nodes': nodes, 'edges': edges}
            
        except Exception as e:
            logger.error(f"Error formatting graph for visualization: {str(e)}")
            return {'nodes': [], 'edges': []} 