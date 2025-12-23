
import sys
import os
import numpy as np
import pytest
from unittest.mock import MagicMock

# Adjust path to import from the project root
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

# Mock DataManager and curve_utils for isolation if needed, 
# but for integration test on logic we can import actual utils.

from web.backend.utils.curve_utils import find_path

# We will test the logic flow akin to app.py
# Mocking the data manager's edges
edges = np.array([
    [1, 2],
    [2, 3],
    [4, 2]
])

def test_strict_vs_force_logic():
    print("--- Test: Backend Operations Force Logic ---")
    
    start_id = 1
    end_id = 4
    
    # 1. Reverse Path Logic Simulation
    print("\n[Operation: Reverse Path 1->4]")
    
    # Strict (Default)
    path_strict = find_path(edges, start_id, end_id, directed=True)
    if path_strict is None:
        print("PASS: Strict mode correctly blocked invalid path.")
    else:
        print(f"FAIL: Strict mode found path {path_strict}")
        
    # Force (Undirected)
    path_force = find_path(edges, start_id, end_id, directed=False)
    if path_force == [1, 2, 4]:
        print("PASS: Force mode found zig-zag path.")
    else:
        print(f"FAIL: Force mode returned {path_force}")
        
    # 2. Remove Between Logic Simulation
    print("\n[Operation: Remove Between 1->4]")
    # Strict
    path_strict = find_path(edges, start_id, end_id, directed=True)
    if path_strict is None:
         print("PASS: Strict mode correctly blocked invalid path.")
    
    # Force
    path_force = find_path(edges, start_id, end_id, directed=False)
    if path_force == [1, 2, 4]:
        # Logic in app.py: if len > 2, delete path[1:-1] => delete [2]
        to_delete = path_force[1:-1]
        if to_delete == [2]:
             print("PASS: Force mode identified correct node to delete (2).")
        else:
             print(f"FAIL: Force mode identified {to_delete} to delete.")

if __name__ == "__main__":
    test_strict_vs_force_logic()
