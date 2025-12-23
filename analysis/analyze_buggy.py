import os
import pickle
import numpy as np
import matplotlib.pyplot as plt
import networkx as nx

def load_npy(path):
    print(f"Loading NPY: {path}")
    try:
        data = np.load(path)
        if data.size > 0 and data.ndim == 2:
            return data
    except Exception as e:
        print(f"Error loading NPY {path}: {e}")
    return None

def load_pickle_graph(path):
    print(f"Loading Pickle Graph: {path}")
    try:
        with open(path, 'rb') as f:
            G = pickle.load(f)
    except UnicodeDecodeError:
        with open(path, 'rb') as f:
            G = pickle.load(f, encoding='latin1')
    except Exception as e:
        print(f"Error loading pickle {path}: {e}")
        return None

    nodes_data = []
    try:
        # Debugging revealed nodes are in G.__dict__['node']
        if hasattr(G, '__dict__') and 'node' in G.__dict__:
            node_dict = G.__dict__['node']
            for n, d in node_dict.items():
                x = d.get('x', 0)
                y = d.get('y', 0)
                yaw = d.get('yaw', 0)
                nodes_data.append([x, y, yaw])
        # Fallbacks
        elif hasattr(G, 'nodes'):
             # Try standard iteration (might fail with some custom/broken graph objects)
            try:
                for n, d in G.nodes.items():
                    x = d.get('x', 0)
                    y = d.get('y', 0)
                    yaw = d.get('yaw', 0)
                    nodes_data.append([x, y, yaw])
            except:
                pass
    except Exception as e:
        print(f"Error parsing graph nodes: {e}")
        return None
    
    if not nodes_data:
        print("No nodes extracted from graph.")
        return None

    # Sort by X? Or just return as is. Let's return as is, but maybe we want to order them?
    # If they are a path, order matters. If it's a graph, order doesn't explicitly matter for plotting list of points.
    return np.array(nodes_data)

def load_vlp16_log(path):
    print(f"Loading VLP16 Log: {path}")
    data = []
    try:
        with open(path, 'r') as f:
            lines = f.readlines()
            for line in lines:
                parts = line.strip().split()
                if len(parts) < 3: continue
                try:
                    # Assuming standard FAST_LIO format where columns 1, 2, 3 might be x, y, z
                    # Need to verify columns. Usually: timestamp, x, y, z, qx, qy, qz, qw...
                    # Let's try to extract floats
                    nums = [float(p) for p in parts]
                    data.append(nums)
                except ValueError:
                    continue
    except Exception as e:
        print(f"Error reading log {path}: {e}")
        return None
    
    return np.array(data)

def calculate_steering(trajectory, L=2.7):
    if len(trajectory) < 2: return np.array([]), np.array([]), np.array([])
    
    x = trajectory[:, 0]
    y = trajectory[:, 1]
    
    # Use 3rd column as yaw if available, else zero (or calculate from xy dim)
    if trajectory.shape[1] >= 3:
        yaw = trajectory[:, 2]
    else:
        # Estimate yaw from path
        yaw = np.arctan2(np.diff(y), np.diff(x))
        yaw = np.append(yaw, yaw[-1])

    dx = np.diff(x)
    dy = np.diff(y)
    dists = np.sqrt(dx**2 + dy**2)
    s = np.concatenate(([0], np.cumsum(dists)))
    
    dyaw = np.diff(yaw)
    dyaw = (dyaw + np.pi) % (2 * np.pi) - np.pi # Normalize
    
    dists_safe = dists.copy()
    dists_safe[dists_safe < 1e-6] = 1e-6
    
    kappa = dyaw / dists_safe
    steering = np.arctan(L * kappa)
    steering = np.append(steering, 0)
    
    return s, steering, dists

