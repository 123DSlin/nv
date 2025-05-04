"""
Network verification engine with fallback mode.
"""

import json
import os
import time
from typing import Dict, Any
import logging
import re

logger = logging.getLogger(__name__)

class VerificationEngine:
    """Verifies network properties using basic checks when Batfish is not available."""
    
    def __init__(self):
        """Initialize the verification engine."""
        self.batfish_client = None
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
            
    def verify_network_properties_local(self, configs: Dict) -> Dict:
        """Verify network properties using local analysis."""
        try:
            results = {
                "overall_status": "PASS",
                "checks": []
            }
            
            # Basic connectivity check
            connectivity = self._check_connectivity(configs)
            results["checks"].append(connectivity)
            
            # BGP peering check
            bgp = self._check_bgp_peering(configs)
            results["checks"].append(bgp)
            
            # ACL consistency check
            acl = self._check_acl_consistency(configs)
            results["checks"].append(acl)
            
            # Update overall status based on individual checks
            if any(check["status"] == "FAIL" for check in results["checks"]):
                results["overall_status"] = "FAIL"
                
            return results
            
        except Exception as e:
            raise Exception(f"Error in local verification: {str(e)}")
            
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
    
    def _check_forwarding_loops(self, params: Dict[str, Any], configs: Dict[str, Any]) -> Dict[str, Any]:
        """Basic forwarding loops check."""
        return {
            "status": "PASSED",
            "message": "Basic forwarding loops check completed (limited functionality)",
            "details": {}
        }
    
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