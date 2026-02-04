
import sys
import os
import pickle
import numpy as np
import matplotlib.pyplot as plt
from scipy.interpolate import splprep, splev

# Add project root to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from utils.curve_manager import CurveManager
from utils.data_manager import DataManager

# Mock classes
class MockPlotManager:
    class MockSlider:
        val = 0.5 # Default smoothing factor
    
    def __init__(self):
        self.slider_smooth = self.MockSlider()
        self.ax = None
        self.fig = None
        self.selected_indices = []
    
    def update_plot(self, *args, **kwargs):
        pass

class MockEventHandler:
    def __init__(self):
        self.smoothing_path_ids = []
        self.smoothing_preview_line = None
        self.status = ""

    def update_status(self, msg):
        pass

def load_graph_nodes(pickle_path):
    print(f"Loading graph from {pickle_path}...")
    try:
        with open(pickle_path, 'rb') as f:
            G = pickle.load(f, encoding='latin1')
    except Exception as e:
        print(f"Pickle load failed: {e}")
        return None, None

    print(f"Loaded object type: {type(G)}")
    
    # helper to extract attributes
    def get_attrs(data):
        return [
            data.get('x', 0), 
            data.get('y', 0), 
            data.get('yaw', 0), 
            data.get('zone', 0), 
            data.get('width', 0), 
            data.get('indicator', 0)
        ]

    dm_nodes = []
    dm_edges = []
    
    # Strategy 1: Standard NetworkX API
    try:
        print("Attempting standard NetworkX iteration...")
        node_ids = sorted(list(G.nodes())) # This triggers the error usually
        for n in node_ids:
            data = G.nodes[n]
            dm_nodes.append([n] + get_attrs(data))
            
        for u, v in G.edges():
            dm_edges.append([u, v])
            
        print("Standard iteration successful.")
            
    except Exception as e:
        print(f"Standard iteration failed: {e}")
        print("Attempting direct dict access...")
        
        # Strategy 2: Direct Dict Access (Bypass broken iterator)
        # Check for _node (NX 2.x+) or node (NX 1.x)
        if hasattr(G, '_node'):
            nodes_dict = G._node
            print(f"Found G._node. Type: {type(nodes_dict)}")
            # Try to grab dict if it's wrapped
            if not isinstance(nodes_dict, dict):
                 print(f"G._node is not a dict. Inspecting: {nodes_dict}")
                 if hasattr(nodes_dict, '__dict__'):
                     print(f"G._node.__dict__: {nodes_dict.__dict__.keys()}")
                 # maybe it is the property itself?
        
        elif hasattr(G, 'node'):
            nodes_dict = G.node
            print(f"Found G.node. Type: {type(nodes_dict)}")

        # Fallback: Check G.__dict__ directly
        if nodes_dict is None or not isinstance(nodes_dict, dict):
             print("Checking G.__dict__ for hidden dicts...")
             for k, v in G.__dict__.items():
                 if isinstance(v, dict) and len(v) > 0:
                     # Heuristic: keys are integers (point IDs), values have 'x','y'
                     first_k = next(iter(v))
                     first_v = v[first_k]
                     if isinstance(first_v, dict) and 'x' in first_v and 'y' in first_v:
                         print(f"Found candidate node dict in G.__dict__['{k}']")
                         nodes_dict = v
                         break
            
        if nodes_dict is not None and isinstance(nodes_dict, dict):
            sorted_ids = sorted(nodes_dict.keys())
            for n in sorted_ids:
                data = nodes_dict[n]
                dm_nodes.append([n] + get_attrs(data))
        else:
            print("Could not find nodes dict.")
            return None, None
            
        # Edges
        # Check for adjacency dict in G.__dict__
        adj_dict = None
        
        # Try finding it in __dict__ by key 'adj' or 'edge'
        candidates = ['adj', '_adj', 'edge', '_edge']
        for k in candidates:
             if k in G.__dict__ and isinstance(G.__dict__[k], dict):
                 print(f"Found candidate adj dict at G.__dict__['{k}']")
                 adj_dict = G.__dict__[k]
                 break
        
        if adj_dict is None:
             print("Scanning G.__dict__ for adj-like structure...")
             for k, v in G.__dict__.items():
                 if isinstance(v, dict) and len(v) > 0:
                     if k == 'node': continue # Skip the one we already found
                     # Heuristic: keys are integers, values are dicts (neighbors)
                     first_k = next(iter(v))
                     first_v = v[first_k]
                     # Check if first_v is a dict (neighbors)
                     if isinstance(first_v, dict):
                         # Distinguish from node dict: node dict values have 'x','y'. Adj dict values have edge attrs (or empty)
                         if 'x' in first_v and 'y' in first_v:
                             continue # likely another node dict?
                         
                         print(f"Found potential adj dict in G.__dict__['{k}']")
                         adj_dict = v
                         break

        if adj_dict is not None and isinstance(adj_dict, dict):
            for u in sorted(adj_dict.keys()):
                if u not in adj_dict: continue
                neighbors = adj_dict[u]
                if not isinstance(neighbors, dict): continue
                for v in sorted(neighbors.keys()):
                    dm_edges.append([u, v])
        else:
            print("Could not find adj dict.")
            
    print(f"Extracted {len(dm_nodes)} nodes and {len(dm_edges)} edges.")
    return np.array(dm_nodes), np.array(dm_edges)

