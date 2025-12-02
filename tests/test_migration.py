import numpy as np
import os
import sys

# Add root to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from utils.data_loader import DataLoader

def test_migration():
    # Create a dummy 5-column saved file
    os.makedirs('files_test', exist_ok=True)
    
    # 5 columns: point_id, x, y, yaw, original_lane_id
    old_nodes = np.array([
        [0, 10, 20, 0.1, 1],
        [1, 30, 40, 0.2, 1]
    ])
    old_edges = np.array([[0, 1]])
    
    nodes_path = 'files_test/OldNodes.npy'
    edges_path = 'files_test/OldEdges.npy'
    
    np.save(nodes_path, old_nodes)
    np.save(edges_path, old_edges)
    
    print(f"Created old nodes with shape: {old_nodes.shape}")
    
    loader = DataLoader('lanes') # Directory doesn't matter for load_graph_data
    
    # Load and check for migration
    nodes, edges, names, D = loader.load_graph_data(nodes_path, edges_path)
    
    print(f"Loaded nodes shape: {nodes.shape}")
    
    if nodes.shape[1] == 7:
        print("Migration successful: Nodes have 7 columns.")
        # Check if original data is preserved
        if np.allclose(nodes[:, :5], old_nodes):
            print("Data integrity check passed.")
        else:
            print("Data integrity check FAILED.")
            
        # Check if new columns are 0
        if np.all(nodes[:, 5:] == 0):
             print("New columns initialized to 0.")
        else:
             print("New columns NOT initialized to 0.")
             
    else:
        print(f"Migration FAILED: Nodes have {nodes.shape[1]} columns.")

if __name__ == "__main__":
    test_migration()
