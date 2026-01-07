import sys
import os
import requests
import json
import numpy as np

# Add project root to path to import app if needed, but we used requests
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

BASE_URL = "http://localhost:5001/api"

def test_reverse_indicator():
    print("Testing Reverse Indicator API...")
    
    # 1. Clear Data
    # We can't easily clear data without affecting user state if the server is running.
    # But we can add a new distinct node.
    
    # Check if server is running by getting data
    try:
        requests.get(f"{BASE_URL}/data")
    except requests.exceptions.ConnectionError:
        print("Server not running. Please start the backend server to run this test.")
        return

    # 2. Add a test node with Indicator 2 (Right)
    # perform_operation 'add_node' doesn't let us set indicator directly.
    # We add node, then update property.
    print("Adding test node...")
    add_resp = requests.post(f"{BASE_URL}/operation", json={
        'operation': 'add_node',
        'params': {'x': 1000, 'y': 1000, 'lane_id': 999}
    })
    
    if add_resp.status_code != 200:
        print("Failed to add node")
        return

    nodes = add_resp.json()['nodes']
    # Find our node (approx x=1000, y=1000)
    test_node_id = None
    for n in nodes:
        if abs(n[1] - 1000) < 0.1 and abs(n[2] - 1000) < 0.1:
            test_node_id = n[0]
            break
            
    if test_node_id is None:
        print("Test node not found")
        return
        
    print(f"Test Node ID: {test_node_id}")
    
    # 3. Set Indicator to 2 (Right)
    print("Setting Indicator to 2 (Right)...")
    requests.post(f"{BASE_URL}/operation", json={
        'operation': 'update_node_properties',
        'params': {
            'point_ids': [test_node_id],
            'indicator': 2
        }
    })
    
    # Verify
    data = requests.get(f"{BASE_URL}/data").json()
    node = next(n for n in data['nodes'] if n[0] == test_node_id)
    print(f"Current Indicator: {node[6]}")
    assert node[6] == 2, "Indicator should be 2"
    
    # Store initial Yaw
    initial_yaw = node[3]
    print(f"Initial Yaw: {initial_yaw}")
    
    # 4. Reverse Indicator (2 -> 3)
    print("Reversing Indicator (Should be 2 -> 3)...")
    requests.post(f"{BASE_URL}/operation", json={
        'operation': 'reverse_indicators',
        'params': {
            'point_ids': [test_node_id]
        }
    })
    
    # Verify
    data = requests.get(f"{BASE_URL}/data").json()
    node = next(n for n in data['nodes'] if n[0] == test_node_id)
    print(f"Current Indicator: {node[6]}")
    assert node[6] == 3, "Indicator should be 3"
    assert node[3] == initial_yaw, f"Yaw changed! {initial_yaw} -> {node[3]}"
    print("Yaw validation passed (Unchanged).")

    # 5. Reverse Indicator again (3 -> 2)
    print("Reversing Indicator again (Should be 3 -> 2)...")
    requests.post(f"{BASE_URL}/operation", json={
        'operation': 'reverse_indicators',
        'params': {
            'point_ids': [test_node_id]
        }
    })
    
    # Verify
    data = requests.get(f"{BASE_URL}/data").json()
    node = next(n for n in data['nodes'] if n[0] == test_node_id)
    print(f"Current Indicator: {node[6]}")
    assert node[6] == 2, "Indicator should be 2"
    
    # Cleanup single node
    print("Cleaning up single node...")
    requests.post(f"{BASE_URL}/operation", json={
        'operation': 'delete_points',
        'params': {'point_ids': [test_node_id]}
    })

    # --- Test Multiple Nodes ---
    print("\nTesting Multiple Nodes...")
    # Add 2 nodes: one with 2 (Right), one with 3 (Left)
    params_multi = {
        'points': [
            {'x': 1010, 'y': 1010},
            {'x': 1020, 'y': 1020}
        ],
        'lane_id': 999,
        'connect_to_start_id': None
    }
    resp = requests.post(f"{BASE_URL}/operation", json={'operation': 'batch_add_nodes', 'params': params_multi})
    nodes_all = resp.json()['nodes']
    
    # Identify our new nodes (last 2 added ideally, or by position)
    multi_ids = []
    for n in nodes_all:
        if (abs(n[1] - 1010) < 0.1 and abs(n[2] - 1010) < 0.1) or \
           (abs(n[1] - 1020) < 0.1 and abs(n[2] - 1020) < 0.1):
            multi_ids.append(n[0])
            
    if len(multi_ids) < 2:
        print("Failed to add multiple nodes")
        return
        
    id1, id2 = multi_ids[0], multi_ids[1]
    
    # Set ID1 -> 2 (Right), ID2 -> 3 (Left)
    requests.post(f"{BASE_URL}/operation", json={'operation': 'update_node_properties', 'params': {'point_ids': [id1], 'indicator': 2}})
    requests.post(f"{BASE_URL}/operation", json={'operation': 'update_node_properties', 'params': {'point_ids': [id2], 'indicator': 3}})
    
    print(f"Node {id1}: Ind=2. Node {id2}: Ind=3.")
    
    # Reverse Both
    print("Reversing both...")
    requests.post(f"{BASE_URL}/operation", json={
        'operation': 'reverse_indicators',
        'params': {'point_ids': [id1, id2]}
    })
    
    # Verify
    data = requests.get(f"{BASE_URL}/data").json()
    n1 = next(n for n in data['nodes'] if n[0] == id1)
    n2 = next(n for n in data['nodes'] if n[0] == id2)
    
    print(f"Node {id1}: Ind={n1[6]} (Expected 3)")
    print(f"Node {id2}: Ind={n2[6]} (Expected 2)")
    
    assert n1[6] == 3, f"Node {id1} failed swap"
    assert n2[6] == 2, f"Node {id2} failed swap"
    
    # Cleanup
    requests.post(f"{BASE_URL}/operation", json={'operation': 'delete_points', 'params': {'point_ids': [id1, id2]}})
    print("Multiple nodes test passed!")

    
    print("Test Validated Successfully!")

if __name__ == "__main__":
    test_reverse_indicator()
