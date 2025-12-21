import math
import os
import sys

import matplotlib.pyplot as plt
import numpy as np

# Adjust path to import from the parent project if needed
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))


def calculate_yaw_diff(yaw1, yaw2):
    """
    Calculates the difference between two angles in radians, normalized to [-pi, pi].
    Formula provided by user: abs((((yaw1 - yaw2) + 3.14159) % 6.28319) - 3.14159)
    """
    diff = abs((((yaw1 - yaw2) + math.pi) % (2 * math.pi)) - math.pi)
    return diff


def test_yaw_logic():
    """Tests the yaw difference calculation for various cases."""
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
    assert abs(diff - math.pi / 2) < 1e-4

    # Test Case 4: Wrapping
    y1 = 0.1
    y2 = 2 * math.pi - 0.1  # -0.1 effectively
    diff = calculate_yaw_diff(y1, y2)
    print(f"Wrapping (0.1, 2pi-0.1): Diff={diff:.4f} (Expected ~0.2)")
    assert abs(diff - 0.2) < 1e-4

    print("Logic tests passed!\n")


def visualize_results(nodes, edges, node_map, threshold, workspace_dir):
    """Generate a visualization of nodes and edges based on yaw alignment.
    
    This function creates a scatter plot of nodes and overlays edges  based on
    their yaw alignment. It distinguishes between aligned and  misaligned edges
    using a specified threshold. The nodes are plotted  as small gray dots, while
    aligned edges are shown in green and  misaligned edges in red. The resulting
    visualization is saved as  "yaw_verification.png" in the specified workspace
    directory.
    
    Args:
        nodes: A numpy array containing node information, where each
            row represents a node with its coordinates and yaw.
        edges: A list of edges, where each edge is represented by a
            pair of node indices.
        node_map: A dictionary mapping node IDs to their corresponding
            information in the nodes array.
        threshold: A float representing the yaw difference threshold
            for alignment.
        workspace_dir: A string representing the directory where the
            visualization will be saved.
    """
    print("--- Generating Visualization ---")
    plt.figure(figsize=(12, 10))

    # Plot all nodes as small gray dots
    # nodes[:, 1] is x, nodes[:, 2] is y
    plt.scatter(nodes[:, 1], nodes[:, 2], c='lightgray', s=10, alpha=0.5, label='Nodes')

    aligned_x = []
    aligned_y = []
    misaligned_x = []
    misaligned_y = []

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
            aligned_x.extend([u_node[1], v_node[1], None])
            aligned_y.extend([u_node[2], v_node[2], None])
        else:
            misaligned_x.extend([u_node[1], v_node[1], None])
            misaligned_y.extend([u_node[2], v_node[2], None])

    # Plot aligned edges (Green)
    if aligned_x:
        plt.plot(aligned_x, aligned_y, c='green', linewidth=1, alpha=0.6, label=f'Aligned (<{threshold} rad)')

    # Plot misaligned edges (Red)
    if misaligned_x:
        plt.plot(misaligned_x, misaligned_y, c='red', linewidth=1.5, alpha=0.8, label=f'Misaligned (>={threshold} rad)')

    plt.title(f"Yaw Verification (Threshold: {threshold} rad)")
    plt.xlabel("X")
    plt.ylabel("Y")
    plt.legend()
    plt.axis('equal')
    plt.grid(True, alpha=0.3)

    output_path = os.path.join(workspace_dir, "yaw_verification.png")
    plt.savefig(output_path, dpi=150)
    print(f"Visualization saved to: {output_path}")
    # plt.show() # Don't show in non-interactive env


def verify_graph_data():
    """Verify the integrity and alignment of graph data.
    
    This function checks for the existence of graph data files, loads the nodes and
    edges, and verifies their alignment based on a specified yaw threshold. It
    creates a mapping for quick node lookup and counts the number of aligned and
    misaligned edges. Finally, it visualizes the results and handles any exceptions
    that may occur during the process.
    """
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
        threshold = 0.4  # User mentioned 0.4

        # Pre-pass to count
        for edge in edges:
            u_id, v_id = int(edge[0]), int(edge[1])
            if u_id not in node_map or v_id not in node_map: continue

            u_node = node_map[u_id]
            v_node = node_map[v_id]
            dx = v_node[1] - u_node[1]
            dy = v_node[2] - u_node[2]
            edge_yaw = math.atan2(dy, dx)
            stored_yaw = u_node[3]
            diff = calculate_yaw_diff(stored_yaw, edge_yaw)

            if diff < threshold:
                aligned_count += 1
            else:
                misaligned_count += 1

        total_edges = aligned_count + misaligned_count
        if total_edges > 0:
            print(f"Total Edges Checked: {total_edges}")
            print(f"Aligned Edges (< {threshold} rad): {aligned_count} ({aligned_count / total_edges * 100:.1f}%)")
            print(f"Misaligned Edges: {misaligned_count} ({misaligned_count / total_edges * 100:.1f}%)")
        else:
            print("No valid edges to check.")

        # Visualize
        visualize_results(nodes, edges, node_map, threshold, workspace_dir)

    except Exception as e:
        print(f"Error verifying data: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    test_yaw_logic()
    verify_graph_data()
