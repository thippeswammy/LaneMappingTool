import os
import sys
import pickle
import numpy as np
import networkx as nx

# Setup paths
BASE_DIR = r"f:/RunningProjects/LaneMappingTool"
sys.path.append(BASE_DIR)

from utils.data_loader import DataLoader
from utils.data_manager import DataManager

RAW_DATA_PATH = os.path.join(BASE_DIR, "lanes", "Gitam_lanes")
OUTPUT_DIR = os.path.join(BASE_DIR, "web", "backend", "workspace")

def regenerate_pickle():
    print("Initializing DataLoader with fixed logic...")
    loader = DataLoader(RAW_DATA_PATH)
    
    print(f"Loading data from {RAW_DATA_PATH}...")
    # Load all default files as the app would on startup/reset
    nodes, edges, file_names = loader.load_data()
    
    if nodes.size == 0:
        print("Error: No data loaded.")
        return

    print(f"Loaded {nodes.shape[0]} nodes. Initializing DataManager...")
    dm = DataManager(nodes, edges, file_names)
    
    # Save using the web format (which includes output.pickle)
    print(f"Saving to {OUTPUT_DIR}...")
    dm.save_by_web(OUTPUT_DIR)
    print("Regeneration complete. output.pickle should now contain correct yaw/steering data.")

if __name__ == "__main__":
    regenerate_pickle()
