import matplotlib.pyplot as plt
import numpy as np
from matplotlib.widgets import Slider, RectangleSelector


class PlotManager:
    def __init__(self, data, file_names, D, data_manager, event_handler):
        self.data_manager = data_manager
        self.file_names = file_names
        self.D = D
        self.event_handler = event_handler
        self.fig, self.ax = plt.subplots(figsize=(12, 8))
        self.scatter_plots = []
        self.indices = []
        self.curve_manager = None
        self.selected_indices = []
        self.rs = RectangleSelector(self.ax, self.event_handler.on_select, useblit=True, button=[1])
        self.slider_smooth = None
        self.slider_size = None
        self.setup_widgets()
        self.update_plot(data)

    def setup_widgets(self):
        ax_size = plt.axes([0.15, 0.02, 0.65, 0.03])
        self.slider_size = Slider(ax_size, 'Point Size', 1, 100, valinit=10)
        self.slider_size.on_changed(self.event_handler.update_point_sizes)

        ax_smooth = plt.axes([0.15, 0.06, 0.65, 0.03])
        self.slider_smooth = Slider(ax_smooth, 'Smoothness', 0.1, 10.0, valinit=1.0)

        self.fig.canvas.draw()

    def update_plot(self, data, selected_indices=None):
        if selected_indices is None:
            selected_indices = self.selected_indices
        self.selected_indices = selected_indices

        for plot in self.scatter_plots:
            plot.remove()
        self.scatter_plots = []
        self.indices = []

        if data.size == 0:
            self.ax.set_title("No Data")
            self.fig.canvas.draw()
            return

        unique_lane_ids = np.unique(data[:, -1])
        colors = plt.cm.get_cmap('tab10')(np.linspace(0, 1, max(len(unique_lane_ids), 10)))

        for lane_id in unique_lane_ids:
            mask = data[:, -1] == lane_id
            lane_data = data[mask]
            if len(lane_data) > 0:
                label = self.file_names[int(lane_id)] if int(lane_id) < len(self.file_names) else f"Lane {lane_id}"
                sc = self.ax.scatter(lane_data[:, 0], lane_data[:, 1], s=10, label=label, color=colors[int(lane_id)],
                                     picker=True)
                self.scatter_plots.append(sc)
                self.indices.append(np.where(mask)[0])

        if selected_indices:
            selected_points = data[np.array(selected_indices, dtype=int)]
            self.ax.scatter(selected_points[:, 0], selected_points[:, 1], s=50, color='red', marker='^',
                            label='Selected')

        if self.event_handler.merge_mode:
            if self.event_handler.merge_point_1 is not None:
                point_1 = data[self.event_handler.merge_point_1]
                marker = '>' if self.event_handler.merge_point_1_type == 'end' else '<'
                self.ax.scatter(point_1[0], point_1[1], s=100, color='purple', marker=marker,
                                label=f'Lane {self.event_handler.merge_lane_1} {self.event_handler.merge_point_1_type}')
            if self.event_handler.merge_point_2 is not None:
                point_2 = data[self.event_handler.merge_point_2]
                marker = '>' if self.event_handler.merge_point_2_type == 'end' else '<'
                self.ax.scatter(point_2[0], point_2[1], s=100, color='orange', marker=marker,
                                label=f'Lane {self.event_handler.merge_lane_2} {self.event_handler.merge_point_2_type}')

        self.ax.set_xlabel('X')
        self.ax.set_ylabel('Y')
        self.ax.set_title('Lane Data Visualization')
        self.ax.legend()
        self.fig.canvas.draw()

    def update_status(self, message=""):
        self.ax.set_title(f'Lane Data Visualization: {message}' if message else 'Lane Data Visualization')
        self.fig.canvas.draw()
