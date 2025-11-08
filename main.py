import os

import matplotlib.pyplot as plt
import numpy as np

# These imports assume your package structure
from DataVisualizationEditingTool.utils.data_loader import DataLoader
from DataVisualizationEditingTool.utils.data_manager import DataManager
from DataVisualizationEditingTool.utils.event_handler import EventHandler
from DataVisualizationEditingTool.utils.plot_manager import PlotManager


def main():
    # Get path where the user is running the .exe from
    base_path = os.getcwd()  # Not sys._MEIPASS

    # Use that to find the 'lanes' folder
    lanes_path = os.path.join(base_path, 'backup_lanes')

    if not os.path.isdir(lanes_path):
        raise ValueError(f"Directory does not exist: {lanes_path}")

    # Load data
    custom_order = ["lane-0.npy", "lane-3.npy", "lane-2.npy", "lane-1.npy"]
    loader = DataLoader(lanes_path, file_order=custom_order)

    # Unpack 3 values (nodes, edges, file_names) 
    nodes, edges, file_names = loader.load_data()
    D = loader.D

    # Debug: Verify the data loaded
    if nodes.size > 0:
        print(f"Loaded {len(file_names)} files,  total nodes: {nodes.shape[0]}, total edges: {edges.shape[0]}")
        # Column 4 is 'original_lane_id'
        print(f"Unique lane IDs: {np.unique(nodes[:, 4])}")
    else:
        print("No data loaded")
        return

    # Initialize managers with nodes and edges 
    data_manager = DataManager(nodes, edges, file_names)
    event_handler = EventHandler(data_manager)

    # Pass nodes and edges instead of merged_data
    plot_manager = PlotManager(nodes, edges, file_names, D, data_manager, event_handler)

    event_handler.set_plot_manager(plot_manager)
    event_handler.update_point_sizes()

    plt.show()


if __name__ == "__main__":
    main()
