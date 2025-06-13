import matplotlib.pyplot as plt
import numpy as np

from data_loader import DataLoader
from data_manager import DataManager
from event_handler import EventHandler
from plot_manager import PlotManager


def main():
    # Load data
    loader = DataLoader("F:/RunningProjects/SAM2/lanes")
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

    # Set plot manager in event handler
    event_handler.set_plot_manager(plot_manager)

    # Update point sizes after initialization
    event_handler.update_point_sizes()

    # Show plot
    plt.show()


if __name__ == "__main__":
    main()
