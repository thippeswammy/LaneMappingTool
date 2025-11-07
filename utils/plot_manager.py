import time

import matplotlib.pyplot as plt
import numpy as np
from matplotlib.widgets import Slider, RectangleSelector


class PlotManager:
    def __init__(self, nodes, edges, file_names, D, data_manager, event_handler):
        self.data_manager = data_manager
        self.file_names = file_names
        self.D = D
        self.event_handler = event_handler
        self.fig, self.ax = plt.subplots(figsize=(12, 8))
        self.lane_scatter_plots = []
        self.start_point_plots = []
        self.extra_scatter_plots = []
        self.edge_plots = []  # To hold lines for edges
        self.indices = []

        # This will store the ROW INDICES of selected nodes in self.data_manager.nodes
        self.selected_indices = []

        self.highlighted_lane = None
        self.grid_visible = False
        self.tooltip = self.ax.text(0, 0, '', bbox=dict(facecolor='white', alpha=0.8), visible=False)
        self.nearest_point = None
        self.rs = RectangleSelector(self.ax, self.event_handler.on_select, useblit=True, button=[1])
        self.rs.set_active(False)
        self.slider_smooth = None
        self.slider_size = None
        self.slider_weight = None
        self.setup_widgets()
        self.setup_navigation()

        # Call update_plot with the new graph data
        self.update_plot(nodes, edges)

    def setup_widgets(self):
        ax_size = plt.axes([0.6, 0.02, 0.3, 0.03])
        self.slider_size = Slider(ax_size, 'Point Size', 1, 100, valinit=10)
        # self.slider_size.on_changed(self.event_handler.update_point_sizes) # Re-enable later

        ax_smooth = plt.axes([0.1, 0.06, 0.8, 0.03])
        self.slider_smooth = Slider(ax_smooth, 'Smoothness', 0.1, 30.0, valinit=1.0)

        ax_weight = plt.axes([0.1, 0.02, 0.3, 0.03])
        self.slider_weight = Slider(ax_weight, 'Smoothing Weight', 1, 100, valinit=20)
        # self.slider_weight.on_changed(lambda val: self.event_handler.update_smoothing_weight(val)) # Re-enable later

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
        # Use self.data_manager.nodes instead of .data
        if event.inaxes != self.ax or self.data_manager.nodes.size == 0:
            self.tooltip.set_visible(False)
            if self.nearest_point:
                self.nearest_point.remove()
                self.nearest_point = None
            self.fig.canvas.draw_idle()
            return
        try:
            x, y = event.xdata, event.ydata

            # Compare distances against node x, y (cols 1, 2)
            nodes = self.data_manager.nodes
            distances = np.sqrt((nodes[:, 1] - x) ** 2 + (nodes[:, 2] - y) ** 2)
            closest_idx = np.argmin(distances)  # This is the ROW index

            if distances[closest_idx] < self.D / 100:
                point = nodes[closest_idx]

                # Update tooltip to show new info
                # [point_id, x, y, yaw, original_lane_id]
                self.tooltip.set_text(
                    f'X: {point[1]:.2f}\nY: {point[2]:.2f}\n'
                    f'Lane: {int(point[4])}\nPointID: {int(point[0])}'
                )
                self.tooltip.set_position((point[1], point[2]))

                self.tooltip.set_visible(True)
                if self.nearest_point:
                    self.nearest_point.remove()
                self.nearest_point = self.ax.scatter(point[1], point[2], s=30, color='cyan', marker='o', alpha=0.5)
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

                    # Get lane_id (col 4) from self.nodes
                    lane_id = int(np.unique(self.data_manager.nodes[self.indices[idx], 4])[0])

                    if self.highlighted_lane == lane_id:
                        self.highlighted_lane = None
                    else:
                        self.highlighted_lane = lane_id
                    self.event_handler.update_point_sizes()
                    self.update_status(
                        f"{'Highlighted' if self.highlighted_lane is not None else 'Unhighlighted'} lane {lane_id}")
            except Exception as e:
                print(f"Error during legend pick: {e}")
        self.fig.canvas.draw_idle()

    def setup_legend_handler(self):
        self.ax.legend_ = self.ax.legend()
        for legend_line in self.ax.legend_.get_lines():
            legend_line.set_picker(True)
            legend_line.set_pickradius(5)

    def update_plot(self, nodes, edges, selected_indices=None):
        if selected_indices is None:
            selected_indices = self.selected_indices
        self.selected_indices = selected_indices  # row indices of nodes

        start_time = time.time()
        try:
            # Clear all plot elements
            for plot in self.lane_scatter_plots + self.start_point_plots + self.extra_scatter_plots + self.edge_plots:
                plot.remove()
            if self.event_handler.smoothing_preview_line is not None:
                try:
                    self.event_handler.smoothing_preview_line.remove()
                except ValueError:
                    pass
                self.event_handler.smoothing_preview_line = None

            self.lane_scatter_plots = []
            self.start_point_plots = []
            self.extra_scatter_plots = []
            self.edge_plots = []
            self.indices = []

            if nodes.size == 0:
                self.ax.set_title("No Data")
                self.fig.canvas.draw_idle()
                return

            #  1. PLOT EDGES 
            if edges.size > 0:
                # Create a lookup dictionary for node coordinates by point_id
                # Node: [point_id, x, y, yaw, original_lane_id]
                node_coords = {int(node[0]): (node[1], node[2]) for node in nodes}

                edge_lines = []  # Store (x_pairs, y_pairs) for plotting
                for from_id, to_id in edges:
                    if from_id in node_coords and to_id in node_coords:
                        p1 = node_coords[from_id]
                        p2 = node_coords[to_id]
                        edge_lines.append(([p1[0], p2[0]], [p1[1], p2[1]]))

                for x_pair, y_pair in edge_lines:
                    # Plot all edges as thin black lines
                    line = self.ax.plot(x_pair, y_pair, 'k-', alpha=0.3, zorder=1)[0]
                    self.edge_plots.append(line)

            #  2. PLOT NODES (POINTS) 
            # Node: [point_id, x, y, yaw, original_lane_id]
            unique_lane_ids = np.unique(nodes[:, 4])
            colors = plt.cm.get_cmap('tab10')(np.linspace(0, 1, max(len(unique_lane_ids), 10)))

            for lane_id in unique_lane_ids:
                mask = nodes[:, 4] == lane_id
                lane_nodes = nodes[mask]

                if len(lane_nodes) > 0:
                    label = self.file_names[int(lane_id)] if int(lane_id) < len(self.file_names) else f"Lane {lane_id}"
                    sc = self.ax.scatter(lane_nodes[:, 1], lane_nodes[:, 2], s=10, label=label,
                                         color=colors[int(lane_id)], marker='o', picker=True, zorder=2)
                    self.lane_scatter_plots.append(sc)
                    self.indices.append(np.where(mask)[0])  # Store row indices

            #  3. PLOT START POINTS 
            if edges.size > 0:
                # Find all nodes that are "to" nodes (i.e., have an incoming edge)
                to_ids = set(edges[:, 1])
                # A start node is any node that is not a "to" node
                start_nodes = [node for node in nodes if int(node[0]) not in to_ids]

                for node in start_nodes:
                    lane_id = int(node[4])
                    start_sc = self.ax.scatter(node[1], node[2], s=50, color=colors[lane_id],
                                               marker='s', label=f'Lane {lane_id} Start', zorder=3)
                    self.start_point_plots.append(start_sc)

            #  4. PLOT SELECTED POINTS 
            if self.selected_indices:
                selected_nodes = nodes[np.array(self.selected_indices, dtype=int)]
                sc = self.ax.scatter(selected_nodes[:, 1], selected_nodes[:, 2], s=30, color='red', marker='x',
                                     label='Selected', zorder=4)
                self.extra_scatter_plots.append(sc)

            #  5. PLOT MERGE/SMOOTHING POINTS (from event_handler) 
            if self.event_handler.merge_mode:
                # This logic will need to be updated in event_handler.py
                pass

            #  6. FINALIZE PLOT 
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
