import matplotlib.pyplot as plt

from data_loader import DataLoader
from data_manager import DataManager
from event_handler import EventHandler
from plot_manager import PlotManager


def main():
    # Load data
    loader = DataLoader("F:/RunningProjects/SAM2/lanes")
    merged_data, file_names = loader.load_data()
    D = loader.D

    # Initialize managers
    data_manager = DataManager(merged_data, file_names)
    event_handler = EventHandler(data_manager)
    plot_manager = PlotManager(merged_data, file_names, D, data_manager, event_handler)

    # Set plot manager in event handler before setup_plot is called
    event_handler.set_plot_manager(plot_manager)

    # Show plot
    plt.show()


if __name__ == "__main__":
    main()
