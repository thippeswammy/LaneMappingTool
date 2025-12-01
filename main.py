import os

import matplotlib.pyplot as plt
import numpy as np

from utils.data_loader import DataLoader
from utils.data_manager import DataManager
from utils.event_handler import EventHandler
from utils.plot_manager import PlotManager


def main():
    """Main function to load, merge, and manage data for processing.
    
    This function orchestrates the loading of existing and new data files,
    calculates necessary parameters, and initializes various managers for data
    handling and visualization. It checks for the existence of saved working files,
    loads them if available, and merges them with new raw data files. The function
    also handles ID offsets to avoid conflicts and sets up the necessary components
    for further data processing and visualization.
    """
    base_path = os.getcwd()
    files_dir = os.path.join(base_path, 'files')
    original_data_path = os.path.join(base_path, 'lanes','TEMP1')

    # These files must exist in your 'original_data_path' folder
    files_path_ = ["lane-0.npy"]

    nodes_path = os.path.join(files_dir, 'graph_nodes.npy')
    edges_path = os.path.join(files_dir, 'graph_edges.npy')
    files_path = [os.path.join(original_data_path, i) for i in files_path_]
    # Initialize variables
    final_nodes = np.array([])
    final_edges = np.array([])
    file_names = []
    D = 1.0

    #  Load Saved Working Data
    if os.path.exists(nodes_path) and os.path.exists(edges_path):
        print("Loading saved working files...")
        saved_nodes = np.load(nodes_path)
        saved_edges = np.load(edges_path)

        # Calculate basic D from saved data
        if saved_nodes.size > 0:
            p2d = saved_nodes[:, 1:3]
            dists = np.sqrt(((p2d[:, None] - p2d[None, :]) ** 2).sum(axis=-1))
            D = np.max(dists) if dists.size > 0 else 1.0

            # Reconstruct file names for saved data
            unique_lanes = np.unique(saved_nodes[:, 4]).astype(int)
            file_names = [f"Edited Lane {i}" for i in unique_lanes]

        final_nodes = saved_nodes
        final_edges = saved_edges
        print(f"Loaded edited data: {len(final_nodes)} nodes.")
    else:
        print("No working files found. Starting clean.")

    # Load new Raw Data and Merge
    if files_path:
        print(f"Attempting to merge {len(files_path)} new raw files...")
        loader = DataLoader(original_data_path)

        # Calculate ID offset
        start_id_offset = 0
        lane_id_offset = 0

        if final_nodes.size > 0:
            # Start IDs after the highest existing ID
            start_id_offset = int(np.max(final_nodes[:, 0])) + 1
            # Start Lane IDs after the highest existing Lane ID
            lane_id_offset = int(np.max(final_nodes[:, 4])) + 1

        # Load specific new files with offset
        new_nodes, new_edges, new_names = loader.load_data(
            specific_files=files_path,
            start_id=start_id_offset
        )

        if new_nodes.size > 0:
            # Adjust Lane IDs for the new nodes to avoid color conflict
            new_nodes[:, 4] += lane_id_offset

            # Merge Data
            if final_nodes.size > 0:
                final_nodes = np.vstack([final_nodes, new_nodes])
                final_edges = np.vstack([final_edges, new_edges])
                file_names.extend(new_names)
                # Update D
                D = max(D, loader.D)
            else:
                final_nodes = new_nodes
                final_edges = new_edges
                file_names = new_names
                D = loader.D

            print(f"Merged successfully. Total: {final_nodes.shape[0]} nodes.")
        else:
            print("Could not load new files (check filenames/paths).")

    if final_nodes.size == 0:
        print("No data loaded at all.")
        return

    # Initialize Managers
    data_manager = DataManager(final_nodes, final_edges, file_names)
    event_handler = EventHandler(data_manager)
    plot_manager = PlotManager(final_nodes, final_edges, file_names, D, data_manager, event_handler)

    event_handler.set_plot_manager(plot_manager)
    event_handler.update_point_sizes()

    plt.show()


if __name__ == "__main__":
    main()
