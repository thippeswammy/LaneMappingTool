import matplotlib.pyplot as plt

from data_loader import DataLoader
from data_manager import DataManager
from event_handler import EventHandler
from plot_manager import PlotManager


def main():
    merged_data, file_names, D = DataLoader.load_and_merge_npy_files()
    if D is None and not file_names:
        print("No .npy files found.")
        return
    # print(merged_data)
    data_manager = DataManager(merged_data, file_names, D)
    event_handler = EventHandler(data_manager)
    plot_manager = PlotManager(merged_data, file_names, D, data_manager, event_handler)
    event_handler.set_plot_manager(plot_manager)  # Set plot_manager and initialize curve_manager
    plt.show()


if __name__ == '__main__':
    main()
