import os
import pickle

import matplotlib.pyplot as plt
import networkx as nx
import numpy as np


def load_npy(path):
    print(f"Loading NPY: {path}")
    data = np.load(path)
    # Expected: [x, y, yaw, ...]
    if data.ndim == 2 and data.shape[1] >= 3:
        return data  # return full array
    return None


def load_pickle_graph(path):
    print(f"Loading Pickle Graph: {path}")
    try:
        with open(path, 'rb') as f:
            G = pickle.load(f)
    except UnicodeDecodeError:
        with open(path, 'rb') as f:
            G = pickle.load(f, encoding='latin1')

    if not isinstance(G, nx.DiGraph):
        print("Error: Pickle does not contain a DiGraph")
        return None

    # Extract ordered nodes
    nodes_data = []
    try:
        # Try standard way
        ids = sorted(list(G.nodes))
    except (TypeError, Exception) as e:
        print(f"Standard node iteration failed: {e}")
        print("Attempting to access internal _node storage...")
        try:
            # Fallback for version mismatch or broken pickles
            if hasattr(G, '_node'):
                ids = sorted(list(G._node.keys()))
            elif hasattr(G, 'node'):  # Older networkx
                ids = sorted(list(G.node.keys()))
            else:
                print("Could not find node storage.")
                return None
        except Exception as e2:
            print(f"Internal node access failed: {e2}")
            return None

    for i in ids:
        try:
            # Access node data
            if hasattr(G, 'nodes'):
                d = G.nodes[i]
            elif hasattr(G, '_node'):
                d = G._node[i]
            else:
                d = {}

            # Ensure we have x, y, yaw at minimum
            row = [d.get('x', 0), d.get('y', 0), d.get('yaw', 0)]
            nodes_data.append(row)
        except Exception as e3:
            print(f"Error accessing node {i}: {e3}")

    return np.array(nodes_data)


def calculate_steering(trajectory, L=2.7):
    """
    Calculate steering angle based on trajectory.
    trajectory: np.array of shape (N, 3+) where columns are x, y, yaw (radians)
    L: Wheelbase in meters
    """
    x = trajectory[:, 0]
    y = trajectory[:, 1]
    yaw = trajectory[:, 2]  # Assumed in radians

    # Distance between points
    dx = np.diff(x)
    dy = np.diff(y)
    dists = np.sqrt(dx ** 2 + dy ** 2)

    # Cumulative distance
    s = np.concatenate(([0], np.cumsum(dists)))

    # Derivative of yaw w.r.t distance (curvature kappa)
    # Simple finite difference: d(yaw) / d(s)
    dyaw = np.diff(yaw)

    # Handle wrapping if needed (assuming yaw is continuous or small changes)
    # Normalize angles to -pi, pi
    dyaw = (dyaw + np.pi) % (2 * np.pi) - np.pi

    # Avoid division by zero
    dists_safe = dists.copy()
    dists_safe[dists_safe < 1e-6] = 1e-6

    kappa = dyaw / dists_safe

    # Steering angle delta = arctan(L * kappa)
    steering = np.arctan(L * kappa)

    # Pad to match length N (append last value or prepend first)
    # Appending 0 for the last point
    steering = np.append(steering, 0)

    return s, steering, dists


def plot_comparison(datasets, output_dir):
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)

    plt.figure(figsize=(12, 10))

    # Plot 1: Trajectory
    plt.subplot(3, 1, 1)
    for label, data in datasets.items():
        if data is None or len(data) == 0: continue
        plt.plot(data[:, 0], data[:, 1], label=label, marker='.', markersize=2, alpha=0.7)
    plt.title("Vehicle Trajectory (XY)")
    plt.xlabel("X (m)")
    plt.ylabel("Y (m)")
    plt.legend()
    plt.axis('equal')
    plt.grid(True)

    # Plot 2: Steering Angle
    plt.subplot(3, 1, 2)
    s_max = 0
    for label, data in datasets.items():
        if data is None or len(data) == 0: continue
        s, steering, _ = calculate_steering(data)
        plt.plot(s, np.degrees(steering), label=label, alpha=0.7)
        s_max = max(s_max, s.max())

    plt.title("Calculated Steering Angle (deg)")
    plt.xlabel("Distance Travelled (m)")
    plt.ylabel("Steering Angle (deg)")
    plt.legend()
    plt.grid(True)

    # Plot 3: Yaw
    plt.subplot(3, 1, 3)
    for label, data in datasets.items():
        if data is None or len(data) == 0: continue
        # Recalculate s just for x-axis consistency
        dx = np.diff(data[:, 0])
        dy = np.diff(data[:, 1])
        dists = np.sqrt(dx ** 2 + dy ** 2)
        s = np.concatenate(([0], np.cumsum(dists)))

        plt.plot(s, np.degrees(data[:, 2]), label=label, alpha=0.7)

    plt.title("Yaw (deg)")
    plt.xlabel("Distance Travelled (m)")
    plt.ylabel("Yaw (deg)")
    plt.legend()
    plt.grid(True)

    plt.tight_layout()
    save_path = os.path.join(output_dir, "steering_analysis.png")
    plt.savefig(save_path)
    print(f"Comparison plot saved to: {save_path}")
    # plt.show() # Disabled for headless


if __name__ == "__main__":
    # Define paths
    BASE_DIR = r"f:/RunningProjects/LaneMappingTool"
    GITAM_NPY = os.path.join(BASE_DIR, "lanes", "Gitam_lanes", "Gitam.npy")
    TOOL_PICKLE = os.path.join(BASE_DIR, "web", "backend", "workspace", "output.pickle")
    BUGGY_PICKLE = r"G:/RunningProjects/Buggy/vechicalFileByInfCmp/sb_main_gate1.pickel"

    datasets = {}

    # Load Gitam.npy
    if os.path.exists(GITAM_NPY):
        npy_data = load_npy(GITAM_NPY)
        if npy_data is not None:
            # Gitam.npy columns: x, y, yaw, ...
            datasets["Original (Gitam.npy)"] = npy_data[:, :3]  # Keep first 3 cols

    # Load Tool Output
    if os.path.exists(TOOL_PICKLE):
        tool_data = load_pickle_graph(TOOL_PICKLE)
        if tool_data is not None:
            datasets["Tool Output (output.pickle)"] = tool_data

    # Load Buggy Reference (if simple file rename didn't work, might need to inspect actual content structure)
    # For now trying as graph
    if os.path.exists(BUGGY_PICKLE):
        buggy_data = load_pickle_graph(BUGGY_PICKLE)
        if buggy_data is not None:
            datasets["Reference (sb_main_gate.pickel)"] = buggy_data
        else:
            print("Reference pickle failed to load as Graph. Might be raw data?")

    if not datasets:
        print("No datasets loaded!")
    else:
        plot_comparison(datasets, os.path.join(BASE_DIR, "analysis", "results"))
