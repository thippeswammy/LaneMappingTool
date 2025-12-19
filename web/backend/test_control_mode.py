import sys
import os
import numpy as np

# Adjust path to import from the parent project
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

from utils.data_manager import DataManager
from web.backend.utils.curve_utils import find_path

def test_control_mode_backend():
    print("--- Testing Control Mode Backend Logic ---")
    
    # Setup DataManager with some dummy data
    # Nodes: [id, x, y, yaw, zone, width, indicator, (speed - optional/legacy)]
    nodes = np.array([
        [0, 0, 0, 0, 1, 3.5, 0],
        [1, 10, 0, 0, 1, 3.5, 0],
        [2, 20, 0, 0, 1, 3.5, 0],
        [3, 30, 0, 0, 2, 3.5, 0] # Different zone
    ])
    
    edges = np.array([
        [0, 1],
        [1, 2],
        [2, 3]
    ])
    
    file_names = ["Lane1.npy", "Lane2.npy", "Lane3.npy"]
    
    dm = DataManager(nodes, edges, file_names)
    
    # 1. Test update_node_properties
    print("\n1. Testing update_node_properties...")
    
    # Update Zone for node 1 to 5
    dm.update_node_properties([1], zone=5)
    assert dm.nodes[1, 4] == 5, f"Node 1 Zone should be 5, got {dm.nodes[1, 4]}"
    print("   Zone update passed.")
    
    # Update Indicator for node 2 to 2 (Right)
    dm.update_node_properties([2], indicator=2)
    assert dm.nodes[2, 6] == 2.0, f"Node 2 Indicator should be 2.0, got {dm.nodes[2, 6]}"
    print("   Indicator update passed.")
    
    # Batch update
    dm.update_node_properties([0, 3], zone=9, indicator=4)
    assert dm.nodes[0, 4] == 9 and dm.nodes[0, 6] == 4.0, "Node 0 batch update failed"
    assert dm.nodes[3, 4] == 9 and dm.nodes[3, 6] == 4.0, "Node 3 batch update failed"
    print("   Batch update passed.")
    
    # 2. Test get_path (find_path)
    print("\n2. Testing get_path logic...")
    path = find_path(dm.edges, 0, 3)
    print(f"   Path from 0 to 3: {path}")
    expected_path = [0, 1, 2, 3]
    assert path == expected_path, f"Path shoud be {expected_path}, got {path}"
    print("   Path finding passed.")
    
    print("\n--- All Backend Tests Passed ---")

if __name__ == "__main__":
    test_control_mode_backend()
