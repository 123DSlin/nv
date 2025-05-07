"""
Network verification engine with fallback mode.
"""

import json
import os
import time
from typing import Dict, Any, List
import logging
import re
from src.network_verifier.model_layer.topology_builder import TopologyBuilder
from src.network_verifier.data_layer.config_loader import ConfigLoader

logger = logging.getLogger(__name__)

class VerificationEngine:
    """Verifies network properties using basic checks when Batfish is not available."""
    
    def __init__(self, use_batfish=True):
        """Initialize the verification engine."""
        self.use_batfish = use_batfish
        self.results = {}
        if use_batfish:
            try:
                self._init_batfish_client()
            except Exception as e:
                logger.warning(f"Failed to initialize Batfish client: {str(e)}")
                self.use_batfish = False
        self.snapshot_dir = "snapshots"
        self.report_dir = "reports"
        
        # Create directories if they don't exist
        os.makedirs(self.snapshot_dir, exist_ok=True)
        os.makedirs(self.report_dir, exist_ok=True)
    
    def verify_network_properties(self, snapshot_name: str, properties: Dict[str, Any]) -> Dict[str, Any]:
        """Verify network properties using Batfish."""
        try:
            self._init_batfish_client()
            self._init_snapshot(snapshot_name)
            return self._run_verification(properties)
        except Exception as e:
            raise Exception(f"Error verifying network properties: {str(e)}")
            
    def verify_network_properties_local(self, configs: Dict[str, Any]) -> Dict[str, Any]:
        """
        Perform local verification of network properties.
        
        Args:
            configs: Dictionary of device configurations
            
        Returns:
            Dictionary containing verification results
        """
        try:
            # Initialize results dictionary
            results = {
                'overall_status': 'PASSED',
                'checks': {}
            }
            
            # Check connectivity
            connectivity_results = self._check_connectivity(configs)
            results['checks']['reachability'] = {
                'status': connectivity_results['status'],
                'description': 'Basic connectivity check',
                'details': connectivity_results['details']
            }
            
            # Check BGP peering
            bgp_results = self._check_bgp_peering(configs)
            results['checks']['bgp_peering'] = {
                'status': bgp_results['status'],
                'description': 'BGP peering check',
                'details': bgp_results['details']
            }
            
            # Check ACL consistency
            acl_results = self._check_acl_consistency(configs)
            results['checks']['acl_consistency'] = {
                'status': acl_results['status'],
                'description': 'ACL consistency check',
                'details': acl_results['details']
            }
            
            # Update overall status if any check failed
            if any(check['status'] == 'FAILED' for check in results['checks'].values()):
                results['overall_status'] = 'FAILED'
            
            return results
            
        except Exception as e:
            logger.error(f"Local verification failed: {str(e)}")
            return {
                'overall_status': 'ERROR',
                'checks': {
                    'error': {
                        'status': 'ERROR',
                        'description': f'Local verification failed: {str(e)}',
                        'details': {}
                    }
                }
            }
            
    def _check_connectivity(self, configs: Dict) -> Dict:
        """Check basic network connectivity."""
        check = {
            "name": "Connectivity",
            "status": "PASS",
            "description": "Basic network connectivity check",
            "details": []
        }
        
        # Check if devices have interfaces configured
        for device, config in configs.items():
            if not config.get("interfaces"):
                check["status"] = "FAIL"
                check["details"].append(f"Device {device} has no interfaces configured")
                
        return check
        
    def _check_bgp_peering(self, configs: Dict) -> Dict:
        """Check BGP peering configuration."""
        check = {
            "name": "BGP Peering",
            "status": "PASS",
            "description": "BGP peering configuration check",
            "details": []
        }
        
        # Check if devices have BGP neighbors configured
        for device, config in configs.items():
            if not config.get("bgp"):
                check["status"] = "FAIL"
                check["details"].append(f"Device {device} has no BGP configuration")
                
        return check
        
    def _check_acl_consistency(self, configs: Dict) -> Dict:
        """Check ACL consistency across devices."""
        check = {
            "name": "ACL Consistency",
            "status": "PASS",
            "description": "ACL consistency check",
            "details": []
        }
        
        # Check if devices have consistent ACL configurations
        acls = {}
        for device, config in configs.items():
            if "acls" in config:
                acls[device] = config["acls"]
                
        if not acls:
            check["status"] = "WARNING"
            check["details"].append("No ACLs found in configurations")
            
        return check
    
    def _perform_check(self, check_name: str, params: Dict[str, Any], configs: Dict[str, Any]) -> Dict[str, Any]:
        """
        Perform a specific verification check.
        
        Args:
            check_name: Name of the check to perform
            params: Parameters for the check
            configs: Network configurations
            
        Returns:
            Dictionary containing check results
        """
        check_methods = {
            "reachability": self._check_reachability,
            "isolation": self._check_isolation,
            "forwarding_loops": self._check_forwarding_loops,
            "bgp_peering": self._check_bgp_peering,
            "acl_consistency": self._check_acl_consistency,
            "route_table": self._check_route_table
        }
        
        if check_name not in check_methods:
            return {"status": "ERROR", "message": f"Unknown check: {check_name}"}
        
        try:
            return check_methods[check_name](params, configs)
        except Exception as e:
            logger.error(f"Error performing check {check_name}: {str(e)}")
            return {"status": "ERROR", "message": str(e)}
    
    def _check_reachability(self, params: Dict[str, Any], configs: Dict[str, Any]) -> Dict[str, Any]:
        """Basic reachability check."""
        try:
            # Simple check: verify that interfaces have valid IP addresses
            valid_ips = True
            interfaces = []
            
            for device, config in configs.items():
                if 'interfaces' in config:
                    for interface in config['interfaces']:
                        if interface.get('ip_address'):
                            if not self._is_valid_ip(interface['ip_address']):
                                valid_ips = False
                            interfaces.append(interface)
            
            return {
                "status": "PASSED" if valid_ips and interfaces else "FAILED",
                "message": "Basic reachability check completed",
                "details": {
                    "valid_ips": valid_ips,
                    "interface_count": len(interfaces)
                }
            }
        except Exception as e:
            return {"status": "ERROR", "message": str(e)}
    
    def _check_isolation(self, params: Dict[str, Any], configs: Dict[str, Any]) -> Dict[str, Any]:
        """Basic isolation check."""
        try:
            # Simple check: verify that interfaces have different subnets
            subnets = set()
            conflicts = []
            
            for device, config in configs.items():
                if 'interfaces' in config:
                    for interface in config['interfaces']:
                        if interface.get('ip_address') and interface.get('subnet_mask'):
                            subnet = self._get_subnet(interface['ip_address'], interface['subnet_mask'])
                            if subnet in subnets:
                                conflicts.append(subnet)
                            subnets.add(subnet)
            
            return {
                "status": "PASSED" if not conflicts else "FAILED",
                "message": "Basic isolation check completed",
                "details": {
                    "subnet_conflicts": conflicts
                }
            }
        except Exception as e:
            return {"status": "ERROR", "message": str(e)}
    
    def check_forwarding_loops(self, params: Dict[str, Any], configs: Dict[str, Any]) -> Dict[str, Any]:
        """Robust forwarding loops check: returns all unique cycles (labels) in the network."""
        import traceback
        try:
            mode = params.get("mode", "global")
            node = params.get("node")
            logger.info(f"[LoopCheck] mode={mode}, node={node}")
            # 构建拓扑
            topology_builder = TopologyBuilder()
            topology = topology_builder.build_topology(configs)
            nodes = topology.get("nodes", [])
            edges = topology.get("edges", [])
            logger.info(f"[LoopCheck] nodes={nodes}")
            logger.info(f"[LoopCheck] edges={edges}")
            if not nodes or not edges:
                logger.error("[LoopCheck] No nodes or edges in topology, cannot check loops.")
                return {"status": "ERROR", "message": "No nodes or edges in topology, cannot check loops."}
            id2label = {n["id"]: n.get("label", str(n["id"])) for n in nodes if "id" in n}
            label2id = {n.get("label", str(n["id"])): n["id"] for n in nodes if "id" in n}
            # 建邻接表
            graph = {n["id"]: set() for n in nodes if "id" in n}
            for edge in edges:
                u, v = edge.get("from"), edge.get("to")
                if u in graph and v in graph:
                    graph[u].add(v)
                    graph[v].add(u)
            logger.info(f"[LoopCheck] graph={graph}")
            # 环路收集
            cycles = set()
            def canonical_cycle(path):
                labels = [id2label[i] for i in path]
                min_idx = labels.index(min(labels))
                norm1 = labels[min_idx:] + labels[:min_idx]
                norm2 = list(reversed(labels))
                min_idx2 = norm2.index(min(norm2))
                norm2 = norm2[min_idx2:] + norm2[:min_idx2]
                return tuple(norm1) if tuple(norm1) < tuple(norm2) else tuple(norm2)
            def dfs(start, current, path, visited, parent):
                for neighbor in graph[current]:
                    if neighbor == parent:
                        continue
                    if neighbor == start and len(path) >= 3:
                        cycle = canonical_cycle(path)
                        cycles.add(cycle)
                    elif neighbor not in visited:
                        visited.add(neighbor)
                        dfs(start, neighbor, path + [neighbor], visited, current)
                        visited.remove(neighbor)
            if mode == "global":
                for nid in graph:
                    dfs(nid, nid, [nid], set([nid]), None)
            elif mode == "node":
                if not node:
                    logger.error("[LoopCheck] Node parameter is required for node mode")
                    return {"status": "ERROR", "message": "Node parameter is required for node mode"}
                node_id = label2id.get(node)
                if not node_id:
                    logger.error(f"[LoopCheck] Node {node} not found")
                    return {"status": "ERROR", "message": f"Node {node} not found"}
                dfs(node_id, node_id, [node_id], set([node_id]), None)
            else:
                logger.error(f"[LoopCheck] Unknown mode: {mode}")
                return {"status": "ERROR", "message": f"Unknown mode: {mode}"}
            loops_list = [list(c) for c in cycles]
            logger.info(f"[LoopCheck] loops_list={loops_list}")
            return {
                "status": "PASSED" if not loops_list else "FAILED",
                "message": "Forwarding loops check completed",
                "details": {"loops": loops_list}
            }
        except Exception as e:
            logger.error(f"[LoopCheck] Exception: {str(e)}")
            traceback.print_exc()
            return {"status": "ERROR", "message": f"Exception: {str(e)}"}
    
    def _check_route_table(self, params: Dict[str, Any], configs: Dict[str, Any]) -> Dict[str, Any]:
        """Basic route table check."""
        try:
            # Simple check: look for routing configuration
            route_configs = []
            
            for device, config in configs.items():
                if 'raw_config' in config:
                    if re.search(r'ip\s+route|router|ospf|eigrp|rip', config['raw_config'], re.IGNORECASE):
                        route_configs.append(device)
            
            return {
                "status": "PASSED" if route_configs else "FAILED",
                "message": "Basic route table check completed",
                "details": {
                    "devices_with_routes": route_configs
                }
            }
        except Exception as e:
            return {"status": "ERROR", "message": str(e)}
    
    def _is_valid_ip(self, ip: str) -> bool:
        """Check if an IP address is valid."""
        try:
            parts = ip.split('.')
            return len(parts) == 4 and all(0 <= int(part) <= 255 for part in parts)
        except:
            return False
    
    def _get_subnet(self, ip: str, mask: str) -> str:
        """Get subnet from IP and mask."""
        try:
            ip_parts = [int(x) for x in ip.split('.')]
            mask_parts = [int(x) for x in mask.split('.')]
            subnet_parts = [ip_parts[i] & mask_parts[i] for i in range(4)]
            return '.'.join(str(x) for x in subnet_parts)
        except:
            return ''

    def _init_batfish_client(self):
        # Initialize Batfish client
        pass

    def get_results(self):
        return self.results

    def verify_reachability(self, source: str, target: str, config_files: List[str]) -> Dict[str, Any]:
        """
        Verify reachability between two nodes in the network.
        
        Args:
            source: Source node name
            target: Target node name
            config_files: List of configuration file paths
            
        Returns:
            Dict containing reachability result with the following keys:
            - reachable: bool indicating if the path exists
            - path: list of nodes in the path (if reachable)
            - reason: string explaining why the path is not reachable (if not reachable)
        """
        try:
            # 加载所有配置文件
            configs = {}
            loader = ConfigLoader()
            for file_path in config_files:
                file_configs = loader.load_configs(file_path)
                configs.update(file_configs)
            # Build topology from configs
            topology_builder = TopologyBuilder()
            topology = topology_builder.build_topology(configs)
            
            # Get nodes and edges from topology
            nodes = topology.get("nodes", [])
            edges = topology.get("edges", [])
            
            # Create adjacency list for graph traversal
            graph = {}
            for node in nodes:
                graph[node["id"]] = []
            
            for edge in edges:
                from_node = edge["from"]
                to_node = edge["to"]
                graph[from_node].append(to_node)
                graph[to_node].append(from_node)  # Assuming bidirectional links
            
            # Find source and target nodes
            source_node = next((node for node in nodes if node["label"] == source), None)
            target_node = next((node for node in nodes if node["label"] == target), None)
            
            if not source_node:
                return {
                    "reachable": False,
                    "reason": f"Source node {source} not found in topology"
                }
            
            if not target_node:
                return {
                    "reachable": False,
                    "reason": f"Target node {target} not found in topology"
                }
            
            # BFS to find path
            visited = set()
            queue = [(source_node["id"], [source_node["id"]])]
            
            while queue:
                current_node, path = queue.pop(0)
                
                if current_node == target_node["id"]:
                    # Convert node IDs to labels
                    path_labels = [next(node["label"] for node in nodes if node["id"] == node_id) for node_id in path]
                    return {
                        "reachable": True,
                        "path": path_labels
                    }
                
                if current_node not in visited:
                    visited.add(current_node)
                    for neighbor in graph[current_node]:
                        if neighbor not in visited:
                            queue.append((neighbor, path + [neighbor]))
            
            return {
                "reachable": False,
                "reason": "No path found between source and target nodes"
            }
            
        except Exception as e:
            logger.error(f"Error in reachability verification: {str(e)}")
            return {
                "reachable": False,
                "reason": f"Error during verification: {str(e)}"
            }

    def find_all_paths(self, source: str, target: str, config_files: List[str], path_strategy: str = "shortest") -> Dict[str, Any]:
        """
        Find all paths between source and target nodes in the network.
        Returns all paths and the best path based on the selected strategy.
        
        Args:
            source: Source node name
            target: Target node name
            config_files: List of configuration file paths
            path_strategy: Strategy for selecting the best path
                - "shortest": Path with minimum number of hops
                - "core_preferred": Path that goes through core devices when possible
                - "border_preferred": Path that goes through border devices when possible
                - "redundant": Path that shares minimum nodes with other paths
        """
        try:
            # 加载所有配置文件
            from src.network_verifier.data_layer.config_loader import ConfigLoader
            configs = {}
            loader = ConfigLoader()
            for file_path in config_files:
                file_configs = loader.load_configs(file_path)
                configs.update(file_configs)
            # Build topology
            topology_builder = TopologyBuilder()
            topology = topology_builder.build_topology(configs)
            nodes = topology.get("nodes", [])
            edges = topology.get("edges", [])
            # 构建邻接表
            graph = {}
            for node in nodes:
                graph[node["id"]] = []
            for edge in edges:
                from_node = edge["from"]
                to_node = edge["to"]
                graph[from_node].append(to_node)
                graph[to_node].append(from_node)
            # 找到源和目标节点ID
            source_node = next((node for node in nodes if node["label"] == source), None)
            target_node = next((node for node in nodes if node["label"] == target), None)
            if not source_node or not target_node:
                return {
                    "found": False,
                    "paths": [],
                    "best_path": [],
                    "reason": "Source or target node not found in topology"
                }
            # DFS查找所有路径
            all_paths = []
            def dfs(current, target, path, visited):
                if current == target:
                    all_paths.append(list(path))
                    return
                for neighbor in graph[current]:
                    if neighbor not in visited:
                        path.append(neighbor)
                        visited.add(neighbor)
                        dfs(neighbor, target, path, visited)
                        path.pop()
                        visited.remove(neighbor)
            dfs(source_node["id"], target_node["id"], [source_node["id"]], set([source_node["id"]]))
            # 路径ID转label
            def id2label(path):
                return [next(node["label"] for node in nodes if node["id"] == node_id) for node_id in path]
            all_paths_label = [id2label(p) for p in all_paths]
            
            # 根据策略选择最佳路径
            best_path = []
            if all_paths:
                if path_strategy == "shortest":
                    best_path = min(all_paths, key=len)
                elif path_strategy == "core_preferred":
                    # 优先选择经过核心设备的路径
                    def core_score(path):
                        core_count = sum(1 for node_id in path if any(n["id"] == node_id and "core" in n.get("group", "").lower() for n in nodes))
                        return (-core_count, len(path))  # 负号使得核心设备多的路径优先
                    best_path = min(all_paths, key=core_score)
                elif path_strategy == "border_preferred":
                    # 优先选择经过边界设备的路径
                    def border_score(path):
                        border_count = sum(1 for node_id in path if any(n["id"] == node_id and "border" in n.get("group", "").lower() for n in nodes))
                        return (-border_count, len(path))  # 负号使得边界设备多的路径优先
                    best_path = min(all_paths, key=border_score)
                elif path_strategy == "redundant":
                    # 选择与其他路径共享节点最少的路径
                    def redundancy_score(path):
                        path_nodes = set(path)
                        shared_nodes = sum(len(path_nodes.intersection(set(p))) for p in all_paths if p != path)
                        return (shared_nodes, len(path))
                    best_path = min(all_paths, key=redundancy_score)
                else:
                    # 默认使用最短路径
                    best_path = min(all_paths, key=len)
            
            best_path_label = id2label(best_path) if best_path else []
            return {
                "found": bool(all_paths),
                "paths": all_paths_label,
                "best_path": best_path_label,
                "reason": "" if all_paths else "No path found between source and target nodes"
            }
        except Exception as e:
            logger.error(f"Error finding all paths: {str(e)}")
            return {
                "found": False,
                "paths": [],
                "best_path": [],
                "reason": f"Error during path finding: {str(e)}"
            }

    def find_disjoint_paths(self, source: str, target: str, config_files: List[str], mode: str = "node", max_paths: int = 2) -> Dict[str, Any]:
        """
        Find node- or edge-disjoint paths between source and target.
        Args:
            source: Source node name
            target: Target node name
            config_files: List of configuration file paths
            mode: 'node' or 'edge'
            max_paths: number of disjoint paths to find
        Returns:
            Dict with found (bool), paths (list of label lists), type (node/edge), reason
        """
        try:
            from src.network_verifier.data_layer.config_loader import ConfigLoader
            import copy
            configs = {}
            loader = ConfigLoader()
            for file_path in config_files:
                file_configs = loader.load_configs(file_path)
                configs.update(file_configs)
            topology_builder = TopologyBuilder()
            topology = topology_builder.build_topology(configs)
            nodes = topology.get("nodes", [])
            edges = topology.get("edges", [])
            graph = {}
            for node in nodes:
                graph[node["id"]] = []
            for edge in edges:
                from_node = edge["from"]
                to_node = edge["to"]
                graph[from_node].append(to_node)
                graph[to_node].append(from_node)
            source_node = next((node for node in nodes if node["label"] == source), None)
            target_node = next((node for node in nodes if node["label"] == target), None)
            if not source_node or not target_node:
                return {"found": False, "paths": [], "type": mode, "reason": "Source or target node not found in topology"}
            def id2label(path):
                return [next(node["label"] for node in nodes if node["id"] == node_id) for node_id in path]
            paths = []
            G = copy.deepcopy(graph)
            for _ in range(max_paths):
                # BFS for shortest path
                queue = [(source_node["id"], [source_node["id"]])]
                visited = set()
                found_path = None
                while queue:
                    current, path = queue.pop(0)
                    if current == target_node["id"]:
                        found_path = list(path)
                        break
                    if current not in visited:
                        visited.add(current)
                        for neighbor in G.get(current, []):
                            if neighbor not in path:
                                queue.append((neighbor, path + [neighbor]))
                if not found_path:
                    break
                paths.append(id2label(found_path))
                # 移除中间节点或边
                if mode == "node":
                    for node_id in found_path[1:-1]:
                        G.pop(node_id, None)
                        for v in G.values():
                            if node_id in v:
                                v.remove(node_id)
                elif mode == "edge":
                    for i in range(len(found_path)-1):
                        u, v = found_path[i], found_path[i+1]
                        if v in G.get(u, []):
                            G[u].remove(v)
                        if u in G.get(v, []):
                            G[v].remove(u)
            return {
                "found": len(paths) >= max_paths,
                "paths": paths,
                "type": mode,
                "reason": "" if paths else "No disjoint path found"
            }
        except Exception as e:
            logger.error(f"Error finding disjoint paths: {str(e)}")
            return {"found": False, "paths": [], "type": mode, "reason": f"Error: {str(e)}"} 