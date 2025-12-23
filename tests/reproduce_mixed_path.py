
import sys
import os
import numpy as np

# Adjust path to import from the project root
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from web.backend.utils.curve_utils import find_path

def test_mixed_direction_path():
    print("--- Test: Mixed Direction Pathfinding (Zig-Zag) ---")
    
    # 1. Setup a simple directed graph
    # Lane 1: 1 -> 2 -> 3
    # Lane 2: 4 -> 2 (Merges into 2? Or just connects? Let's say 4 conn to 2)
    # 
    # Graph:
    # 1 -> 2
    # 2 -> 3
    # 4 -> 2
    #
    # Expected: 
    # find_path(1, 3) -> [1, 2, 3] (Valid)
    # find_path(4, 3) -> [4, 2, 3] (Valid)
    # find_path(1, 4) -> None (Cannot go 1->2 vs 4->2)
    # 
    # Current "Undirected" Behavior (Hypothesis):
    # find_path(1, 4) -> [1, 2, 4] because it treats 4->2 as 2-4 linkage.
    
    edges = np.array([
        [1, 2],
        [2, 3],
        [4, 2]
    ])
    
    print(f"Edges:\n{edges}")
    
    # Test 1: Valid Path
    path_1_3 = find_path(edges, 1, 3)
    print(f"\nfind_path(1, 3): {path_1_3}")
    if path_1_3 == [1, 2, 3]:
        print("PASS: Found valid forward path.")
    else:
        print(f"FAIL: Expected [1, 2, 3], got {path_1_3}")

    # Test 2: Invalid "Zig-Zag" Path
    # Going 1->2 (Forward) then 2->4 (Backward against 4->2 arrow)
    path_1_4 = find_path(edges, 1, 4)
    print(f"\nfind_path(1, 4): {path_1_4}")
    
    if path_1_4 == [1, 2, 4]:
        print("CONFIRMED ISSUE: Found invalid zig-zag path (1->2->4). This is what we want to fix.")
    elif path_1_4 is None:
        print("ALREADY FIXED? Loop prevented path finding.")
    else:
        print(f"Unexpected result: {path_1_4}")

    # Test 3: Reverse Selection (User clicks End then Start)
    # find_path(3, 1) should auto-detect 1->3 is the correct valid lane
    path_3_1 = find_path(edges, 3, 1)
    print(f"\nfind_path(3, 1) [Reverse Click]: {path_3_1}")
    # Test 4: Forced "Undirected" Selection
    # find_path(1, 4, directed=False) should find [1, 2, 4]
    print(f"\nfind_path(1, 4, directed=False) [Force Mode]:")
    path_force = find_path(edges, 1, 4, directed=False)
    print(f"Result: {path_force}")
    
    if path_force == [1, 2, 4]:
        print("PASS: Force mode found the mixed-direction path.")
    else:
        print(f"FAIL: Expected [1, 2, 4], got {path_force}")
    
if __name__ == "__main__":
    test_mixed_direction_path()
