import pickle
import networkx as nx
import numpy as np
import math
import os

# Paths to check
files_to_check = [
    "web/backend/workspace/output.pickle",
    "lanes/thipp/output.pickle",
    "lanes/thipp/output1.pickle"
]

npy_files_to_check = [
    "web/backend/workspace/graph_nodes.npy",
    "lanes/thipp/graph_nodes.npy"
]

def inspect_graph():
    # 1. Try Pickle Files
    for graph_file_path in files_to_check:
        print(f"\nScanning Pickle: {graph_file_path}...")
        if not os.path.exists(graph_file_path):
            print(f"File {graph_file_path} not found.")
            continue

        graph_loaded = False
        G = None
        
        try:
            with open(graph_file_path, 'rb') as f:
                G = pickle.load(f)
            print("Graph loaded successfully using pickle.load().")
            graph_loaded = True
        except Exception as e:
            print(f"Standard load failed: {e}")
            try:
                with open(graph_file_path, 'rb') as f:
                    G = pickle.load(f, encoding='latin1')
                print("Graph loaded successfully using encoding='latin1'.")
                graph_loaded = True
            except Exception as e2:
                print(f"Latin1 load failed: {e2}")

        if graph_loaded:
            try:
                print(f"Graph type: {type(G)}")
                # This might fail if the object is broken
                if hasattr(G, 'number_of_nodes'):
                    print(f"Number of nodes: {G.number_of_nodes()}")
                if hasattr(G, 'number_of_edges'):
                    print(f"Number of edges: {G.number_of_edges()}")
                
                # Try iterating
                print("--- Inspecting first 2 nodes ---")
                nodes_list = list(G.nodes(data=True))[:2]
                for node_id, data in nodes_list:
                    print(f"Node {node_id}: {data}")

            except Exception as e:
                print(f"Error inspecting loaded graph object: {e}")

    # 2. Try NPY Files (Fallback)
    print("\n\n--- Inspecting .npy files (Raw Data) ---")
    for npy_path in npy_files_to_check:
        print(f"\nScanning NPY: {npy_path}...")
        if not os.path.exists(npy_path):
            print(f"File {npy_path} not found.")
            continue
            
        try:
            data = np.load(npy_path)
            print(f"Loaded shape: {data.shape}")
            if data.size == 0:
                print("Empty data.")
                continue
                
            # Expecting format based on data_manager.py:
            # [point_id, x, y, yaw, zone, width, indicator]
            print(f"Columns: [point_id, x, y, yaw, zone, width, indicator]")
            print("--- First 2 rows ---")
            print(data[:2])
            
            # Simulate "Closest Node"
            target_x = data[0][1]
            target_y = data[0][2]
            print(f"Simulating search near ({target_x:.2f}, {target_y:.2f})...")
            
            # Calculate distances
            # dist = sqrt((x-tx)^2 + (y-ty)^2)
            dists = np.sqrt((data[:, 1] - target_x)**2 + (data[:, 2] - target_y)**2)
            closest_idx = np.argmin(dists)
            closest_row = data[closest_idx]
            
            print(f"Closest Node ID: {closest_row[0]} at distance {dists[closest_idx]:.4f}")
            print(f"Node Data: {closest_row}")
            
        except Exception as e:
            print(f"Error loading npy: {e}")


if __name__ == "__main__":
    inspect_graph()
