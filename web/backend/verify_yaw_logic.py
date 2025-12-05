import os
import sys
import numpy as np
import math

# Adjust path to import from the parent project if needed
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

def calculate_yaw_diff(yaw1, yaw2):
    """
    Calculates the difference between two angles in radians, normalized to [-pi, pi].
    Formula provided by user: abs((((yaw1 - yaw2) + 3.14159) % 6.28319) - 3.14159)
    """
    diff = abs((((yaw1 - yaw2) + math.pi) % (2 * math.pi)) - math.pi)
    return diff

def test_yaw_logic():
    print("--- Testing Yaw Logic ---")
    
    # Test Case 1: Aligned
    y1 = 1.0
    y2 = 1.0
    diff = calculate_yaw_diff(y1, y2)
    print(f"Aligned (1.0, 1.0): Diff={diff:.4f} (Expected ~0.0)")
    assert diff < 1e-5

    # Test Case 2: Opposite
    y1 = 0.0
    y2 = math.pi
    diff = calculate_yaw_diff(y1, y2)
    print(f"Opposite (0.0, pi): Diff={diff:.4f} (Expected ~3.1416)")
    assert abs(diff - math.pi) < 1e-4

    # Test Case 3: Perpendicular
    y1 = 0.0
    y2 = math.pi / 2
    diff = calculate_yaw_diff(y1, y2)
    print(f"Perpendicular (0.0, pi/2): Diff={diff:.4f} (Expected ~1.5708)")
    assert abs(diff - math.pi/2) < 1e-4
    
    # Test Case 4: Wrapping
    y1 = 0.1
    y2 = 2 * math.pi - 0.1 # -0.1 effectively
    diff = calculate_yaw_diff(y1, y2)
    print(f"Wrapping (0.1, 2pi-0.1): Diff={diff:.4f} (Expected ~0.2)")
    assert abs(diff - 0.2) < 1e-4

    print("Logic tests passed!\n")

def verify_graph_data():
    print("--- Verifying Graph Data ---")
    base_dir = os.path.dirname(os.path.abspath(__file__))
    workspace_dir = os.path.join(base_dir, "workspace")
    nodes_path = os.path.join(workspace_dir, "graph_nodes.npy")
    edges_path = os.path.join(workspace_dir, "graph_edges.npy")

    if not os.path.exists(nodes_path) or not os.path.exists(edges_path):
        print("Graph data files not found in workspace.")
        return

    try:
        nodes = np.load(nodes_path)
        edges = np.load(edges_path)
        
        print(f"Loaded {len(nodes)} nodes and {len(edges)} edges.")
        
        if len(nodes) == 0 or len(edges) == 0:
            print("Graph is empty.")
            return

        # Create a map for quick node lookup
        # Node structure: [point_id, x, y, yaw, zone, width, indicator]
        node_map = {int(row[0]): row for row in nodes}

        aligned_count = 0
        misaligned_count = 0
        threshold = 0.4 # User mentioned 0.4

        for edge in edges:
            u_id, v_id = int(edge[0]), int(edge[1])
            
            if u_id not in node_map or v_id not in node_map:
                continue
                
            u_node = node_map[u_id]
            v_node = node_map[v_id]
            
            # Calculate geometric yaw of the edge
            dx = v_node[1] - u_node[1]
            dy = v_node[2] - u_node[2]
            edge_yaw = math.atan2(dy, dx)
            
            # Compare with stored yaw of the source node (u)
            stored_yaw = u_node[3]
            
            diff = calculate_yaw_diff(stored_yaw, edge_yaw)
            
            if diff < threshold:
                aligned_count += 1
            else:
                misaligned_count += 1
                # print(f"Misaligned Edge {u_id}->{v_id}: Stored={stored_yaw:.2f}, Edge={edge_yaw:.2f}, Diff={diff:.2f}")

        total_edges = aligned_count + misaligned_count
        if total_edges > 0:
            print(f"Total Edges Checked: {total_edges}")
            print(f"Aligned Edges (< {threshold} rad): {aligned_count} ({aligned_count/total_edges*100:.1f}%)")
            print(f"Misaligned Edges: {misaligned_count} ({misaligned_count/total_edges*100:.1f}%)")
        else:
            print("No valid edges to check.")

    except Exception as e:
        print(f"Error verifying data: {e}")

if __name__ == "__main__":
    test_yaw_logic()
    verify_graph_data()
