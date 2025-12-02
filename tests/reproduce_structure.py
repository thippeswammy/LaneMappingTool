import numpy as np
import os
import sys

# Add root to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from utils.data_loader import DataLoader
from utils.data_manager import DataManager

def test_structure():
    # Create a dummy raw file
    os.makedirs('lanes/TEST_STRUCT', exist_ok=True)
    raw_data = np.array([[10, 20], [30, 40]]) # x, y
    np.save('lanes/TEST_STRUCT/lane-0.npy', raw_data)

    loader = DataLoader('lanes/TEST_STRUCT')
    nodes, edges, names = loader.load_data()
    
    print(f"Loaded nodes shape: {nodes.shape}")
    print(f"Nodes columns: {nodes.shape[1]}")
    print("Sample node:", nodes[0])

    # Check if it matches (point_id, x, y, yaw, zone, width, indicator)
    # Current expectation: 5 columns (point_id, x, y, yaw, original_lane_id)
    
    if nodes.shape[1] == 5:
        print("Current structure has 5 columns.")
    elif nodes.shape[1] == 7:
        print("Current structure has 7 columns.")
    else:
        print(f"Current structure has {nodes.shape[1]} columns.")

    # Initialize DataManager and save
    dm = DataManager(nodes, edges, names)
    dm.save_by_matplotlib()
    
    # Load back and check
    loaded_nodes = np.load('./files/WorkingNodes.npy')
    print(f"Saved nodes shape: {loaded_nodes.shape}")

if __name__ == "__main__":
    test_structure()
