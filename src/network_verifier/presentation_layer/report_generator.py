"""
Report generator for network verification results.
"""

from typing import Dict, Any
import json
from pathlib import Path
from datetime import datetime

class ReportGenerator:
    """Generates reports from verification results."""
    
    def generate_report(self, results: Dict[str, Any], snapshot_name: str) -> str:
        """
        Generate a report from verification results.
        
        Args:
            results: Dictionary containing verification results
            snapshot_name: Name of the snapshot being verified
            
        Returns:
            Path to the generated report
        """
        try:
            # Create reports directory if it doesn't exist
            reports_dir = Path("reports")
            reports_dir.mkdir(exist_ok=True)
            
            # Generate report filename
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            report_filename = f"report_{snapshot_name}_{timestamp}.json"
            report_path = reports_dir / report_filename
            
            # Add metadata and summary to report
            report = {
                'metadata': {
                    'timestamp': datetime.now().isoformat(),
                    'snapshot_name': snapshot_name,
                    'version': '1.0',
                    'report_id': f"REPORT_{timestamp}"
                },
                'summary': {
                    'overall_status': results.get('overall_status', 'UNKNOWN'),
                    'total_checks': len(results.get('checks', {})),
                    'passed_checks': sum(1 for check in results.get('checks', {}).values() 
                                      if check.get('status') == 'PASSED'),
                    'failed_checks': sum(1 for check in results.get('checks', {}).values() 
                                      if check.get('status') == 'FAILED'),
                    'error_checks': sum(1 for check in results.get('checks', {}).values() 
                                      if check.get('status') == 'ERROR')
                },
                'results': results
            }
            
            # Add detailed analysis for each check
            report['analysis'] = {
                'reachability': self._analyze_reachability(results),
                'isolation': self._analyze_isolation(results),
                'bgp_peering': self._analyze_bgp_peering(results),
                'acl_consistency': self._analyze_acl_consistency(results),
                'route_table': self._analyze_route_table(results)
            }
            
            # Write report to file
            with open(report_path, 'w') as f:
                json.dump(report, f, indent=2)
            
            return str(report_path)
            
        except Exception as e:
            raise Exception(f"Failed to generate report: {str(e)}")
    
    def format_report(self, report: Dict[str, Any]) -> str:
        """
        Format a report for display.
        
        Args:
            report: Dictionary containing the report data
            
        Returns:
            Formatted report string
        """
        try:
            metadata = report['metadata']
            summary = report['summary']
            analysis = report.get('analysis', {})
            
            formatted = [
                "Network Verification Report",
                "=" * 30,
                f"\nReport ID: {metadata['report_id']}",
                f"Generated: {metadata['timestamp']}",
                f"Snapshot: {metadata['snapshot_name']}",
                f"Version: {metadata['version']}",
                
                "\nSummary",
                "-" * 20,
                f"Overall Status: {summary['overall_status']}",
                f"Total Checks: {summary['total_checks']}",
                f"Passed: {summary['passed_checks']}",
                f"Failed: {summary['failed_checks']}",
                f"Errors: {summary['error_checks']}",
                
                "\nDetailed Analysis",
                "-" * 20
            ]
            
            # Add analysis details
            for check_name, check_analysis in analysis.items():
                if check_analysis:
                    formatted.extend([
                        f"\n{check_name.upper()}:",
                        f"Status: {check_analysis.get('status', 'UNKNOWN')}",
                        "Details:",
                        json.dumps(check_analysis.get('details', {}), indent=2)
                    ])
            
            return "\n".join(formatted)
            
        except Exception as e:
            return f"Error formatting report: {str(e)}"
    
    def _analyze_reachability(self, results: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze reachability check results."""
        check = results.get('checks', {}).get('reachability', {})
        if not check:
            return None
            
        return {
            'status': check.get('status'),
            'details': {
                'valid_ips': check.get('details', {}).get('valid_ips'),
                'interface_count': check.get('details', {}).get('interface_count'),
                'recommendation': (
                    "All IP addresses are valid and interfaces are properly configured."
                    if check.get('status') == 'PASSED'
                    else "Review interface IP configurations for potential issues."
                )
            }
        }
    
    def _analyze_isolation(self, results: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze isolation check results."""
        check = results.get('checks', {}).get('isolation', {})
        if not check:
            return None
            
        return {
            'status': check.get('status'),
            'details': {
                'subnet_conflicts': check.get('details', {}).get('subnet_conflicts', []),
                'recommendation': (
                    "Network segments are properly isolated."
                    if check.get('status') == 'PASSED'
                    else "Review subnet configurations to resolve conflicts."
                )
            }
        }
    
    def _analyze_bgp_peering(self, results: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze BGP peering check results."""
        check = results.get('checks', {}).get('bgp_peering', {})
        if not check:
            return None
            
        return {
            'status': check.get('status'),
            'details': {
                'devices_with_bgp': check.get('details', {}).get('devices_with_bgp', []),
                'recommendation': (
                    "BGP configurations are properly set up."
                    if check.get('status') == 'PASSED'
                    else "Review BGP configurations for potential issues."
                )
            }
        }
    
    def _analyze_acl_consistency(self, results: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze ACL consistency check results."""
        check = results.get('checks', {}).get('acl_consistency', {})
        if not check:
            return None
            
        return {
            'status': check.get('status'),
            'details': {
                'devices_with_acl': check.get('details', {}).get('devices_with_acl', []),
                'recommendation': (
                    "ACL configurations are consistent across devices."
                    if check.get('status') == 'PASSED'
                    else "Review ACL configurations for consistency issues."
                )
            }
        }
    
    def _analyze_route_table(self, results: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze route table check results."""
        check = results.get('checks', {}).get('route_table', {})
        if not check:
            return None
            
        return {
            'status': check.get('status'),
            'details': {
                'devices_with_routes': check.get('details', {}).get('devices_with_routes', []),
                'recommendation': (
                    "Routing configurations are properly set up."
                    if check.get('status') == 'PASSED'
                    else "Review routing configurations for potential issues."
                )
            }
        } 