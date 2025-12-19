import numpy as np
import sys
import os

# Adjust path to import DataManager
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from utils.data_manager import DataManager

def test_id_synchronization():
    print("--- Testing ID Synchronization ---")
    
    # 1. Initialize with some data
    nodes = np.array([[0, 10, 10, 0, 0, 0, 0], [1, 20, 20, 0, 0, 0, 0]])
    edges = np.array([[0, 1]])
    file_names = ["lane0.npy"]
    
    dm = DataManager(nodes, edges, file_names)
    print(f"Initial next_point_id: {dm._next_point_id}") # Should be 2
    
    # 2. Simulate an 'undo' or 'apply_updates' that brings in a higher ID node
    # Simulating what happens in app.py's apply_updates or undo/redo
    # Manually setting nodes as if they came from history or client update
    new_nodes = np.array([[0, 10, 10, 0, 0, 0, 0], [1, 20, 20, 0, 0, 0, 0], [99, 100, 100, 0, 0, 0, 0]])
    dm.nodes = new_nodes
    dm.sync_next_id() # Simulate the fix in app.py
    
    # NOTE: In the fixed version, _next_point_id should be updated
    print(f"Post-update next_point_id (After Fix): {dm._next_point_id}")
    
    # 3. Add a new node
    new_id = dm.add_node(50, 50, 0)
    print(f"Added new node with ID: {new_id}")
    
    # 4. Check for collision
    # If the bug exists, new_id will be 2. If valid, it should be > 99.
    # But wait, we have IDs 0, 1, 99.
    # If _next_point_id was 2, new_id is 2.
    # Is 2In use? No. usage is 0, 1, 99.
    # So 2 is actually safe in this specific sparse case.
    # BUT, let's say we loaded [0, 1, 2].
    
    print("\n--- Testing Collision Scenario ---")
    nodes_collision = np.array([[0, 10, 10, 0, 0, 0, 0], [1, 20, 20, 0, 0, 0, 0]])
    dm2 = DataManager(nodes_collision, [], ["lane0.npy"])
    # next_id is 2.
    
    # Update brings in node 2
    dm2.nodes = np.array([[0, 10, 10, 0, 0, 0, 0], [1, 20, 20, 0, 0, 0, 0], [2, 30, 30, 0, 0, 0, 0]])
    dm2.sync_next_id() # Simulate the fix

    
    # Add node. expected next_id should be 3.
    # Buggy: next_id is 2.
    added_id = dm2.add_node(40, 40, 0)
    print(f"Added ID: {added_id}")
    
    if added_id == 2:
        print("FAIL: ID Collision! generated 2, but 2 already exists in nodes.")
    elif added_id > 2:
        print(f"PASS: ID {added_id} is safe.")
    else:
        print(f"Unknown state: {added_id}")

if __name__ == "__main__":
    test_id_synchronization()
