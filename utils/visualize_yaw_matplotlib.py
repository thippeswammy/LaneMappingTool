
import pickle
import matplotlib.pyplot as plt
import numpy as np
import sys
import os
import networkx as nx

def visualize_yaw(pickle_path):
    print(f"Loading graph from {pickle_path}...")
    try:
        with open(pickle_path, 'rb') as f:
            G = pickle.load(f)
    except Exception as e:
        print(f"Error loading pickle: {e}")
        return

    print(f"Graph loaded. Nodes: {len(G.nodes)}")

    x_vals = []
    y_vals = []
    u_vals = []
    v_vals = []
    colors = []

    for node in G.nodes():
        try:
            data = G.nodes[node]
        except TypeError:
            data = G.node[node]
            
        x = data['x']
        y = data['y']
        yaw = data.get('yaw', 0.0)
        
        x_vals.append(x)
        y_vals.append(y)
        u_vals.append(np.cos(yaw))
        v_vals.append(np.sin(yaw))
        
        # Color by zone if available
        colors.append(data.get('zone', 0))

    fig, ax = plt.subplots(figsize=(12, 10))
    
    # Plot edges first (background)
    print("Plotting edges...")
    for u, v in G.edges():
        try:
            udata = G.nodes[u] if hasattr(G, 'nodes') and u in G.nodes else G.node[u]
            vdata = G.nodes[v] if hasattr(G, 'nodes') and v in G.nodes else G.node[v]
            ax.plot([udata['x'], vdata['x']], [udata['y'], vdata['y']], 'gray', alpha=0.3, linewidth=1)
        except Exception:
            pass

    # Plot Quiver (Arrows)
    print("Plotting arrows...")
    # Masking: Plotting every arrow might be too dense. Let's plot all for now, or strided.
    # If thousands of nodes, maybe stride by 1? (User wants to see smoothness, so all is better)
    
    q = ax.quiver(x_vals, y_vals, u_vals, v_vals, colors, cmap='viridis', scale=50, width=0.002, headwidth=4)
    
    ax.set_title(f"Yaw Visualization: {os.path.basename(pickle_path)}")
    ax.set_xlabel("X (m)")
    ax.set_ylabel("Y (m)")
    ax.axis('equal')
    ax.grid(True)
    
    plt.colorbar(q, label='Zone ID')
    
    print("Displaying plot...")
    plt.show()

if __name__ == "__main__":
    path_arg = None
    if len(sys.argv) > 1:
        path_arg = sys.argv[1]
    else:
        # Default to correct workspace path
        base_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'web', 'backend', 'workspace'))
        path_arg = os.path.join(base_dir, 'output_fixed.pickle')
        
        if not os.path.exists(path_arg):
             # Fallback to output.pickle if fixed one doesn't exist
             path_arg = os.path.join(base_dir, 'output.pickle')

    if path_arg and os.path.exists(path_arg):
        visualize_yaw(path_arg)
    else:
        print(f"File not found: {path_arg}")
        print("Usage: python visualize_yaw_matplotlib.py [pickle_file_path]")
