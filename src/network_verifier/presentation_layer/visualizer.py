"""
Network visualization module.
"""

import json
import os
from typing import Dict, Any
import networkx as nx
import matplotlib.pyplot as plt

class NetworkVisualizer:
    """Visualizes network topology and verification results."""
    
    def __init__(self):
        """Initialize the visualizer."""
        self.output_dir = "static/images"
        os.makedirs(self.output_dir, exist_ok=True)
    
    def visualize_topology(self, configs: Dict[str, Any], output_file: str = "topology.png") -> str:
        """
        Generate a network topology visualization.
        
        Args:
            configs: Network configurations
            output_file: Output filename
            
        Returns:
            Path to the generated image
        """
        try:
            # Create a directed graph
            G = nx.DiGraph()
            
            # Add nodes (devices)
            for device_name, device_config in configs.items():
                G.add_node(device_name, type=device_config.get("type", "unknown"))
            
            # Add edges (connections)
            for device_name, device_config in configs.items():
                for interface in device_config.get("interfaces", []):
                    if "neighbor" in interface:
                        G.add_edge(device_name, interface["neighbor"])
            
            # Draw the graph
            plt.figure(figsize=(12, 8))
            pos = nx.spring_layout(G)
            nx.draw(G, pos, with_labels=True, node_color='lightblue', 
                   node_size=2000, font_size=10, font_weight='bold')
            
            # Save the image
            output_path = os.path.join(self.output_dir, output_file)
            plt.savefig(output_path)
            plt.close()
            
            return output_path
            
        except Exception as e:
            return f"Error generating visualization: {str(e)}"
    
    def visualize_verification_results(self, results: Dict[str, Any], output_file: str = "results.png") -> str:
        """
        Generate a visualization of verification results.
        
        Args:
            results: Verification results
            output_file: Output filename
            
        Returns:
            Path to the generated image
        """
        try:
            # Create a bar chart of check results
            checks = list(results["checks"].keys())
            statuses = [results["checks"][check]["status"] for check in checks]
            
            plt.figure(figsize=(12, 6))
            plt.bar(checks, [1 if s == "PASSED" else 0 for s in statuses])
            plt.title("Verification Results")
            plt.xticks(rotation=45)
            plt.yticks([0, 1], ["FAILED", "PASSED"])
            
            # Save the image
            output_path = os.path.join(self.output_dir, output_file)
            plt.savefig(output_path)
            plt.close()
            
            return output_path
            
        except Exception as e:
            return f"Error generating visualization: {str(e)}" 