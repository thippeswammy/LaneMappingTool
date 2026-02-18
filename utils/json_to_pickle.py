import json
import os
import sys

import networkx as nx
from networkx.readwrite import json_graph

try:
    import matplotlib.pyplot as plt
    HAS_MATPLOTLIB = True
except ImportError:
    HAS_MATPLOTLIB = False


def plot_graph(G):
    """
    Visualizes the graph using matplotlib.
    """
    if not HAS_MATPLOTLIB:
        print("Warning: matplotlib not found. Skipping plot.")
        return

    print("Plotting graph...")
    pos = {}
    for node, data in G.nodes(data=True):
        if 'x' in data and 'y' in data:
            pos[node] = (data['x'], data['y'])
        else:
            # Fallback to spring layout if coordinates are missing
            pos = nx.spring_layout(G)
            break
    
    plt.figure(figsize=(10, 8))
    
    # Draw edges
    nx.draw_networkx_edges(G, pos, alpha=0.5, edge_color='gray')
    
    # Draw nodes
    nx.draw_networkx_nodes(G, pos, node_size=50, node_color='blue', alpha=0.7)
    
    # Optional: Draw yaw as arrows if available
    for node, data in G.nodes(data=True):
        if 'x' in data and 'y' in data and 'yaw' in data:
            import numpy as np
            dx = 0.2 * np.cos(data['yaw'])
            dy = 0.2 * np.sin(data['yaw'])
            plt.arrow(data['x'], data['y'], dx, dy, head_width=0.05, head_length=0.1, fc='red', ec='red')

    plt.title("Graph Visualization ({} nodes, {} edges)".format(len(G.nodes()), len(G.edges())))
    plt.axis('equal')
    plt.grid(True)
    print("Close the plot window to continue...")
    plt.show()


def convert_json_to_pickle(json_path, pickle_path, should_plot=False):
    """
    Reads a NetworkX graph from a JSON file (node-link format) and saves it as a Pickle.
    Compatible with Python 2.7 and older NetworkX versions.
    """
    if not os.path.exists(json_path):
        print("Error: JSON file '{}' not found.".format(json_path))
        sys.exit(1)

    print("Loading JSON from '{}'...".format(json_path))
    try:
        with open(json_path, 'r') as f:
            data = json.load(f)
    except Exception as e:
        print("Error reading JSON file: {}".format(e))
        sys.exit(1)

    print("Converting to NetworkX graph...")
    try:
        # node_link_graph handles the reconstruction of the graph object
        G = json_graph.node_link_graph(data)
        
        # JSON keys are always strings, but our original graph used integers.
        # We must convert node IDs back to int to match legacy behavior.
        print("Converting node IDs to integers...")
        G = nx.relabel_nodes(G, int)
        
    except Exception as e:
        print("Error converting JSON to Graph: {}".format(e))
        sys.exit(1)

    print("Graph Info: Nodes: {}, Edges: {}".format(len(G.nodes()), len(G.edges())))

    if should_plot:
        plot_graph(G)

    print("Saving to Pickle '{}'...".format(pickle_path))
    try:
        # Note: nx.write_gpickle is specific to older NetworkX/Python 2.
        # For Python 3, it's usually just pickle.dump(G, f) or nx.write_gpickle
        # as long as the environment supports it.
        if hasattr(nx, 'write_gpickle'):
            nx.write_gpickle(G, pickle_path)
        else:
            import pickle
            with open(pickle_path, 'wb') as f:
                pickle.dump(G, f, protocol=2) # Protocol 2 for Python 2 compatibility
        print("Success! Pickle file created.")
    except Exception as e:
        print("Error writing pickle file: {}".format(e))
        sys.exit(1)


if __name__ == "__main__":
    # Default paths
    input_json = "output.json"
    output_pickle = "output.pickle"
    should_plot = False

    # Simple argument parsing
    args = sys.argv[1:]
    if "--plot" in args:
        should_plot = True
        args.remove("--plot")

    if len(args) > 0:
        input_json = args[0]
    if len(args) > 1:
        output_pickle = args[1]

    print("--------------------------------------------------")
    print("JSON to Pickle Converter (with Plotting)")
    print("--------------------------------------------------")
    convert_json_to_pickle(input_json, output_pickle, should_plot=should_plot)
