from data_loader import DataLoader
from data_manager import DataManager
from plot_manager import PlotManager
from event_handler import EventHandler
import matplotlib.pyplot as plt


def main():
    merged_data, file_names, D = DataLoader.load_and_merge_npy_files()
    if D is None and not file_names:
        print("No .npy files found.")
        return

    data_manager = DataManager(merged_data, file_names, D)
    event_handler = EventHandler(data_manager, None)  # PlotManager will set itself
    plot_manager = PlotManager(merged_data, file_names, D, data_manager, event_handler)
    event_handler.plot_manager = plot_manager  # Complete the circular reference
    plt.show()


if __name__ == '__main__':
    main()
