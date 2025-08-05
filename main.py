import os

import matplotlib
matplotlib.use('TkAgg')
import matplotlib.pyplot as plt
import numpy as np

from DataVisualizationEditingTool.utils.data_loader import DataLoader
from DataVisualizationEditingTool.utils.data_manager import DataManager
from DataVisualizationEditingTool.utils.event_handler import EventHandler
from DataVisualizationEditingTool.utils.plot_manager import PlotManager

def main():
    # Get path where the user is running the .exe from
    base_path = os.getcwd()  # Not sys._MEIPASS

    # Use that to find the 'lanes' folder
    lanes_path = os.path.join(base_path, 'lanes')

    if not os.path.isdir(lanes_path):
        raise ValueError(f"Directory does not exist: {lanes_path}")

    # Load data
    loader = DataLoader(lanes_path)
    merged_data, file_names = loader.load_data()
    D = loader.D

    # Debug: Verify the data loaded
    if merged_data.size > 0:
        print(f"Loaded {len(file_names)} files, total points: {merged_data.shape[0]}")
        print(f"Unique lane IDs: {np.unique(merged_data[:, -1])}")
    else:
        print("No data loaded into merged_data")
        return

    # Initialize managers
    data_manager = DataManager(merged_data, file_names)
    event_handler = EventHandler(data_manager)
    plot_manager = PlotManager(merged_data, file_names, D, data_manager, event_handler)

    event_handler.set_plot_manager(plot_manager)
    event_handler.update_point_sizes()

    plt.show()


if __name__ == "__main__":
    main()
