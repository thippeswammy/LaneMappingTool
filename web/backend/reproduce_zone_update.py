import sys
import os
import numpy as np

# Add project root to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../../')))

from utils.data_manager import DataManager

def test_update_properties():
    # Init with dummy data
    nodes = np.array([
        [1, 0.0, 0.0, 0.0, 0, 3.5, 1],
        [2, 1.0, 1.0, 0.0, 0, 3.5, 1],
        [3, 2.0, 2.0, 0.0, 0, 3.5, 1]
    ])
    edges = np.array([])
    file_names = set()
    dm = DataManager(nodes, edges, file_names)
    
    print("Initial Nodes:")
    print(dm.nodes)

    # Test 1: Update Zone only
    print("\n--- Test 1: Update Zone to 5 for Node 1 ---")
    dm.update_node_properties([1], zone=5)
    print(dm.nodes)
    if dm.nodes[0, 4] == 5:
        print("PASS: Zone updated correctly.")
    else:
        print(f"FAIL: Zone is {dm.nodes[0, 4]}, expected 5.")

    # Test 2: Update Indicator only
    print("\n--- Test 2: Update Indicator to 3 for Node 2 ---")
    dm.update_node_properties([2], indicator=3)
    print(dm.nodes)
    if dm.nodes[1, 6] == 3:
        print("PASS: Indicator updated correctly.")
    else:
        print(f"FAIL: Indicator is {dm.nodes[1, 6]}, expected 3.")

    # Test 3: Update Both
    print("\n--- Test 3: Update Both for Node 3 ---")
    dm.update_node_properties([3], zone=2, indicator=4)
    print(dm.nodes)
    if dm.nodes[2, 4] == 2 and dm.nodes[2, 6] == 4:
         print("PASS: Both updated correctly.")
    else:
         print(f"FAIL: Expected Zone 2, Ind 4. Got Zone {dm.nodes[2, 4]}, Ind {dm.nodes[2, 6]}.")

    # Test 4: Default Zone 0 Logic?
    # The backend doesn't implement default logic, frontend sends explicit values.
    # Check what happens if we send integer 0
    print("\n--- Test 4: Update Zone to 0 ---")
    dm.update_node_properties([1], zone=0)
    print(dm.nodes)
    if dm.nodes[0, 4] == 0:
        print("PASS: Zone 0 handled correctly.")
    else:
        print("FAIL: Zone 0 failed.")

    # Test 5: String conversion
    print("\n--- Test 5: Update Zone with string '7' ---")
    dm.update_node_properties([2], zone='7')
    print(dm.nodes)
    if dm.nodes[1, 4] == 7:
        print("PASS: String zone converted correctly.")
    else:
        print(f"FAIL: String zone handling failed. Got {dm.nodes[1, 4]}.")

if __name__ == "__main__":
    test_update_properties()
