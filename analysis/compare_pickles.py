import argparse
import os
import pickle

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import networkx as nx


def load_graph(bucket_path):
    # Handle directory inputs
    if os.path.isdir(bucket_path):
        bucket_path = os.path.join(bucket_path, "output.pickle")

    if not os.path.exists(bucket_path):
        print(f"Error: File {bucket_path} not found.")
        return None
    try:
        with open(bucket_path, "rb") as f:
            try:
                G = pickle.load(f)
            except UnicodeDecodeError:
                # Fallback for Python 2/3 compatibility or protocol 2 specifics
                f.seek(0)
                G = pickle.load(f, encoding='latin1')
        return G
    except Exception as e:
        print(f"Error loading pickle {bucket_path}: {e}")
        return None


def extract_node_data(G):
    """
    Extracts node attributes into a Dictionary keyed by Node ID.
    Expected attributes: x, y, yaw, zone, etc.
    """
    data_map = {}
    for node_id, attrs in G.nodes(data=True):
        data_map[node_id] = attrs
    return data_map


def sanitize_graph(G):
    """
    Attempt to fix a broken NetworkX graph object loaded from an old pickle.
    """
    try:
        # If this works, it's fine
        _ = len(G.nodes)
        return G
    except Exception:
        print("Detected broken NetworkX graph structure. Attempting repair...")
    
    new_G = nx.DiGraph()
    
    # Try to recover nodes
    # Check for legacy 'node' dict (NX 1.x) or '_node' (NX 2.x)
    node_dict = getattr(G, 'node', getattr(G, '_node', {}))
    # It might be in __dict__ strictly if getattr fails due to properties
    if not node_dict and hasattr(G, '__dict__'):
        node_dict = G.__dict__.get('node', G.__dict__.get('_node', {}))
        
    # Check for adjacency
    adj_dict = getattr(G, 'adj', getattr(G, '_adj', {}))
    if not adj_dict and hasattr(G, '__dict__'):
        adj_dict = G.__dict__.get('adj', G.__dict__.get('_adj', {}))

    # Rebuild nodes
    if isinstance(node_dict, dict):
        for n, attrs in node_dict.items():
            new_G.add_node(n, **attrs)
    
    # Rebuild edges
    if isinstance(adj_dict, dict):
        for u, neighbors in adj_dict.items():
            for v, attrs in neighbors.items():
                new_G.add_edge(u, v, **attrs)
                
    print(f"Repaired Graph: {len(new_G.nodes)} nodes, {len(new_G.edges)} edges")
    return new_G

