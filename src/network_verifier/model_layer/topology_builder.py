"""
Topology builder for network visualization.
"""

from typing import Dict, List, Any
import networkx as nx
import json

class TopologyBuilder:
    """Builds network topology from configuration data."""
    
    def __init__(self):
        self.graph = nx.Graph()
        self.node_counter = 0
        self.edge_counter = 0
    
    def build_topology(self, configs: Dict[str, Any]) -> Dict[str, List[Dict[str, Any]]]:
        """
        Build network topology from configuration data.
        
        Args:
            configs: Dictionary containing network device configurations
            
        Returns:
            Dictionary containing nodes and edges for visualization
        """
        self._reset()
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
        node_id = self.node_counter
        self.node_counter += 1
        
        # Count interfaces and extract key information
        interface_count = len(config.get('interfaces', []))
        ip_addresses = [
            intf.get('ip_address')
            for intf in config.get('interfaces', [])
            if intf.get('ip_address')
        ]
        
        # Build detailed device information
        device_info = {
            'id': node_id,
            'label': device_name,
            'title': (
                f"Device: {device_name}\n"
                f"Type: {config.get('device_type', 'Unknown')}\n"
                f"Interfaces: {interface_count}\n"
                f"IP Addresses: {', '.join(ip_addresses) if ip_addresses else 'None'}"
            ),
            'group': config.get('device_type', 'Unknown'),
            'value': 1,
            'details': {
                'interface_count': interface_count,
                'ip_addresses': ip_addresses,
                'device_type': config.get('device_type', 'Unknown')
            }
        }
        
        self.graph.add_node(node_id, **device_info)
    
    def _process_interface(self, device_name: str, interface: Dict[str, Any]):
        """Process interface information and add connections."""
        source_id = self._get_node_id(device_name)
        
        # Add interface details to the node
        if source_id is not None:
            node = self.graph.nodes[source_id]
            if 'interfaces' not in node:
                node['interfaces'] = []
            
            interface_info = {
                'name': interface.get('name', ''),
                'ip_address': interface.get('ip_address', ''),
                'subnet_mask': interface.get('subnet_mask', ''),
                'status': 'up' if interface.get('ip_address') else 'down'
            }
            node['interfaces'].append(interface_info)
            
            # If there's a neighbor, add the connection
            if interface.get('neighbor'):
                target_id = self._get_node_id(interface['neighbor'])
                if target_id is not None:
                    edge_info = {
                        'id': self.edge_counter,
                        'from': source_id,
                        'to': target_id,
                        'label': f"{interface.get('name', '')} -> {interface.get('neighbor_interface', '')}",
                        'title': (
                            f"Connection Details:\n"
                            f"Source: {device_name} ({interface.get('name', '')})\n"
                            f"Target: {interface['neighbor']} ({interface.get('neighbor_interface', '')})\n"
                            f"IP: {interface.get('ip_address', 'N/A')}"
                        )
                    }
                    self.graph.add_edge(source_id, target_id, **edge_info)
                    self.edge_counter += 1
    
    def _get_node_id(self, device_name: str) -> int:
        """Get the node ID for a device name."""
        for node_id, data in self.graph.nodes(data=True):
            if data['label'] == device_name:
                return node_id
        return None
    
    def _format_for_visualization(self) -> Dict[str, List[Dict[str, Any]]]:
        """Format the graph data for visualization."""
        nodes = []
        edges = []
        
        # Extract nodes
        for node_id, data in self.graph.nodes(data=True):
            node = {
                'id': node_id,
                'label': data['label'],
                'title': data['title'],
                'group': data['group'],
                'value': data['value']
            }
            nodes.append(node)
        
        # Extract edges
        for source, target, data in self.graph.edges(data=True):
            edge = {
                'id': data['id'],
                'from': source,
                'to': target,
                'label': data['label'],
                'title': data['title']
            }
            edges.append(edge)
        
        return {'nodes': nodes, 'edges': edges} 