def main():
    base_dir = r"f:/RunningProjects/LaneMappingTool"
    gitam_path = os.path.join(base_dir, "lanes", "Gitam_lanes", "Gitam.npy")
    buggy_pickle_path = r"G:/RunningProjects/Buggy/vechicalFileByInfCmp/sb_main_gate.pickel"
    vlp16_log_path = r"G:/RunningProjects/Buggy/vechicalFileByInfCmp/SLAM/src/FAST_LIO/Log/mat_pre.txt"
    
    output_dir = os.path.join(base_dir, "analysis", "results")
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)

    datasets = {}

    # 1. Load Gitam Lanes
    gitam_data = load_npy(gitam_path)
    if gitam_data is not None:
        datasets['Original (Gitam)'] = gitam_data[:, :3] # x,y,yaw

    # 2. Load Buggy Pickle
    buggy_data = load_pickle_graph(buggy_pickle_path)
    if buggy_data is not None:
        datasets['Buggy Graph'] = buggy_data

    # 3. Load VLP16
    vlp16_raw = load_vlp16_log(vlp16_log_path)
    if vlp16_raw is not None and vlp16_raw.shape[0] > 0:
        # Debug plot to identify columns
        plt.figure(figsize=(10, 6))
        for i in range(min(vlp16_raw.shape[1], 10)):
            plt.plot(vlp16_raw[:, i], label=f"Col {i}")
        plt.legend()
        plt.title("VLP16 Raw Columns (First 10)")
        plt.savefig(os.path.join(output_dir, "vlp16_columns.png"))
        plt.close()
        
        # Heuristic: Find X, Y columns by variance or magnitude typical of coordinates
        # Checking file content:
        # 0.302614 0 0 0 ...
        # Column 0 looks like timestamp (small increment)? Or maybe the first non-zero are X Y?
        # Let's assume indices 11, 12, 13 (typical for matricies) or look for variation
        # Actually, let's just plot indices 1 vs 2, 2 vs 3 etc to find the path
        
        # Based on typical log formats (e.g. Tum / KITTI), usually: timestamp tx ty tz qx qy qz qw
        # 0.302614 0 0 0 -0.00017... 
        # let's try col 1 and 2, or 11 and 12
        # WE will plot a few candidates in the main plot
        
        # Candidate 1: Cols 1, 2
        datasets['VLP16 (Cols 1-2)'] = vlp16_raw[:, 1:4] # x,y,z? 
        
        # Candidate 2: Cols 11, 12 (Log/mat_pre.txt seems to be a matrix dump?)
        if vlp16_raw.shape[1] > 12:
             datasets['VLP16 (Cols 11-12)'] = vlp16_raw[:, 11:14]

    # Plot Comparison
    plt.figure(figsize=(15, 10))
    
    # 1. Trajectory
    plt.subplot(2, 1, 1)
    for name, data in datasets.items():
        if data is None or len(data) == 0: continue
        plt.plot(data[:, 0], data[:, 1], label=name, marker='.', markersize=2, alpha=0.5)
        # Mark start
        plt.plot(data[0, 0], data[0, 1], 'o', label=f"{name} Start")
        
    plt.title("Trajectory Comparison")
    plt.xlabel("X")
    plt.ylabel("Y")
    plt.legend()
    plt.axis('equal')
    plt.grid(True)

    # 2. Steering
    plt.subplot(2, 1, 2)
    for name, data in datasets.items():
        if "VLP16" in name: continue # Skip VLP16 for steering initially as it might be noisy
        if data is None or len(data) == 0: continue
        
        s, steering, _ = calculate_steering(data)
        plt.plot(s, np.degrees(steering), label=name, alpha=0.7)
        
    plt.title("Steering Profile")
    plt.xlabel("Distance (m)")
    plt.ylabel("Steering Angle (deg)")
    plt.legend()
    plt.grid(True)
    
    plt.tight_layout()
    plt.savefig(os.path.join(output_dir, "trajectory_comparison.png"))
    print("Saved comparison plot.")

if __name__ == "__main__":
    main()