def compare_graphs(path1, path2, label1="Graph 1", label2="Graph 2"):
    G1 = load_graph(path1)
    G2 = load_graph(path2)

    if G1 is None or G2 is None:
        return

    # Sanitize just in case
    G1 = sanitize_graph(G1)
    G2 = sanitize_graph(G2)

    print(f"Loaded {label1}: {len(G1.nodes)} nodes, {len(G1.edges)} edges")
    print(f"Loaded {label2}: {len(G2.nodes)} nodes, {len(G2.edges)} edges")

    nodes1 = extract_node_data(G1)
    nodes2 = extract_node_data(G2)

    # Find common nodes
    common_ids = sorted(list(set(nodes1.keys()) & set(nodes2.keys())))
    missing_in_2 = sorted(list(set(nodes1.keys()) - set(nodes2.keys())))
    missing_in_1 = sorted(list(set(nodes2.keys()) - set(nodes1.keys())))

    print(f"Common Nodes: {len(common_ids)}")
    print(f"Nodes only in {label1}: {len(missing_in_2)}")
    print(f"Nodes only in {label2}: {len(missing_in_1)}")

    if not common_ids:
        print("No common nodes found to compare.")
        return

    # Prepare DataFrame for comparison
    records = []
    for nid in common_ids:
        n1 = nodes1[nid]
        n2 = nodes2[nid]

        # safely get attributes, default to 0.0 or nan if missing
        x1, y1 = n1.get('x', np.nan), n1.get('y', np.nan)
        x2, y2 = n2.get('x', np.nan), n2.get('y', np.nan)
        yaw1, yaw2 = n1.get('yaw', np.nan), n2.get('yaw', np.nan)

        dx = x1 - x2
        dy = y1 - y2
        dist_diff = np.sqrt(dx ** 2 + dy ** 2)
        yaw_diff = yaw1 - yaw2

        # Navigate yaw diff to [-pi, pi]
        yaw_diff = (yaw_diff + np.pi) % (2 * np.pi) - np.pi

        records.append({
            'node_id': nid,
            'x1': x1, 'y1': y1, 'yaw1': yaw1,
            'x2': x2, 'y2': y2, 'yaw2': yaw2,
            'x_diff': dx,
            'y_diff': dy,
            'dist_diff': dist_diff,
            'yaw_diff': yaw_diff
        })

    df = pd.DataFrame(records)

    # Visualization
    fig = plt.figure(figsize=(18, 10))

    # 1. Overlay Map (Full Graph)
    ax1 = plt.subplot(2, 3, 1)

    # Plot all G1 nodes (blue)
    x1_all = [d.get('x', 0) for d in nodes1.values()]
    y1_all = [d.get('y', 0) for d in nodes1.values()]
    ax1.scatter(x1_all, y1_all, c='blue', s=5, alpha=0.5, label=label1)

    # Plot all G2 nodes (red)
    x2_all = [d.get('x', 0) for d in nodes2.values()]
    y2_all = [d.get('y', 0) for d in nodes2.values()]
    ax1.scatter(x2_all, y2_all, c='red', s=5, alpha=0.5, label=label2)

    ax1.set_title("Global Trajectory Overlay")
    ax1.set_xlabel("X")
    ax1.set_ylabel("Y")
    ax1.axis('equal')
    ax1.legend()
    ax1.grid(True)

    # 2. X Difference vs ID
    ax2 = plt.subplot(2, 3, 2)
    ax2.plot(df['node_id'], df['x_diff'], '.', color='purple', alpha=0.6)
    ax2.set_title("X Difference (G1 - G2)")
    ax2.set_xlabel("Node ID")
    ax2.set_ylabel("Delta X (m)")
    ax2.grid(True)

    # 3. Y Difference vs ID
    ax3 = plt.subplot(2, 3, 3)
    ax3.plot(df['node_id'], df['y_diff'], '.', color='green', alpha=0.6)
    ax3.set_title("Y Difference (G1 - G2)")
    ax3.set_xlabel("Node ID")
    ax3.set_ylabel("Delta Y (m)")
    ax3.grid(True)

    # 4. Total Distance Difference vs ID
    ax4 = plt.subplot(2, 3, 4)
    ax4.plot(df['node_id'], df['dist_diff'], '.', color='orange', alpha=0.6)
    ax4.set_title("Total Positional Error")
    ax4.set_xlabel("Node ID")
    ax4.set_ylabel("Distance (m)")
    ax4.grid(True)

    # 5. Yaw Difference vs ID
    ax5 = plt.subplot(2, 3, 5)
    ax5.plot(df['node_id'], np.degrees(df['yaw_diff']), '.', color='magenta', alpha=0.6)
    ax5.set_title("Yaw Difference")
    ax5.set_xlabel("Node ID")
    ax5.set_ylabel("Delta Yaw (degrees)")
    ax5.grid(True)

    # 6. Yaw Values Comparison
    ax6 = plt.subplot(2, 3, 6)
    ax6.plot(df['node_id'], np.degrees(df['yaw1']), label=label1, color='blue', alpha=0.5)
    ax6.plot(df['node_id'], np.degrees(df['yaw2']), label=label2, color='red', alpha=0.5, linestyle='--')
    ax6.set_title("Yaw Values vs ID")
    ax6.set_xlabel("Node ID")
    ax6.set_ylabel("Yaw (degrees)")
    ax6.legend()
    ax6.grid(True)

    plt.tight_layout()
    output_img = "pickle_comparison.png"
    # plt.savefig(output_img)
    print(f"Comparison plot saved to {output_img}")
    plt.show()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Compare two Graph Pickle files.")
    parser.add_argument("file1", help="Path to the first pickle file")
    parser.add_argument("file2", help="Path to the second pickle file")
    parser.add_argument("--label1", default="File 1", help="Label for first file")
    parser.add_argument("--label2", default="File 2", help="Label for second file")

    args = parser.parse_args()

    compare_graphs(args.file1, args.file2, args.label1, args.label2)
