import pickle
import networkx as nx
import os

try:
    file_path = r'f:\RunningProjects\LaneMappingTool\point_save\output.pickle'
    if os.path.exists(file_path):
        with open(file_path, 'rb') as f:
            data = pickle.load(f)
        
        print(f"File found and loaded. Type: {type(data)}")
        
        if isinstance(data, nx.Graph):
            print(f"Graph loaded with {data.number_of_nodes()} nodes and {data.number_of_edges()} edges.")
            if data.number_of_nodes() > 0:
                print("First 5 nodes:", list(data.nodes(data=True))[:5])
                print("First 5 edges:", list(data.edges(data=True))[:5])
        else:
            print("Data:", data)
    else:
        print(f"File not found at {file_path}")
except Exception as e:
    print(f"Error loading pickle: {e}")
