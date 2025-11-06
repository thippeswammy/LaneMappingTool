import time

import matplotlib.pyplot as plt
import numpy as np
from matplotlib.widgets import Button


# Note: CurveManager import is deferred as it's not used in this update
# from DataVisualizationEditingTool.utils.curve_manager import CurveManager
# from DataVisualizationEditingTool.utils.data_loader import DataLoader # No longer needed here


class EventHandler:
    def __init__(self, data_manager):
        self.data_manager = data_manager
        self.plot_manager = None
        self.curve_manager = None  # Will be set in set_plot_manager
        self.selection_mode = True
        self.draw_mode = False
        self.selected_id = 0  # Default original_lane_id
        self.id_set = True

        # --- Smoothing (Deferred) ---
        self.smoothing_point_selection = False
        self.smoothing_start_idx = None  # This will become start_point_id
        self.smoothing_end_idx = None  # This will become end_point_id
        self.smoothing_selected_indices = None  # This will become selected_row_indices
        self.smoothing_lane_id = None
        self.smoothing_preview_line = None

        # --- Connect Nodes (Replaces Merge) ---
        self.merge_mode = False  # We'll reuse 'merge_mode' for "Connect Nodes"
        self.merge_point_1_id = None
        self.merge_point_2_id = None

        # --- Remove Above/Below (Deferred) ---
        self.remove_above_mode = False
        self.remove_below_mode = False
        self.remove_point_idx = None
        self.remove_lane_id = None

        self.buttons = {}
        self.status_timeout = 5  # seconds
        self.last_status_time = 0

    def set_plot_manager(self, plot_manager):
        self.plot_manager = plot_manager
        # self.curve_manager = CurveManager(self.data_manager, self.plot_manager) # Defer
        self.fig = self.plot_manager.fig
        self.setup_event_handlers()
        self.setup_buttons()
        self.update_button_states()

    def setup_event_handlers(self):
        self.fig.canvas.mpl_connect('button_press_event', self.on_click)
        self.fig.canvas.mpl_connect('key_press_event', self.on_key)
        self.fig.canvas.mpl_connect('pick_event', self.on_pick)
        self.plot_manager.rs.onselect = self.on_select

    def setup_buttons(self):
        ax_toggle = plt.axes([0.01, 0.95, 0.1, 0.04])
        self.buttons['toggle'] = Button(ax_toggle, 'Select Mode')
        self.buttons['toggle'].on_clicked(self.on_toggle_mode)

        ax_draw = plt.axes([0.01, 0.90, 0.1, 0.04])
        self.buttons['draw'] = Button(ax_draw, 'Draw')
        self.buttons['draw'].on_clicked(self.on_toggle_draw_mode)

        ax_linecurve = plt.axes([0.01, 0.85, 0.1, 0.04])
        self.buttons['linecurve'] = Button(ax_linecurve, 'Line')
        self.buttons['linecurve'].on_clicked(self.on_toggle_linecurve)

        ax_straighten = plt.axes([0.01, 0.80, 0.1, 0.04])
        self.buttons['straighten'] = Button(ax_straighten, 'Smooth')
        self.buttons['straighten'].on_clicked(self.on_straighten)

        ax_confirm_start = plt.axes([0.01, 0.75, 0.1, 0.04])
        self.buttons['confirm_start'] = Button(ax_confirm_start, 'Confirm Start')
        self.buttons['confirm_start'].on_clicked(self.on_confirm_start)

        ax_confirm_end = plt.axes([0.01, 0.70, 0.1, 0.04])
        self.buttons['confirm_end'] = Button(ax_confirm_end, 'Confirm End')
        self.buttons['confirm_end'].on_clicked(self.on_confirm_end)

        ax_cancel = plt.axes([0.01, 0.65, 0.1, 0.04])
        self.buttons['cancel'] = Button(ax_cancel, 'Cancel Operation')
        self.buttons['cancel'].on_clicked(self.on_cancel_operation)

        ax_clear = plt.axes([0.01, 0.60, 0.1, 0.04])
        self.buttons['clear'] = Button(ax_clear, 'Clear Selection')
        self.buttons['clear'].on_clicked(self.on_clear_selection)

        ax_save = plt.axes([0.01, 0.55, 0.1, 0.04])
        self.buttons['save'] = Button(ax_save, 'Save')
        self.buttons['save'].on_clicked(self.save_data)

        # --- RENAMED ---
        ax_merge = plt.axes([0.01, 0.50, 0.1, 0.04])
        self.buttons['merge'] = Button(ax_merge, 'Connect Nodes')  # Was 'Merge Lanes'
        self.buttons['merge'].on_clicked(self.on_connect_nodes)  # Was 'merge_lanes'
        # --- END RENAMED ---

        ax_export = plt.axes([0.01, 0.45, 0.1, 0.04])
        self.buttons['export'] = Button(ax_export, 'Export Selected')
        self.buttons['export'].on_clicked(self.export_selected)

        ax_grid = plt.axes([0.01, 0.40, 0.1, 0.04])
        self.buttons['grid'] = Button(ax_grid, 'Toggle Grid')
        self.buttons['grid'].on_clicked(self.toggle_grid)

        ax_remove_above = plt.axes([0.01, 0.35, 0.1, 0.04])
        self.buttons['remove_above'] = Button(ax_remove_above, 'Remove Above')
        self.buttons['remove_above'].on_clicked(self.on_remove_above)

        ax_remove_below = plt.axes([0.01, 0.30, 0.1, 0.04])
        self.buttons['remove_below'] = Button(ax_remove_below, 'Remove Below')
        self.buttons['remove_below'].on_clicked(self.on_remove_below)

        self.fig.canvas.draw()

    def update_button_states(self):
        # Defer draw logic
        self.buttons['linecurve'].eventson = False  # self.draw_mode
        self.buttons['linecurve'].ax.set_facecolor('lightgray')  # 'white' if self.draw_mode else 'lightgray'
        self.buttons['linecurve'].label.set_color('gray')  # 'black' if self.draw_mode else 'gray'

        # Defer smoothing logic
        self.buttons['straighten'].eventson = False  # self.selection_mode
        self.buttons['straighten'].ax.set_facecolor('lightgray')  # 'white' if self.selection_mode else 'lightgray'
        self.buttons['straighten'].label.set_color('gray')  # 'black' if self.selection_mode else 'gray'
        self.buttons['confirm_start'].eventson = False  # self.smoothing_point_selection
        self.buttons['confirm_start'].ax.set_facecolor(
            'lightgray')  # 'white' if self.smoothing_point_selection else 'lightgray'
        self.buttons['confirm_start'].label.set_color('gray')  # 'black' if self.smoothing_point_selection else 'gray'
        self.buttons['confirm_end'].eventson = False  # self.smoothing_point_selection
        self.buttons['confirm_end'].ax.set_facecolor(
            'lightgray')  # 'white' if self.smoothing_point_selection else 'lightgray'
        self.buttons['confirm_end'].label.set_color('gray')  # 'black' if self.smoothing_point_selection else 'gray'

        # Update Cancel button
        self.buttons['cancel'].eventson = any([self.smoothing_point_selection, self.merge_mode, self.draw_mode,
                                               self.remove_above_mode, self.remove_below_mode])
        self.buttons['cancel'].ax.set_facecolor('white' if self.buttons['cancel'].eventson else 'lightgray')
        self.buttons['cancel'].label.set_color('black' if self.buttons['cancel'].eventson else 'gray')

        # Update Export button
        self.buttons['export'].eventson = bool(self.plot_manager.selected_indices)
        self.buttons['export'].ax.set_facecolor('white' if self.plot_manager.selected_indices else 'lightgray')
        self.buttons['export'].label.set_color('black' if self.plot_manager.selected_indices else 'gray')

        # Defer Remove Above/Below
        self.buttons['remove_above'].eventson = False  # not (...)
        self.buttons['remove_above'].ax.set_facecolor('lightgray')
        self.buttons['remove_above'].label.set_color('gray')
        self.buttons['remove_below'].eventson = False  # not (...)
        self.buttons['remove_below'].ax.set_facecolor('lightgray')
        self.buttons['remove_below'].label.set_color('gray')

        self.fig.canvas.draw_idle()

    def update_smoothing_weight(self, val):
        # Defer
        print("Smoothing disabled for now.")
        pass

    def toggle_grid(self, event):
        self.plot_manager.grid_visible = not self.plot_manager.grid_visible
        self.plot_manager.ax.grid(self.plot_manager.grid_visible)
        self.update_status(f"Grid {'enabled' if self.plot_manager.grid_visible else 'disabled'}")
        self.fig.canvas.draw()

    def on_toggle_mode(self, event):
        self.draw_mode = False
        self.selection_mode = not self.selection_mode
        self.plot_manager.rs.set_active(self.selection_mode)
        self.buttons['toggle'].label.set_text('Select Mode' if self.selection_mode else 'Add/Delete Mode')
        self.buttons['toggle'].color = 'lightcoral' if self.selection_mode else 'lightgreen'
        if not self.selection_mode:
            self.id_set = True
            self.clear_smoothing_state()
            self.clear_remove_state()
            if self.plot_manager.selected_indices:
                self.plot_manager.selected_indices = []
                self.update_point_sizes()
                print("Cleared selection")
        print(f"Entered {'selection' if self.selection_mode else 'add/delete'} mode")
        self.update_button_states()
        self.update_status()

    def on_toggle_draw_mode(self, event):
        # Defer
        self.update_status("Draw mode is disabled for now.")
        print("Draw mode is disabled for now.")
        # self.selection_mode = False
        # self.draw_mode = not self.draw_mode
        # ... (rest of logic)

    def on_toggle_linecurve(self, event):
        # Defer
        self.update_status("Draw mode is disabled for now.")
        pass

    def on_straighten(self, event):
        # Defer
        self.update_status("Smoothing is disabled for now.")
        print("Smoothing is disabled for now.")
        pass

    def on_confirm_start(self, event):
        # Defer
        self.update_status("Smoothing is disabled for now.")
        pass

    def on_confirm_end(self, event):
        # Defer
        self.update_status("Smoothing is disabled for now.")
        pass

    def on_remove_above(self, event):
        # Defer
        self.update_status("Remove Above is disabled for now.")
        print("Remove Above is disabled for now.")
        pass

    def on_remove_below(self, event):
        # Defer
        self.update_status("Remove Below is disabled for now.")
        print("Remove Below is disabled for now.")
        pass

    def on_cancel_operation(self, event):
        print("Operation canceled")
        self.clear_smoothing_state()
        self.clear_merge_state()
        self.clear_remove_state()
        self.draw_mode = False
        self.selection_mode = False  # Default to add/delete
        self.plot_manager.rs.set_active(False)
        # if self.curve_manager: # Defer
        #     self.curve_manager.draw_points = []
        #     if self.curve_manager.current_line:
        #         self.curve_manager.current_line.remove()
        #         self.curve_manager.current_line = None
        #         self.plot_manager.fig.canvas.draw_idle()
        self.update_point_sizes()
        self.update_button_states()
        self.update_status("Operation canceled")

    def on_clear_selection(self, event):
        if self.plot_manager.selected_indices:
            self.plot_manager.selected_indices = []
            print("Cleared selection")
        self.clear_smoothing_state()
        self.clear_merge_state()
        self.clear_remove_state()
        self.update_point_sizes()
        self.update_button_states()
        self.update_status("Selection cleared")

    def clear_smoothing_state(self):
        self.smoothing_point_selection = False
        self.smoothing_start_idx = None
        self.smoothing_end_idx = None
        self.smoothing_selected_indices = None
        self.smoothing_lane_id = None
        if self.smoothing_preview_line:
            self.smoothing_preview_line.remove()
            self.smoothing_preview_line = None
            self.plot_manager.fig.canvas.draw_idle()

    def clear_merge_state(self):
        """Resets the state for 'Connect Nodes' mode."""
        self.merge_mode = False
        self.merge_point_1_id = None
        self.merge_point_2_id = None
        self.update_status()

    def clear_remove_state(self):
        self.remove_above_mode = False
        self.remove_below_mode = False
        self.remove_point_idx = None
        self.remove_lane_id = None

    def on_connect_nodes(self, event):
        """Handler for the 'Connect Nodes' button."""
        if self.data_manager.nodes.size == 0:
            self.update_status("No nodes to connect")
            return

        self.merge_mode = True  # Use merge_mode to track "Connect Nodes" state
        self.merge_point_1_id = None
        self.merge_point_2_id = None
        print("Please select first node to connect")
        self.update_status("Select first node")
        self.update_point_sizes()
        self.update_button_states()

    def finalize_connection(self):
        """Creates the edge between the two selected nodes."""
        if self.merge_point_1_id is None or self.merge_point_2_id is None:
            print("Two nodes must be selected to create a connection")
            self.update_status("Select two nodes")
            self.clear_merge_state()
            return

        # Call the new DataManager function
        self.data_manager.add_edge(self.merge_point_1_id, self.merge_point_2_id)

        # Redraw the plot with the new edge
        self.plot_manager.update_plot(self.data_manager.nodes, self.data_manager.edges)

        print(f"Connected node {self.merge_point_1_id} to {self.merge_point_2_id}")
        self.update_status(f"Connected {self.merge_point_1_id} -> {self.merge_point_2_id}")

        # Reset state
        self.clear_merge_state()
        self.update_point_sizes()
        self.update_button_states()

    def save_data(self, event):
        filename = self.data_manager.save()
        if filename:
            print(f"Saved to {filename}")
            self.update_status(f"Saved to {filename}")
        else:
            self.update_status("Save failed")

    def export_selected(self, event):
        if not self.plot_manager.selected_indices:
            print("No points selected to export")
            self.update_status("Select points to export")
            return
        try:
            # selected_indices contains ROW indices of the nodes array
            selected_nodes = self.data_manager.nodes[np.array(self.plot_manager.selected_indices, dtype=int)]

            filename = f"selected_points_{int(time.time())}.npy"

            # Save [x, y, yaw] (cols 1, 2, 3)
            np.save(filename, selected_nodes[:, 1:4])

            print(f"Exported {len(selected_nodes)} points to {filename}")
            self.update_status(f"Exported {len(selected_nodes)} points")
        except Exception as e:
            print(f"Error exporting points: {e}")
            self.update_status("Export failed")

    def on_click(self, event):
        if self.plot_manager is None or event.inaxes != self.plot_manager.ax or event.button != 1:
            return

        if self.data_manager.nodes.size == 0:
            # If no nodes, just add a new one (if in add mode)
            if not self.selection_mode:
                new_id = self.data_manager.add_node(event.xdata, event.ydata, self.selected_id)
                self.plot_manager.update_plot(self.data_manager.nodes, self.data_manager.edges)
                print(f"Added first node {new_id} with ID {self.selected_id}")
                self.update_status("Added first node")
            return

        click_x, click_y = event.xdata, event.ydata

        # Find closest node
        # nodes[:, 1] is x, nodes[:, 2] is y
        nodes = self.data_manager.nodes
        distances = np.sqrt((nodes[:, 1] - click_x) ** 2 + (nodes[:, 2] - click_y) ** 2)
        closest_row_idx = np.argmin(distances)

        # Get the persistent point_id and original_lane_id
        closest_point_id = int(nodes[closest_row_idx, 0])
        original_lane_id = int(nodes[closest_row_idx, 4])

        if self.remove_above_mode:
            # Defer
            self.update_status("Remove Above disabled")
            return

        if self.remove_below_mode:
            # Defer
            self.update_status("Remove Below disabled")
            return

        if self.merge_mode:  # "Connect Nodes" mode
            if self.merge_point_1_id is None:
                self.merge_point_1_id = closest_point_id
                print(f"Selected first node (ID {closest_point_id})")
                self.update_status(f"Node 1: {closest_point_id}. Select second node.")
                self.update_point_sizes()
                self.plot_manager.fig.canvas.draw_idle()
            elif self.merge_point_2_id is None and closest_point_id != self.merge_point_1_id:
                self.merge_point_2_id = closest_point_id
                print(f"Selected second node (ID {closest_point_id})")
                self.finalize_connection()
            return

        if self.smoothing_point_selection:
            # Defer
            self.update_status("Smoothing disabled")
            return

        if self.draw_mode:
            # Defer
            self.update_status("Draw disabled")
            return

        if self.selection_mode:
            # In select mode, a click just selects the nearest point
            self.plot_manager.selected_indices = [closest_row_idx]
            self.update_point_sizes()
            self.update_status(f"Selected node {closest_point_id}")
            return

        # --- If we get here, we are in "Add/Delete Mode" ---

        # Add a new node
        new_point_id = self.data_manager.add_node(event.xdata, event.ydata, self.selected_id)

        # Automatically add an edge from the closest node to the new node
        self.data_manager.add_edge(closest_point_id, new_point_id)

        # Redraw
        self.plot_manager.update_plot(self.data_manager.nodes, self.data_manager.edges)
        print(f"Added node {new_point_id} (Lane {self.selected_id}), connected from {closest_point_id}")
        self.update_status(f"Added node {new_point_id}, linked from {closest_point_id}")

    def update_point_sizes(self):
        if self.plot_manager is None:
            print("Plot manager not set, skipping update_point_sizes")
            return
        try:
            nodes = self.data_manager.nodes
            if nodes.size == 0:
                return

            for plot_idx, sc in enumerate(self.plot_manager.lane_scatter_plots):
                # 'indices' contains the ROW indices for this scatter plot
                row_indices = self.plot_manager.indices[plot_idx]
                if len(row_indices) == 0:
                    continue

                # Get the lane_id (col 4) from the first node in this group
                lane_id = int(nodes[row_indices[0], 4])

                base_size = 20 if self.plot_manager.highlighted_lane == lane_id else 10
                sizes = np.full(len(row_indices), base_size, dtype=float)

                # Get all point_ids for this scatter plot
                point_ids_in_plot = nodes[row_indices, 0]

                # Create a map of {point_id -> local_idx_in_sizes_array}
                id_to_local_idx = {int(pid): i for i, pid in enumerate(point_ids_in_plot)}

                if self.merge_mode:
                    if self.merge_point_1_id in id_to_local_idx:
                        sizes[id_to_local_idx[self.merge_point_1_id]] = 100
                    if self.merge_point_2_id in id_to_local_idx:
                        sizes[id_to_local_idx[self.merge_point_2_id]] = 80

                # Note: Smoothing/Remove logic is deferred

                # Highlight selected points
                # Create a set of selected row indices for fast lookup
                selected_row_set = set(self.plot_manager.selected_indices)
                for local_idx, global_row_idx in enumerate(row_indices):
                    if global_row_idx in selected_row_set:
                        sizes[local_idx] = 30

                sc.set_sizes(sizes)

            self.plot_manager.fig.canvas.draw_idle()
            self.plot_manager.fig.canvas.flush_events()
            self.update_button_states()
        except Exception as e:
            print(f"Error updating point sizes: {e}")

    def on_pick(self, event):
        """Handler for right-click delete."""
        if self.plot_manager is None or event.mouseevent.button != 3 or self.plot_manager.rs.active:
            return

        artist = event.artist
        if artist not in self.plot_manager.lane_scatter_plots:
            return

        # ind[0] is the local index *within the scatter plot data*
        local_ind = event.ind[0]

        # file_index maps to the correct lane scatter plot
        file_index = self.plot_manager.lane_scatter_plots.index(artist)

        # global_row_ind is the ROW index in self.data_manager.nodes
        global_row_ind = self.plot_manager.indices[file_index][local_ind]

        # Get the persistent point_id to delete
        point_id_to_delete = int(self.data_manager.nodes[global_row_ind, 0])

        # Call DataManager to delete this node and all connected edges
        self.data_manager.delete_points([point_id_to_delete])

        # Remove the deleted row index from the selection
        self.plot_manager.selected_indices = [i for i in self.plot_manager.selected_indices if i != global_row_ind]

        # Redraw the plot
        self.plot_manager.update_plot(self.data_manager.nodes, self.data_manager.edges)
        self.update_status(f"Deleted node {point_id_to_delete}")

    def on_select(self, eclick, erelease):
        """Handler for rectangle selection."""
        if not self.selection_mode:
            return
        try:
            x1, y1 = eclick.xdata, eclick.ydata
            x2, y2 = erelease.xdata, erelease.ydata
            x_min, x_max = min(x1, x2), max(x1, x2)
            y_min, y_max = min(y1, y2), max(y1, y2)

            nodes = self.data_manager.nodes

            # Find all nodes within the box
            # nodes[:, 1] is x, nodes[:, 2] is y
            x_mask = (nodes[:, 1] >= x_min) & (nodes[:, 1] <= x_max)
            y_mask = (nodes[:, 2] >= y_min) & (nodes[:, 2] <= y_max)
            combined_mask = x_mask & y_mask

            # Get the ROW indices of the selected nodes
            self.plot_manager.selected_indices = np.where(combined_mask)[0].tolist()

            print(f"Selected {len(self.plot_manager.selected_indices)} nodes")
            self.update_point_sizes()
            self.update_status(f"Selected {len(self.plot_manager.selected_indices)} nodes")
        except Exception as e:
            print(f"Error during selection: {e}")

    def on_key(self, event):
        key = event.key.lower()
        if key == 'ctrl+z':
            self.on_undo(event)
        elif key in ('ctrl+shift+z', 'ctrl+y'):
            self.on_redo(event)
        elif key == 'tab':
            self.on_toggle_mode(event)
        elif key == 'd':
            self.on_toggle_draw_mode(event)
        elif key == 'escape':
            self.on_escape(event)
        elif key == 'delete':
            self.on_delete(event)
        elif key == 'enter':
            self.on_finalize_draw(event)
        elif key in '0123456789':
            # Use number keys to select the 'original_lane_id' for new points
            new_id = int(key)
            if new_id < len(self.data_manager.file_names):
                self.selected_id = new_id
                print(f"Set new point lane ID to {new_id} ({self.data_manager.file_names[new_id]})")
                self.update_status(f"New point ID set to {new_id}")
            else:
                self.update_status(f"Invalid lane ID {new_id}")

    def on_escape(self, event):
        if self.plot_manager is None:
            return
        self.selection_mode = False
        self.draw_mode = False
        self.id_set = True
        self.clear_smoothing_state()
        self.clear_merge_state()
        self.clear_remove_state()
        self.plot_manager.rs.set_active(False)
        # Defer curve manager
        # if self.curve_manager:
        #     self.curve_manager.draw_points = []
        #     ...
        if self.plot_manager.selected_indices:
            self.plot_manager.selected_indices = []
            self.update_point_sizes()
            print("Cleared selection")
        print("Entered add/delete mode")
        self.update_button_states()
        self.update_status("Entered add/delete mode")

    def on_delete(self, event):
        """Handler for 'Delete' key to delete selected nodes."""
        if self.plot_manager is None or not self.selection_mode or not self.plot_manager.selected_indices:
            return

        # selected_indices contains the ROW indices
        row_indices = self.plot_manager.selected_indices

        # Get the persistent point_ids from the row indices
        # nodes[:, 0] is point_id
        point_ids_to_delete = self.data_manager.nodes[row_indices, 0].astype(int)

        self.data_manager.delete_points(point_ids_to_delete)

        self.plot_manager.selected_indices = []
        self.plot_manager.update_plot(self.data_manager.nodes, self.data_manager.edges)
        print(f"Deleted {len(point_ids_to_delete)} nodes")
        self.update_status(f"Deleted {len(point_ids_to_delete)} nodes")

    def on_undo(self, event):
        if self.plot_manager is None:
            return

        # Undo now returns (nodes, edges, success)
        nodes, edges, success = self.data_manager.undo()

        if success:
            self.plot_manager.selected_indices = []
            self.plot_manager.update_plot(nodes, edges)
            print("Undo performed")
            self.update_status("Undo performed")
        else:
            self.update_status("Nothing to undo")

    def on_redo(self, event):
        if self.plot_manager is None:
            return

        # Redo now returns (nodes, edges, success)
        nodes, edges, success = self.data_manager.redo()

        if success:
            self.plot_manager.selected_indices = []
            self.plot_manager.update_plot(nodes, edges)
            print("Redo performed")
            self.update_status("Redo performed")
        else:
            self.update_status("Nothing to redo")

    def on_finalize_draw(self, event):
        # Defer
        self.update_status("Draw mode disabled")
        pass

    def update_status(self, message=""):
        try:
            self.plot_manager.update_status(message)
            self.last_status_time = time.time()

            if message:
                def clear_status():
                    if time.time() - self.last_status_time >= self.status_timeout:
                        self.plot_manager.update_status("")
                        self.fig.canvas.draw_idle()

                timer = self.fig.canvas.new_timer(interval=int(self.status_timeout * 1000))
                timer.add_callback(clear_status)
                timer.start()

        except Exception as e:
            print(f"Error updating status: {e}")