import sys
import os
import numpy as np

# Adjust path to import from the parent project
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../web/backend')))

from curve_utils import find_path, smooth_segment

def test_smooth_robustness():
    print("Testing Smooth Operation Robustness...")

    # Mock Data
    nodes = np.array([
        [1, 0, 0, 0],
        [2, 10, 10, 0],
        [3, 20, 20, 0],
        [4, 30, 30, 0],
        [5, 40, 40, 0]
    ])
    edges = np.array([
        [1, 2],
        [2, 3],
        [3, 4],
        [4, 5]
    ])

    # 1. Test Valid Path
    print("\n--- Test 1: Valid Path ---")
    path = find_path(edges, 1, 5)
    print(f"Path found: {path}")
    assert path == [1, 2, 3, 4, 5]
    
    smoothed = smooth_segment(nodes, edges, path, smoothness=1.0, weight=10)
    if smoothed is not None:
        print("Smoothing successful (Expected)")
    else:
        print("Smoothing failed (Unexpected)")

    # 2. Test No Path
    print("\n--- Test 2: No Path ---")
    path = find_path(edges, 1, 99) # 99 doesn't exist
    print(f"Path found: {path}")
    assert path is None

    # 3. Test Short Path (< 3 points)
    print("\n--- Test 3: Short Path ---")
    short_path = [1, 2]
    smoothed = smooth_segment(nodes, edges, short_path, smoothness=1.0, weight=10)
    if smoothed is None:
        print("Smoothing rejected short path (Expected)")
    else:
        print("Smoothing accepted short path (Unexpected)")

    # 4. Test Duplicate Points
    print("\n--- Test 4: Duplicate Points ---")
    # Create nodes with duplicates
    nodes_dup = np.array([
        [1, 0, 0, 0],
        [2, 10, 10, 0],
        [3, 10, 10, 0], # Duplicate of 2
        [4, 10, 10, 0]  # Another duplicate of 2
    ])
    path_dup = [1, 2, 3, 4]
    smoothed = smooth_segment(nodes_dup, edges, path_dup, smoothness=1.0, weight=10)
    if smoothed is None:
        print("Smoothing rejected duplicate points (Expected)")
    else:
        print("Smoothing accepted duplicate points (Unexpected)")

if __name__ == "__main__":
    test_smooth_robustness()
