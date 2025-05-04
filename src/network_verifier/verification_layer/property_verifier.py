"""
Property verifier for network control plane properties.
"""

from typing import Dict, List, Optional, Union
from batfish.client.session import Session
from batfish.datamodel import *
from batfish.question import bfq
from ..config import settings

class PropertyVerifier:
    """Handles verification of network control plane properties."""
    
    def __init__(self):
        self.session = Session(
            host=settings.batfish_host,
            port=settings.batfish_port
        )
        
    def verify_reachability(self, snapshot_name: str, 
                          source: str, 
                          destination: str,
                          protocol: str = "tcp",
                          dst_ports: List[int] = None) -> Dict:
        """
        Verify reachability between source and destination.
        
        Args:
            snapshot_name: Name of the snapshot to verify
            source: Source IP address or interface
            destination: Destination IP address or interface
            protocol: Protocol to test (tcp, udp, icmp)
            dst_ports: List of destination ports to test
            
        Returns:
            Dictionary containing reachability verification results
        """
        self.session.set_snapshot(snapshot_name)
        
        # Build reachability query
        query = bfq.reachability(
            pathConstraints=PathConstraints(
                startLocation=source,
                endLocation=destination
            ),
            headers=HeaderConstraints(
                protocols=protocol,
                dstPorts=dst_ports if dst_ports else None
            )
        )
        
        # Execute verification
        result = query.answer().frame()
        return {
            'status': 'reachable' if not result.empty else 'unreachable',
            'paths': result.to_dict('records') if not result.empty else []
        }
    
    def verify_isolation(self, snapshot_name: str,
                        source: str,
                        destination: str) -> Dict:
        """
        Verify isolation between source and destination.
        
        Args:
            snapshot_name: Name of the snapshot to verify
            source: Source IP address or interface
            destination: Destination IP address or interface
            
        Returns:
            Dictionary containing isolation verification results
        """
        self.session.set_snapshot(snapshot_name)
        
        # Build isolation query
        query = bfq.reachability(
            pathConstraints=PathConstraints(
                startLocation=source,
                endLocation=destination
            ),
            actions=FlowDisposition.DENIED_IN
        )
        
        # Execute verification
        result = query.answer().frame()
        return {
            'status': 'isolated' if result.empty else 'not_isolated',
            'violations': result.to_dict('records') if not result.empty else []
        }
    
    def verify_path_trace(self, snapshot_name: str,
                         source: str,
                         destination: str) -> Dict:
        """
        Trace and verify paths between source and destination.
        
        Args:
            snapshot_name: Name of the snapshot to verify
            source: Source IP address or interface
            destination: Destination IP address or interface
            
        Returns:
            Dictionary containing path trace results
        """
        self.session.set_snapshot(snapshot_name)
        
        # Build path trace query
        query = bfq.traceroute(
            startLocation=source,
            headers=HeaderConstraints(
                dstIps=destination
            )
        )
        
        # Execute verification
        result = query.answer().frame()
        return {
            'paths': result.to_dict('records') if not result.empty else [],
            'path_count': len(result) if not result.empty else 0
        }
    
    def verify_disjoint_paths(self, snapshot_name: str,
                            source: str,
                            destination: str) -> Dict:
        """
        Verify existence of disjoint paths between source and destination.
        
        Args:
            snapshot_name: Name of the snapshot to verify
            source: Source IP address or interface
            destination: Destination IP address or interface
            
        Returns:
            Dictionary containing disjoint paths verification results
        """
        self.session.set_snapshot(snapshot_name)
        
        # Build disjoint paths query
        query = bfq.reachability(
            pathConstraints=PathConstraints(
                startLocation=source,
                endLocation=destination
            ),
            actions=FlowDisposition.ACCEPTED
        )
        
        # Execute verification
        result = query.answer().frame()
        paths = result.to_dict('records') if not result.empty else []
        
        # Analyze paths for disjointness
        disjoint_paths = self._analyze_disjoint_paths(paths)
        
        return {
            'path_count': len(paths),
            'disjoint_paths': disjoint_paths,
            'paths': paths
        }
    
    def verify_forwarding_loops(self, snapshot_name: str) -> Dict:
        """
        Verify absence of forwarding loops in the network.
        
        Args:
            snapshot_name: Name of the snapshot to verify
            
        Returns:
            Dictionary containing forwarding loop verification results
        """
        self.session.set_snapshot(snapshot_name)
        
        # Build forwarding loop query
        query = bfq.detectLoops()
        
        # Execute verification
        result = query.answer().frame()
        return {
            'has_loops': not result.empty,
            'loops': result.to_dict('records') if not result.empty else []
        }
    
    def verify_bgp_peering(self, snapshot_name: str) -> Dict:
        """
        Verify BGP peering relationships and configurations.
        
        Args:
            snapshot_name: Name of the snapshot to verify
            
        Returns:
            Dictionary containing BGP peering verification results
        """
        self.session.set_snapshot(snapshot_name)
        
        # Build BGP peering query
        query = bfq.bgpSessionStatus()
        
        # Execute verification
        result = query.answer().frame()
        return {
            'peering_status': result.to_dict('records') if not result.empty else [],
            'established_count': len(result[result['Established_Status'] == 'ESTABLISHED']) if not result.empty else 0
        }
    
    def _analyze_disjoint_paths(self, paths: List[Dict]) -> List[List[Dict]]:
        """
        Analyze paths to identify disjoint paths.
        
        Args:
            paths: List of path dictionaries
            
        Returns:
            List of lists containing disjoint paths
        """
        if not paths:
            return []
            
        # Group paths by source and destination
        path_groups = {}
        for path in paths:
            key = (path['Start_Location'], path['End_Location'])
            if key not in path_groups:
                path_groups[key] = []
            path_groups[key].append(path)
        
        # Find disjoint paths within each group
        disjoint_paths = []
        for group in path_groups.values():
            if len(group) > 1:
                # Simple check for disjointness based on intermediate nodes
                # This is a simplified version - actual implementation would need
                # more sophisticated path comparison
                disjoint = []
                for path in group:
                    if not any(self._paths_share_nodes(path, p) for p in disjoint):
                        disjoint.append(path)
                if len(disjoint) > 1:
                    disjoint_paths.append(disjoint)
        
        return disjoint_paths
    
    def _paths_share_nodes(self, path1: Dict, path2: Dict) -> bool:
        """
        Check if two paths share any intermediate nodes.
        
        Args:
            path1: First path dictionary
            path2: Second path dictionary
            
        Returns:
            True if paths share nodes, False otherwise
        """
        nodes1 = set(path1.get('Nodes', []))
        nodes2 = set(path2.get('Nodes', []))
        return bool(nodes1.intersection(nodes2)) 