import matplotlib.pyplot as plt
import numpy as np
import time
from matplotlib.widgets import Slider, RectangleSelector, Button

class PlotManager:
    def __init__(self, data, file_names, D, data_manager, event_handler):
        self.data_manager = data_manager
        self.file_names = file_names
        self.D = D
        self.event_handler = event_handler
        self.fig, self.ax = plt.subplots(figsize=(12, 8))
        self.lane_scatter_plots = []
        self.start_point_plots = []
        self.extra_scatter_plots = []
        self.indices = []
        self.selected_indices = []
        self.highlighted_lane = None
        self.grid_visible = False
        self.tooltip = self.ax.text(0, 0, '', bbox=dict(facecolor='white', alpha=0.8), visible=False)
        self.nearest_point = None
        self.rs = RectangleSelector(self.ax, self.event_handler.on_select, useblit=True, button=[1])
        self.slider_smooth = None
        self.slider_size = None
        self.setup_widgets()
        self.setup_navigation()
        self.update_plot(data)

    def setup_widgets(self):
        ax_size = plt.axes([0.15, 0.02, 0.65, 0.03])
        self.slider_size = Slider(ax_size, 'Point Size', 1, 100, valinit=10)
        self.slider_size.on_changed(self.event_handler.update_point_sizes)

        ax_smooth = plt.axes([0.15, 0.06, 0.65, 0.03])
        self.slider_smooth = Slider(ax_smooth, 'Smoothness', 0.1, 10.0, valinit=1.0)

        self.fig.canvas.draw()

    def setup_navigation(self):
        self.fig.canvas.mpl_connect('scroll_event', self.on_scroll)
        self.fig.canvas.mpl_connect('motion_notify_event', self.on_motion)
        self.fig.canvas.mpl_connect('pick_event', self.on_legend_pick)
        self.ax.set_navigate(True)

    def on_scroll(self, event):
        if event.inaxes != self.ax:
            return
        try:
            base_scale = 1.1
            cur_xlim = self.ax.get_xlim()
            cur_ylim = self.ax.get_ylim()
            xdata = event.xdata
            ydata = event.ydata
            if event.button == 'up':
                scale = 1 / base_scale
            elif event.button == 'down':
                scale = base_scale
            else:
                return
            new_width = (cur_xlim[1] - cur_xlim[0]) * scale
            new_height = (cur_ylim[1] - cur_ylim[0]) * scale
            self.ax.set_xlim([xdata - new_width * (xdata - cur_xlim[0]) / (cur_xlim[1] - cur_xlim[0]),
                              xdata + new_width * (cur_xlim[1] - xdata) / (cur_xlim[1] - cur_xlim[0])])
            self.ax.set_ylim([ydata - new_height * (ydata - cur_ylim[0]) / (cur_ylim[1] - cur_ylim[0]),
                              ydata + new_height * (cur_ylim[1] - ydata) / (cur_ylim[1] - cur_ylim[0])])
            self.fig.canvas.draw_idle()
        except Exception as e:
            print(f"Error during scroll: {e}")

    def on_motion(self, event):
        if event.inaxes != self.ax or self.data_manager.data.size == 0:
            self.tooltip.set_visible(False)
            if self.nearest_point:
                self.nearest_point.remove()
                self.nearest_point = None
            self.fig.canvas.draw_idle()
            return
        try:
            x, y = event.xdata, event.ydata
            distances = np.sqrt((self.data_manager.data[:, 0] - x) ** 2 + (self.data_manager.data[:, 1] - y) ** 2)
            closest_idx = np.argmin(distances)
            if distances[closest_idx] < self.D / 100:
                point = self.data_manager.data[closest_idx]
                self.tooltip.set_text(
                    f'X: {point[0]:.2f}\nY: {point[1]:.2f}\nLane: {int(point[-1])}\nIndex: {int(point[4])}')
                self.tooltip.set_position((point[0], point[1]))
                self.tooltip.set_visible(False)
                if self.nearest_point:
                    self.nearest_point.remove()
                self.nearest_point = self.ax.scatter(point[0], point[1], s=30, color='cyan', marker='o', alpha=0.5)
            else:
                self.tooltip.set_visible(False)
                if self.nearest_point:
                    self.nearest_point.remove()
                    self.nearest_point = None
            self.fig.canvas.draw_idle()
        except Exception as e:
            print(f"Error during motion: {e}")

    def on_legend_pick(self, event):
        if event.artist in self.ax.legend_.get_lines():
            try:
                idx = self.ax.legend_.get_lines().index(event.artist)
                if idx < len(self.lane_scatter_plots):
                    lane_id = int(np.unique(self.data_manager.data[self.indices[idx], -1])[0])
                    if self.highlighted_lane == lane_id:
                        self.highlighted_lane = None
                    else:
                        self.highlighted_lane = lane_id
                    self.event_handler.update_point_sizes()
                    self.update_status(f"{'Highlighted' if self.highlighted_lane is not None else 'Unhighlighted'} lane {lane_id}")
            except Exception as e:
                print(f"Error during legend pick: {e}")
        self.fig.canvas.draw_idle()

    def setup_legend_handler(self):
        self.ax.legend_ = self.ax.legend()
        for legend_line in self.ax.legend_.get_lines():
            legend_line.set_picker(True)
            legend_line.set_pickradius(5)

    def update_plot(self, data, selected_indices=None):
        if selected_indices is None:
            selected_indices = self.selected_indices
        self.selected_indices = selected_indices

        start_time = time.time()
        try:
            # Remove all existing scatter plots
            for plot in self.lane_scatter_plots + self.start_point_plots + self.extra_scatter_plots:
                plot.remove()
            # Remove smoothing preview line separately if it exists
            if self.event_handler.smoothing_preview_line is not None:
                try:
                    self.event_handler.smoothing_preview_line.remove()
                except ValueError:
                    pass  # Line already removed
                self.event_handler.smoothing_preview_line = None
            self.lane_scatter_plots = []
            self.start_point_plots = []
            self.extra_scatter_plots = []
            self.indices = []

            if data.size == 0:
                self.ax.set_title("No Data")
                self.fig.canvas.draw_idle()
                return

            unique_lane_ids = np.unique(data[:, -1])
            colors = plt.cm.get_cmap('tab10')(np.linspace(0, 1, max(len(unique_lane_ids), 10)))

            for lane_id in unique_lane_ids:
                mask = data[:, -1] == lane_id
                lane_data = data[mask]
                if len(lane_data) > 0:
                    label = self.file_names[int(lane_id)] if int(lane_id) < len(self.file_names) else f"Lane {lane_id}"
                    sc = self.ax.scatter(lane_data[:, 0], lane_data[:, 1], s=10, label=label,
                                         color=colors[int(lane_id)], marker='o', picker=True)
                    self.lane_scatter_plots.append(sc)
                    self.indices.append(np.where(mask)[0])

                    start_idx = lane_data[:, 4].argmin()
                    start_point = lane_data[start_idx]
                    start_sc = self.ax.scatter(start_point[0], start_point[1], s=50, color=colors[int(lane_id)],
                                               marker='s', label=f'Lane {lane_id} Start')
                    self.start_point_plots.append(start_sc)

            if selected_indices:
                selected_points = data[np.array(selected_indices, dtype=int)]
                sc = self.ax.scatter(selected_points[:, 0], selected_points[:, 1], s=50, color='red', marker='o',
                                     label='Selected')
                self.extra_scatter_plots.append(sc)

            if self.event_handler.merge_mode:
                if self.event_handler.merge_point_1 is not None:
                    point_1 = data[self.event_handler.merge_point_1]
                    marker = '>' if self.event_handler.merge_point_1_type == 'end' else '<'
                    sc = self.ax.scatter(point_1[0], point_1[1], s=100, color='purple', marker=marker,
                                         label=f'Lane {self.event_handler.merge_lane_1} {self.event_handler.merge_point_1_type}')
                    self.extra_scatter_plots.append(sc)
                if self.event_handler.merge_point_2 is not None:
                    point_2 = data[self.event_handler.merge_point_2]
                    marker = '>' if self.event_handler.merge_point_2_type == 'end' else '<'
                    sc = self.ax.scatter(point_2[0], point_2[1], s=100, color='orange', marker=marker,
                                         label=f'Lane {self.event_handler.merge_lane_2} {self.event_handler.merge_point_2_type}')
                    self.extra_scatter_plots.append(sc)

            self.ax.set_xlabel('X')
            self.ax.set_ylabel('Y')
            self.ax.set_title('Lane Data Visualization')
            self.ax.grid(self.grid_visible)
            self.ax.legend()
            self.setup_legend_handler()
            self.fig.canvas.draw_idle()

            print(f"Plot updated in {time.time() - start_time:.3f} seconds")
        except Exception as e:
            print(f"Error in update_plot: {e}")
            self.update_status(f"Error: {e}")

    def update_status(self, message=""):
        try:
            self.ax.set_title(f'Lane Data Visualization: {message}' if message else 'Lane Data Visualization')
            self.fig.canvas.draw_idle()
        except Exception as e:
            print(f"Error in update_status: {e}")