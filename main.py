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
    graph_dir = os.path.join(base_path, 'files')
    raw_data_path = os.path.join(base_path, 'lanes', 'TEMP1')

    # Paths for saved working state
    nodes_path = os.path.join(graph_dir, 'graph_nodes.npy')
    edges_path = os.path.join(graph_dir, 'graph_edges.npy')

    # These files must exist in your 'raw_data_path' folder
    files_path_ = ["lane-20.npy", "lane-30.npy"]
    files_path = [os.path.join(raw_data_path, i) for i in files_path_]

    # Initialize DataLoader
    loader = DataLoader(raw_data_path)

    # Load Saved Working Data (Graph Nodes/Edges)
    final_nodes, final_edges, file_names, D = loader.load_graph_data(nodes_path, edges_path)

    # Load New Raw Data and Merge
    if files_path:
        print(f"Attempting to merge {len(files_path)} new raw files...")

        # Calculate ID offsets to prevent collision with saved graph data
        start_id_offset = 0
        lane_id_offset = 0

        if final_nodes.size > 0:
            # Start IDs after the highest existing ID
            start_id_offset = int(np.max(final_nodes[:, 0])) + 1
            # Start Lane IDs after the highest existing Lane ID
            lane_id_offset = int(np.max(final_nodes[:, 4])) + 1

        # Load specific new files with offset using the SAME loader
        new_nodes, new_edges, new_names = loader.load_data(
            specific_files=files_path_,
            start_id=start_id_offset
        )

        if new_nodes.size > 0:
            # Adjust Lane IDs for the new nodes to avoid color/logic conflict
            new_nodes[:, 4] += lane_id_offset

            # Merge Data
            if final_nodes.size > 0:
                final_nodes = np.vstack([final_nodes, new_nodes])
                final_edges = np.vstack([final_edges, new_edges])
                file_names.extend(new_names)
                # Update D to be the max of existing D and new loader D
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