def get_longest_path(nodes, edges):
    import networkx as nx
    G = nx.Graph()
    G.add_nodes_from(nodes[:, 0])
    G.add_edges_from(edges)
    
    if len(G.nodes) == 0:
        return []

    # Find connected components
    comps = list(nx.connected_components(G))
    if not comps:
        return []
    largest_comp = max(comps, key=len)
    
    # Find longest path in largest component
    # Heuristic: Find endpoints (degree 1)
    subG = G.subgraph(largest_comp)
    endpoints = [n for n, d in subG.degree() if d == 1]
    
    if len(endpoints) < 2:
        # Loop? Pick any node
        start = list(largest_comp)[0]
    else:
        start = endpoints[0]
        
    # BFS/DFS to find furthest node
    lengths = nx.single_source_shortest_path_length(subG, start)
    end = max(lengths, key=lengths.get)
    
    path = nx.shortest_path(subG, start, end)
    return path

def analyze_smoothness(nodes_array, label):
    # Calculate geometric properties
    coords = nodes_array[:, 1:3]
    
    # 1. Spacing
    dists = np.sqrt(np.sum(np.diff(coords, axis=0)**2, axis=1))
    avg_spacing = np.mean(dists)
    std_spacing = np.std(dists)
    
    # 2. Curvature (Kappa)
    # k = (x'y'' - y'x'') / (x'^2 + y'^2)^(3/2)
    # We need derivatives.
    dx = np.gradient(coords[:, 0])
    dy = np.gradient(coords[:, 1])
    ddx = np.gradient(dx)
    ddy = np.gradient(dy)
    
    numerator = dx * ddy - dy * ddx
    denominator = (dx**2 + dy**2)**1.5
    # Avoid zero division
    denominator[denominator < 1e-6] = 1e-6
    
    curvature = numerator / denominator
    
    # 3. Curvature Variation (Jerk proxy)
    curvature_change = np.diff(curvature)
    
    print(f"--- {label} ---")
    print(f"  Nodes: {len(nodes_array)}")
    print(f"  Spacing: {avg_spacing:.4f} m (std: {std_spacing:.4f})")
    print(f"  Max Curvature: {np.max(np.abs(curvature)):.4f}")
    print(f"  Sum Curvature Change (Wiggle): {np.sum(np.abs(curvature_change)):.4f}")
    
    return {
        'coords': coords,
        'curvature': curvature,
        'dists': dists
    }

def main():
    analysis_dir = os.path.dirname(os.path.abspath(__file__))
    base_dir = os.path.join(analysis_dir, "recorded_data")
    original_pickle = os.path.join(base_dir, "original_run", "output.pickle")
    output_dir = os.path.join(base_dir, "new_smooth_analysis")
    os.makedirs(output_dir, exist_ok=True)
    
    # 1. Load Original Data (from Pickle)
    nodes, edges = load_graph_nodes(original_pickle)
    if nodes is None or len(nodes) == 0:
        print("Failed to load nodes from pickle.")
        return

    dm = DataManager(nodes, edges, [])
    
    # 2. Extract Path to Smooth
    path_ids = get_longest_path(nodes, edges)
    # Sort key? path_ids is ordered from start to end by nx.shortest_path
    
    # Get original coords ordered by path
    original_coords = []
    for pid in path_ids:
        mask = nodes[:, 0] == pid
        original_coords.append(nodes[mask][0]) # Keep full node row
    original_nodes_ordered = np.array(original_coords)
    
    # 3. Apply New Smoothing
    # Setup CurveManager
    pm = MockPlotManager()
    eh = MockEventHandler()
    cm = CurveManager(dm, pm, eh)
    
    # Set selection (entire path)
    eh.smoothing_path_ids = path_ids
    
    print(f"Applying new smoothing to {len(path_ids)} points...")
    new_points_xy = cm._smooth_segment(path_ids)
    
    # Construct "New" node array for analysis
    new_nodes = np.zeros((len(new_points_xy), 7))
    new_nodes[:, 1:3] = new_points_xy
    
    # 4. Analysis & Comparison
    stats_orig = analyze_smoothness(original_nodes_ordered, "Original Nodes (2m)")
    stats_new = analyze_smoothness(new_nodes, "New Smoothed (0.5m)")
    
    # 5. Plotting
    # Plot 1: Geometry
    plt.figure(figsize=(10, 6))
    plt.plot(stats_orig['coords'][:, 0], stats_orig['coords'][:, 1], 'k.', label='Original', alpha=0.3)
    plt.plot(stats_new['coords'][:, 0], stats_new['coords'][:, 1], 'r-', label='New Smoothed (0.5m)', linewidth=1)
    # Zoom in on a section
    # plt.xlim(...)
    plt.legend()
    plt.title("Path Geometry Comparison")
    plt.xlabel("X (m)")
    plt.ylabel("Y (m)")
    plt.axis('equal')
    plt.savefig(os.path.join(output_dir, "geometry_comparison.png"))
    
    # Plot 2: Point Spacing
    plt.figure(figsize=(10, 6))
    plt.hist(stats_orig['dists'], bins=50, alpha=0.5, label='Original')
    plt.hist(stats_new['dists'], bins=50, alpha=0.5, label='New Smoothed', color='r')
    plt.axvline(0.5, color='b', linestyle='--', label='Target (0.5m)')
    plt.legend()
    plt.title("Point Spacing Distribution")
    plt.xlabel("Distance between points (m)")
    plt.savefig(os.path.join(output_dir, "spacing_histogram.png"))
    
    # Plot 3: Curvature
    plt.figure(figsize=(10, 6))
    plt.plot(stats_orig['curvature'], label='Original', alpha=0.5)
    plt.plot(np.linspace(0, len(stats_orig['curvature']), len(stats_new['curvature'])), stats_new['curvature'], 'r-', label='New Smoothed')
    plt.legend()
    plt.title("Curvature Profile")
    plt.ylim(-0.5, 0.5) # Limit y-axis to see details
    plt.savefig(os.path.join(output_dir, "curvature_profile.png"))

    print(f"Analysis complete. Results saved to {output_dir}")

if __name__ == "__main__":
    main()
