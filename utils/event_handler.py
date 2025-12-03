import time

import matplotlib.pyplot as plt
import numpy as np
from matplotlib.widgets import Button

from utils.curve_manager import CurveManager


class EventHandler:
    def __init__(self, data_manager):
        self.data_manager = data_manager
        self.plot_manager = None
        self.curve_manager = None
        self.draw_mode = False
        self.selected_id = 0
        self.id_set = True

        # press state 
        self.ctrl_pressed = False
        self.s_pressed = False

        # Smoothing state
        self.smoothing_point_selection = False
        self.smoothing_start_id = None
        self.smoothing_end_id = None
        self.smoothing_path_ids = []
        self.smoothing_preview_line = None

        # Connect Nodes state
        self.merge_mode = False
        self.merge_point_1_id = None
        self.merge_point_2_id = None

        # Remove state (Deferred)
        self.remove_above_mode = False
        self.remove_below_mode = False
        self.remove_point_idx = None
        self.remove_lane_id = None
        self.merge_point_1_id = None
        self.merge_point_2_id = None

        #  Remove Between state 
        self.remove_between_mode = False
        self.remove_start_id = None
        self.remove_end_id = None

        #  Reverse Path state
        self.reverse_path_mode = False
        self.reverse_start_id = None
        self.reverse_end_id = None

        self.buttons = {}
        self.status_timeout = 5
        self.last_status_time = 0

    def set_plot_manager(self, plot_manager):
        self.plot_manager = plot_manager
        try:
            self.curve_manager = CurveManager(self.data_manager, self.plot_manager, self)
        except Exception as e:
            print(f"Error initializing CurveManager: {e}. Draw/Smooth will fail.")
            self.curve_manager = None

        self.fig = self.plot_manager.fig

        if self.plot_manager.slider_smooth:
            self.plot_manager.slider_smooth.on_changed(self.on_slider_update)
        if self.plot_manager.slider_weight:
            self.plot_manager.slider_weight.on_changed(self.on_slider_update)

        self.setup_event_handlers()
        self.setup_buttons()
        self.update_button_states()

    def setup_event_handlers(self):
        self.fig.canvas.mpl_connect('button_press_event', self.on_click)
        self.fig.canvas.mpl_connect('key_press_event', self.on_key)
        self.fig.canvas.mpl_connect('key_release_event', self.on_key_release)
        self.fig.canvas.mpl_connect('pick_event', self.on_pick)
        self.plot_manager.rs.onselect = self.on_select

    def setup_buttons(self):
        # Button layout
        """Sets up the buttons for the user interface."""
        ax_draw = plt.axes([0.01, 0.90, 0.1, 0.04])
        self.buttons['draw'] = Button(ax_draw, 'Draw')
        self.buttons['draw'].on_clicked(self.on_toggle_draw_mode)

        ax_linecurve = plt.axes([0.01, 0.85, 0.1, 0.04])
        self.buttons['linecurve'] = Button(ax_linecurve, 'Line')
        self.buttons['linecurve'].on_clicked(self.on_toggle_linecurve)

        ax_straighten = plt.axes([0.01, 0.80, 0.1, 0.04])
        self.buttons['straighten'] = Button(ax_straighten, 'Smooth')
        self.buttons['straighten'].on_clicked(self.on_straighten)

        # These buttons are hidden but kept for layout
        ax_confirm_start = plt.axes([0.01, 0.75, 0.1, 0.04])
        self.buttons['confirm_start'] = Button(ax_confirm_start, 'Confirm Start')
        self.buttons['confirm_start'].ax.set_visible(False)

        ax_confirm_end = plt.axes([0.01, 0.70, 0.1, 0.04])
        self.buttons['confirm_end'] = Button(ax_confirm_end, 'Confirm End')
        self.buttons['confirm_end'].ax.set_visible(False)

        ax_cancel = plt.axes([0.01, 0.65, 0.1, 0.04])
        self.buttons['cancel'] = Button(ax_cancel, 'Cancel Operation')
        self.buttons['cancel'].on_clicked(self.on_cancel_operation)

        ax_clear = plt.axes([0.01, 0.60, 0.1, 0.04])
        self.buttons['clear'] = Button(ax_clear, 'Clear Selection')
        self.buttons['clear'].on_clicked(self.on_clear_selection)

        ax_save = plt.axes([0.01, 0.55, 0.1, 0.04])
        self.buttons['save'] = Button(ax_save, 'Save')
        self.buttons['save'].on_clicked(self.save_data)

        ax_merge = plt.axes([0.01, 0.50, 0.1, 0.04])
        self.buttons['merge'] = Button(ax_merge, 'Connect Nodes')
        self.buttons['merge'].on_clicked(self.on_connect_nodes)

        ax_export = plt.axes([0.01, 0.45, 0.1, 0.04])
        self.buttons['export'] = Button(ax_export, 'Export Selected')
        self.buttons['export'].on_clicked(self.export_selected)

        ax_grid = plt.axes([0.01, 0.40, 0.1, 0.04])
        self.buttons['grid'] = Button(ax_grid, 'Toggle Grid')
        self.buttons['grid'].on_clicked(self.toggle_grid)

        ax_remove_between = plt.axes([0.01, 0.35, 0.1, 0.04])
        self.buttons['remove_between'] = Button(ax_remove_between, 'Remove Between')
        self.buttons['remove_between'].on_clicked(self.on_remove_between)

        ax_remove_below = plt.axes([0.01, 0.30, 0.1, 0.04])
        self.buttons['remove_below'] = Button(ax_remove_below, 'Remove Below')
        self.buttons['remove_below'].on_clicked(self.on_remove_below)
        self.buttons['remove_below'].ax.set_visible(False)

        ax_reverse_path = plt.axes([0.01, 0.30, 0.1, 0.04])
        self.buttons['reverse_path'] = Button(ax_reverse_path, 'Reverse Path')
        self.buttons['reverse_path'].on_clicked(self.on_reverse_path)
        self.buttons['reverse_path'].ax.set_visible(True)

        self.fig.canvas.draw()

    def update_button_states(self):
        # Draw Buttons
        """Update the states of various buttons based on the current modes.
        
        This function manages the enabled states and visual appearances of buttons in
        the user interface. It checks the current drawing and smoothing modes, updating
        the 'draw', 'linecurve', 'cancel', 'straighten', 'export', 'remove_between',
        and 'reverse_path' buttons accordingly. The function also adjusts button labels
        and colors based on the active modes and selections, ensuring that the
        interface reflects the current operational context.
        
        Args:
            self: The instance of the class containing the button states and modes.
        """
        self.buttons['draw'].eventson = True
        self.buttons['linecurve'].eventson = self.draw_mode
        self.buttons['linecurve'].ax.set_facecolor('white' if self.draw_mode else 'lightgray')
        self.buttons['linecurve'].label.set_color('black' if self.draw_mode else 'gray')

        # Added reverse_path_mode to "Cancel" logi
        is_in_operation = self.draw_mode or self.smoothing_point_selection or self.merge_mode or self.remove_between_mode or self.reverse_path_mode
        self.buttons['cancel'].eventson = is_in_operation

        # Smoothing Buttons
        self.buttons['straighten'].eventson = True
        is_previewing = self.smoothing_point_selection and self.smoothing_preview_line is not None
        if is_previewing:
            self.buttons['straighten'].label.set_text('Confirm Smooth')
            self.buttons['straighten'].ax.set_facecolor('lightgreen')
        else:
            self.buttons['straighten'].label.set_text('Smooth')
            self.buttons['straighten'].ax.set_facecolor('white')

            # Cancel Button
            is_in_operation = self.draw_mode or self.smoothing_point_selection or self.merge_mode or self.remove_between_mode
            self.buttons['cancel'].eventson = is_in_operation
            self.buttons['cancel'].ax.set_facecolor('white' if is_in_operation else 'lightgray')
            self.buttons['cancel'].label.set_color('black' if is_in_operation else 'gray')

        # Export Button
        self.buttons['export'].eventson = bool(self.plot_manager.selected_indices)
        self.buttons['export'].ax.set_facecolor('white' if self.plot_manager.selected_indices else 'lightgray')
        self.buttons['export'].label.set_color('black' if self.plot_manager.selected_indices else 'gray')

        # Remove Between
        self.buttons['remove_between'].eventson = True
        self.buttons['remove_between'].ax.set_facecolor('white')
        self.buttons['remove_between'].label.set_color('black')

        # reverse_path
        self.buttons['reverse_path'].eventson = True
        self.buttons['reverse_path'].ax.set_facecolor('white')
        self.buttons['reverse_path'].label.set_color('black')

        # Remove Buttons (Deferred)
        # self.buttons['remove_above'].eventson = False
        # self.buttons['remove_above'].ax.set_facecolor('lightgray')
        # self.buttons['remove_above'].label.set_color('gray')

        # self.buttons['remove_below'].eventson = False
        # self.buttons['remove_below'].ax.set_facecolor('lightgray')
        # self.buttons['remove_below'].label.set_color('gray')

        self.fig.canvas.draw_idle()

    def on_slider_update(self, val):
        if self.smoothing_point_selection and self.smoothing_start_id is not None and self.smoothing_end_id is not None:
            if self.curve_manager:
                self.curve_manager.smoothing_weight = self.plot_manager.slider_weight.val
                print(
                    f"Slider update: weight={self.curve_manager.smoothing_weight}, smoothness={self.plot_manager.slider_smooth.val}")
                self.curve_manager.preview_smooth(self.smoothing_start_id, self.smoothing_end_id)
                self.update_status("Preview updated. Click 'Confirm Smooth' to apply.")

    def update_smoothing_weight(self, val):
        # Defer
        print("Smoothing disabled for now.")
        pass

    def toggle_grid(self, event):
        self.plot_manager.grid_visible = not self.plot_manager.grid_visible
        self.plot_manager.ax.grid(self.plot_manager.grid_visible)
        self.update_status(f"Grid {'enabled' if self.plot_manager.grid_visible else 'disabled'}")
        self.fig.canvas.draw()

    def on_toggle_draw_mode(self, event):
        was_already_draw = self.draw_mode
        self.clear_operation_modes(back_to_select=False)

        if not was_already_draw:
            self.draw_mode = True
            self.update_status("Draw Mode: Click to add points, 'Enter' to finalize.")

        print(f"Entered {'draw' if self.draw_mode else 'navigation'} mode")
        self.update_button_states()

    def on_remove_between(self, event):
        self.clear_operation_modes(back_to_select=False)
        self.remove_between_mode = True
        print("Entered Remove Between mode.")
        self.update_status("Remove Between: Click to select START node.")
        self.update_button_states()

    def clear_operation_modes(self, back_to_select=True):
        """Clear various operation modes and reset selections.
        
        This method resets the states of smoothing, merging, removing, and reversing
        paths.  It also clears the drawing mode and manages the selection indices based
        on the  current mode. If not in smoothing mode, it clears the selected indices
        and updates  the point sizes. The selection mode is set based on the
        back_to_select parameter,  which determines whether to activate or deactivate
        the selection mode.
        
        Args:
            back_to_select (bool): Indicates whether to return to selection mode.
        """
        self.clear_smoothing_state()
        self.clear_merge_state()
        self.clear_remove_state()
        self.clear_reverse_path_state()
        self.draw_mode = False
        if self.curve_manager:
            self.curve_manager.clear_draw()

        # Clear selection unless we are in smoothing mode
        if not self.smoothing_point_selection and self.plot_manager.selected_indices:
            self.plot_manager.selected_indices = []
            self.update_point_sizes()

        self.selection_mode = back_to_select
        if not back_to_select:
            self.plot_manager.rs.set_active(False)

    #  New button handler
    def on_reverse_path(self, event):
        """Enters reverse path mode and updates the UI accordingly."""
        self.clear_operation_modes(back_to_select=False)
        self.reverse_path_mode = True
        print("Entered Reverse Path mode.")
        self.update_status("Reverse Path: Click to select START node.")
        self.update_button_states()

    def on_toggle_linecurve(self, event):
        """Toggle the drawing mode between line and curve."""
        if not self.draw_mode or not self.curve_manager:
            self.update_status("Enter Draw Mode first")
            return
        self.curve_manager.is_curve = not self.curve_manager.is_curve
        self.buttons['linecurve'].label.set_text('Curve' if self.curve_manager.is_curve else 'Line')
        self.curve_manager.update_draw_line()
        print(f"Drawing {'curve' if self.curve_manager.is_curve else 'line'}")
        self.update_status()

    def on_straighten(self, event):
        """Handles the straightening operation based on the current state."""
        if not self.curve_manager:
            self.update_status("Error: CurveManager not available.")
            return

        if self.smoothing_point_selection and self.smoothing_preview_line is not None:
            print("Confirming smooth...")
            self.curve_manager.apply_smooth()
            self.clear_operation_modes(back_to_select=False)
            self.update_status("Path smoothed.")
        else:
            self.clear_operation_modes(back_to_select=False)
            self.smoothing_point_selection = True
            print("Entered smoothing mode.")
            self.update_status("Smooth Mode: Click to select START node.")

        self.update_button_states()

    def on_confirm_start(self, event):
        # Defer
        self.update_status("Smoothing is disabled for now.")
        pass

    def on_confirm_end(self, event):
        # Defer
        self.update_status("Smoothing is disabled for now.")
        pass

    def on_remove_above(self, event):
        self.update_status("Remove Above is disabled for now.")
        print("Remove Above is disabled for now.")

    def on_remove_below(self, event):
        """Handles the removal of items below a certain threshold."""
        self.update_status("Remove Below is disabled for now.")
        self.on_reverse_path(event)
        print("Remove Below is disabled for now.")

    def on_cancel_operation(self, event):
        print("Operation canceled")
        self.clear_operation_modes(back_to_select=True)
        self.update_button_states()
        self.update_status("Operation canceled")

    def on_clear_selection(self, event):
        print("Cleared selection")
        self.clear_operation_modes(back_to_select=True)
        self.update_button_states()
        self.update_status("Selection cleared")

    def clear_smoothing_state(self):
        self.smoothing_point_selection = False
        self.smoothing_start_id = None
        self.smoothing_end_id = None
        self.smoothing_path_ids = []
        if self.smoothing_preview_line:
            try:
                self.smoothing_preview_line.remove()
            except ValueError:
                pass
            self.smoothing_preview_line = None
        if self.plot_manager:  # Redraw if plot manager
            self.plot_manager.fig.canvas.draw_idle()

    def clear_merge_state(self):
        self.merge_mode = False
        self.merge_point_1_id = None
        self.merge_point_2_id = None

    def clear_remove_state(self):
        self.remove_between_mode = False
        self.remove_start_id = None
        self.remove_end_id = None

    #  New state clear function
    def clear_reverse_path_state(self):
        """Clears the reverse path state."""
        self.reverse_path_mode = False
        self.reverse_start_id = None
        self.reverse_end_id = None

    def finalize_remove_between(self):
        """Finalize the removal of nodes between two specified IDs.
        
        This function checks if the start and end node IDs are set, and if a
        CurveManager is available. It then finds the path between the specified  nodes
        and identifies any nodes that need to be removed. If valid nodes  are found, it
        deletes them and updates the plot accordingly. The function  also manages the
        operation modes and button states throughout the process.
        """
        if self.remove_start_id is None or self.remove_end_id is None:
            self.update_status("Error: Start or end node not set.")
            self.clear_operation_modes(back_to_select=True)
            self.update_button_states()
            return

        if not self.curve_manager:
            self.update_status("Error: CurveManager not found.")
            self.clear_operation_modes(back_to_select=True)
            self.update_button_states()
            return

        print(f"Finding path from {self.remove_start_id} to {self.remove_end_id} for removal...")
        path_ids = self.curve_manager._find_path(self.remove_start_id, self.remove_end_id)

        if not path_ids or len(path_ids) < 2:
            self.update_status("No forward/backward path found between nodes.")
            self.clear_operation_modes(back_to_select=True)
            self.update_button_states()
            return

        # Get all nodes *between* the start and end
        points_to_delete = path_ids[1:-1]

        if not points_to_delete:
            self.update_status("No nodes to remove between start and end.")
            self.clear_operation_modes(back_to_select=True)
            self.update_button_states()
            return

        # Delete the nodes
        self.data_manager.delete_points(points_to_delete)

        # Re-create the direct edge
        # self.data_manager.add_edge(self.remove_start_id, self.remove_end_id)

        # Redraw
        self.plot_manager.update_plot(self.data_manager.nodes, self.data_manager.edges)
        print(f"Deleted {len(points_to_delete)} nodes and connected edge.")
        self.update_status(f"Deleted {len(points_to_delete)} nodes.")

        self.clear_operation_modes(back_to_select=True)
        self.update_button_states()

    def finalize_reverse_path(self):
        """Finalize the reversal path between two nodes.
        
        This method checks if the start and end nodes for the reversal are set. If
        either  is not set, it updates the status and clears operation modes. It
        verifies the  existence of a CurveManager and attempts to find a path between
        the specified  nodes. If a valid path is found, it calls the data_manager to
        reverse the path  and updates the plot accordingly. Finally, it clears
        operation modes and updates  button states.
        """
        if self.reverse_start_id is None or self.reverse_end_id is None:
            self.update_status("Error: Start or end node not set.")
            self.clear_operation_modes(back_to_select=False)
            self.update_button_states()
            return

        if not self.curve_manager:
            self.update_status("Error: CurveManager not found.")
            self.clear_operation_modes(back_to_select=False)
            self.update_button_states()
            return

        print(f"Finding path from {self.reverse_start_id} to {self.reverse_end_id} for reversal...")
        path_ids = self.curve_manager._find_path(self.reverse_start_id, self.reverse_end_id)

        if not path_ids or len(path_ids) < 2:
            self.update_status("No forward path found between nodes.")
            self.clear_operation_modes(back_to_select=True)
            self.update_button_states()
            return

        # Call the new data_manager function
        self.data_manager.reverse_path(path_ids)

        # Redraw
        self.plot_manager.update_plot(self.data_manager.nodes, self.data_manager.edges)
        print(f"Reversed {len(path_ids) - 1} edges.")
        self.update_status(f"Reversed {len(path_ids) - 1} edges.")

        self.clear_operation_modes(back_to_select=True)
        self.update_button_states()

    def on_connect_nodes(self, event):
        """Initiates the process to connect nodes."""
        self.clear_operation_modes(back_to_select=False)
        self.merge_mode = True
        print("Please select first node to connect")
        self.update_status("Select first node")
        self.update_point_sizes()
        self.update_button_states()

    def finalize_connection(self):
        if self.merge_point_1_id is None or self.merge_point_2_id is None:
            self.update_status("Select two nodes")
            self.clear_merge_state()
            self.update_button_states()
            return

        self.data_manager.add_edge(self.merge_point_1_id, self.merge_point_2_id)
        self.plot_manager.update_plot(self.data_manager.nodes, self.data_manager.edges)
        print(f"Connected node {self.merge_point_1_id} to {self.merge_point_2_id}")
        self.update_status(f"Connected {self.merge_point_1_id} -> {self.merge_point_2_id}")

        # Go back to select mode after connection
        self.clear_operation_modes(back_to_select=False)
        self.update_button_states()

    def save_data(self, event):
        """Saves data using the data manager and updates the status."""
        filename = self.data_manager.save_by_matplotlib()
        if filename:
            print(f"Saved to {filename}")
            self.update_status(f"Saved to {filename}")
        else:
            self.update_status("Save failed")

    def export_selected(self, event):
        if not self.plot_manager.selected_indices:
            self.update_status("Select points to export")
            return
        try:
            selected_nodes = self.data_manager.nodes[np.array(self.plot_manager.selected_indices, dtype=int)]
            filename = f"selected_points_{int(time.time())}.npy"
            np.save(filename, selected_nodes[:, 1:4])  # Save [x, y, yaw]
            self.update_status(f"Exported {len(selected_nodes)} points")
        except Exception as e:
            self.update_status("Export failed")

    def on_click(self, event):
        """Handle click events for various modes in the plot manager.
        
        This function processes mouse click events to manage different drawing and
        selection modes. It checks the current state of the plot manager and the data
        manager to determine the appropriate action, such as adding nodes, selecting
        points, or initiating smoothing and merging operations. The function also
        updates the plot and status messages based on user interactions and the current
        mode.
        
        Args:
            event: The mouse event containing information about the click position and state.
        """
        if self.plot_manager is None or event.inaxes != self.plot_manager.ax or event.button != 1:
            return

        #  Mode-based Event Handling 
        if self.draw_mode:
            if self.curve_manager:
                self.curve_manager.add_draw_point(event.xdata, event.ydata)
                print(f"Added point to {'curve' if self.curve_manager.is_curve else 'line'}")
                self.update_status()
            return

        if self.data_manager.nodes.size == 0 and self.ctrl_pressed:
            # Add first node if Ctrl is pressed
            new_id = self.data_manager.add_node(event.xdata, event.ydata, self.selected_id)
            self.plot_manager.update_plot(self.data_manager.nodes, self.data_manager.edges)
            self.update_status("Added first node")
            return
        elif self.data_manager.nodes.size == 0:
            return  # Do nothing if no nodes and Ctrl not pressed

        click_x, click_y = event.xdata, event.ydata
        nodes = self.data_manager.nodes
        distances = np.sqrt((nodes[:, 1] - click_x) ** 2 + (nodes[:, 2] - click_y) ** 2)
        closest_row_idx = np.argmin(distances)
        closest_point_id = int(nodes[closest_row_idx, 0])

        if self.smoothing_point_selection:
            if self.smoothing_start_id is None:
                self.smoothing_start_id = closest_point_id
                print(f"Selected smooth START node #{closest_row_idx} (ID {closest_point_id})")
                self.update_status(f"Start Node: {closest_row_idx}. Click to select END node.")
                self.plot_manager.selected_indices = [closest_row_idx]
                self.update_point_sizes()
            elif self.smoothing_end_id is None:
                if closest_point_id == self.smoothing_start_id:
                    self.update_status("Cannot select same node. Select END node.")
                    return
                self.smoothing_end_id = closest_point_id
                print(f"Selected smooth END node #{closest_row_idx} (ID {closest_point_id})")
                if self.curve_manager:
                    self.curve_manager.preview_smooth(self.smoothing_start_id, self.smoothing_end_id)
                self.update_button_states()  # Update 'Smooth' button to 'Confirm'
            else:
                # Both are set, reset by selecting a new start point
                self.clear_smoothing_state()
                self.smoothing_start_id = closest_point_id
                print(f"Reset smooth START node #{closest_row_idx} (ID {closest_point_id})")
                self.update_status(f"Start Node: {closest_row_idx}. Click to select END node.")
                self.plot_manager.selected_indices = [closest_row_idx]
                self.update_point_sizes()
                self.update_button_states()
            return

        if self.remove_between_mode:
            if self.remove_start_id is None:
                self.remove_start_id = closest_point_id
                print(f"Selected remove START node #{closest_row_idx} (ID {closest_point_id})")
                self.update_status(f"Start Node: {closest_row_idx}. Click to select END node.")
                self.plot_manager.selected_indices = []
                self.update_point_sizes()
            else:
                if closest_point_id == self.remove_start_id:
                    self.update_status("Cannot select same node. Select END node.")
                    return
                self.remove_end_id = closest_point_id
                print(f"Selected remove END node #{closest_row_idx} (ID {closest_point_id})")
                self.finalize_remove_between()
            return

        if self.reverse_path_mode:  # Click logic for "Reverse Path"
            if self.reverse_start_id is None:
                self.reverse_start_id = closest_point_id
                print(f"Selected reverse START node #{closest_row_idx} (ID {closest_point_id})")
                self.update_status(f"Start Node: {closest_row_idx}. Click to select END node.")
                self.plot_manager.selected_indices = []
                self.update_point_sizes()
            else:
                if closest_point_id == self.reverse_start_id:
                    self.update_status("Cannot select same node. Select END node.")
                    return
                self.reverse_end_id = closest_point_id
                print(f"Selected reverse END node #{closest_row_idx} (ID {closest_point_id})")
                self.finalize_reverse_path()
            return

        if self.merge_mode:
            if self.merge_point_1_id is None:
                self.merge_point_1_id = closest_point_id
                print(f"Selected first node #{closest_row_idx} (ID {closest_point_id})")
                self.update_status(f"Node 1: {closest_row_idx}. Select second node.")
                self.update_point_sizes()
                self.plot_manager.fig.canvas.draw_idle()
            elif self.merge_point_2_id is None and closest_point_id != self.merge_point_1_id:
                self.merge_point_2_id = closest_point_id
                print(f"Selected second node #{closest_row_idx} (ID {closest_point_id})")
                self.finalize_connection()
            return

        if self.ctrl_pressed:
            # ADD POINT (Ctrl + Left Click)
            lane_id_to_use = int(nodes[closest_row_idx, 4])
            new_point_id = self.data_manager.add_node(event.xdata, event.ydata, lane_id_to_use)
            self.data_manager.add_edge(closest_point_id, new_point_id)
            self.plot_manager.update_plot(self.data_manager.nodes, self.data_manager.edges)
            print(
                f"Added node {new_point_id} (Lane {lane_id_to_use}), connected from node #{closest_row_idx} (ID {closest_point_id})")
            self.update_status(f"Added node {new_point_id} (Lane {lane_id_to_use})")
        else:
            # SELECT POINT (Simple Left Click)
            self.plot_manager.selected_indices = []
            self.update_point_sizes()
            self.update_status(f"Selected node #{closest_row_idx} (ID: {closest_point_id})")

    def update_point_sizes(self):
        """Update the sizes of points in scatter plots based on various conditions.
        
        This function adjusts the sizes of points in the lane scatter plots managed by
        the plot_manager. It first checks if there are any nodes to process and
        retrieves the selected indices. For each plot, it determines the base size of
        the points and modifies sizes based on merge, removal, and reverse path modes.
        Finally, it updates the scatter plot sizes and refreshes the canvas.
        
        Args:
            self: The instance of the class containing the plot_manager and data_manager.
        """
        if self.plot_manager is None:
            return
        try:
            nodes = self.data_manager.nodes
            if nodes.size == 0:
                return

            selected_row_set = set(self.plot_manager.selected_indices)

            for plot_idx, sc in enumerate(self.plot_manager.lane_scatter_plots):
                row_indices = self.plot_manager.indices[plot_idx]
                if len(row_indices) == 0:
                    continue

                lane_id = int(nodes[row_indices[0], 4])
                base_size = 20 if self.plot_manager.highlighted_lane == lane_id else 10
                sizes = np.full(len(row_indices), base_size, dtype=float)
                point_ids_in_plot = nodes[row_indices, 0]
                id_to_local_idx = {int(pid): i for i, pid in enumerate(point_ids_in_plot)}

                if self.merge_mode:
                    if self.merge_point_1_id in id_to_local_idx:
                        sizes[id_to_local_idx[self.merge_point_1_id]] = 100
                    if self.merge_point_2_id in id_to_local_idx:
                        sizes[id_to_local_idx[self.merge_point_2_id]] = 80

                if self.remove_between_mode:
                    if self.remove_start_id in id_to_local_idx:
                        sizes[id_to_local_idx[self.remove_start_id]] = 100

                if self.reverse_path_mode:
                    if self.reverse_start_id in id_to_local_idx:
                        sizes[id_to_local_idx[self.reverse_start_id]] = 100

                for local_idx, global_row_idx in enumerate(row_indices):
                    if global_row_idx in selected_row_set:
                        sizes[local_idx] = 30

                sc.set_sizes(sizes)

            self.plot_manager.fig.canvas.draw_idle()
            self.plot_manager.fig.canvas.flush_events()
            self.update_button_states()
        except Exception as e:
            print(f"Error updating point sizes: {e}")

    def clear_all_modes(self):
        """Helper to reset all operation states."""
        self.clear_smoothing_state()
        self.clear_merge_state()
        self.clear_remove_state()
        self.draw_mode = False
        self.plot_manager.rs.set_active(False)
        if self.curve_manager:
            self.curve_manager.clear_draw()
        if self.plot_manager.selected_indices:
            self.plot_manager.selected_indices = []
            self.update_point_sizes()
        self.update_button_states()

    def on_pick(self, event):
        """Handles the picking event for scatter plot interactions.
        
        This method processes mouse click events on scatter plot artists.  It checks if
        the right mouse button was clicked and if the plot manager  is active.
        Depending on whether the control key is pressed, it either  breaks connections
        for a selected node or deletes the node from the  data manager. The plot is
        then updated to reflect these changes,  and the status is updated accordingly.
        """
        if self.plot_manager is None or event.mouseevent.button != 3 or self.plot_manager.rs.active:
            return

        artist = event.artist
        if artist not in self.plot_manager.lane_scatter_plots:
            return

        local_ind = event.ind[0]
        file_index = self.plot_manager.lane_scatter_plots.index(artist)
        global_row_ind = self.plot_manager.indices[file_index][local_ind]
        point_id_to_use = int(self.data_manager.nodes[global_row_ind, 0])

        if self.ctrl_pressed:
            print(f"Breaking connections for node #{global_row_ind} (ID {point_id_to_use})")
            self.data_manager.delete_edges_for_node(point_id_to_use)
            self.plot_manager.update_plot(self.data_manager.nodes, self.data_manager.edges)
            self.update_status(f"Broke connections for node #{global_row_ind}")
        else:
            self.data_manager.delete_points([point_id_to_use])
            self.plot_manager.selected_indices = []
            self.plot_manager.update_plot(self.data_manager.nodes, self.data_manager.edges)
            self.update_status(f"Deleted node #{global_row_ind} (ID: {point_id_to_use})")

    def on_select(self, eclick, erelease):
        try:
            x1, y1 = eclick.xdata, eclick.ydata
            x2, y2 = erelease.xdata, erelease.ydata
            x_min, x_max = min(x1, x2), max(x1, x2)
            y_min, y_max = min(y1, y2), max(y1, y2)

            nodes = self.data_manager.nodes
            x_mask = (nodes[:, 1] >= x_min) & (nodes[:, 1] <= x_max)
            y_mask = (nodes[:, 2] >= y_min) & (nodes[:, 2] <= y_max)
            combined_mask = x_mask & y_mask

            self.plot_manager.selected_indices = np.where(combined_mask)[0].tolist()
            print(f"Selected {len(self.plot_manager.selected_indices)} nodes")
            self.update_point_sizes()
            self.update_status(f"Selected {len(self.plot_manager.selected_indices)} nodes")
        except Exception as e:
            print(f"Error during selection: {e}")
        finally:
            #  Deactivate selector after use 
            self.plot_manager.rs.set_active(False)
            self.update_status("Selection complete.")

    def on_key(self, event):
        key = event.key.lower()
        if 'control' in key:
            self.ctrl_pressed = True
        if key == 's':
            self.s_pressed = True
        if key == 'ctrl+z':
            self.on_undo(event)
        elif key in ('ctrl+shift+z', 'ctrl+y'):
            self.on_redo(event)
        elif key == 'd':
            self.on_toggle_draw_mode(event)
        elif key == 'escape':
            self.on_cancel_operation(event)
        elif key == 'delete':
            self.on_delete(event)
        elif key == 'enter':
            self.on_finalize_draw(event)
        elif key in '0123456789':
            new_id = int(key)
            if new_id < len(self.data_manager.file_names):
                self.selected_id = new_id
                print(f"Set new point lane ID to {new_id} ({self.data_manager.file_names[new_id]})")
                self.update_status(f"New point ID set to {new_id}")
            else:
                self.update_status(f"Invalid lane ID {new_id}")
        if self.ctrl_pressed and self.s_pressed:
            if not (self.draw_mode or self.smoothing_point_selection or self.merge_mode or self.remove_between_mode):
                self.plot_manager.rs.set_active(True)
                self.update_status("Rectangle Select: Click and drag to select points.")

    def on_key_release(self, event):
        key = event.key.lower()
        if 'control' in key:
            self.ctrl_pressed = False
        if key == 's':
            self.s_pressed = False

    def on_escape(self, event):
        self.on_cancel_operation(event)

    def on_delete(self, event):
        if self.plot_manager is None or not self.selection_mode or not self.plot_manager.selected_indices:
            return

        row_indices = self.plot_manager.selected_indices
        point_ids_to_delete = self.data_manager.nodes[row_indices, 0].astype(int)

        self.data_manager.delete_points(point_ids_to_delete)
        self.plot_manager.selected_indices = []
        self.plot_manager.update_plot(self.data_manager.nodes, self.data_manager.edges)
        print(f"Deleted {len(point_ids_to_delete)} nodes")
        self.update_status(f"Deleted {len(point_ids_to_delete)} nodes")

    def on_undo(self, event):
        if self.plot_manager is None: return
        nodes, edges, success = self.data_manager.undo()
        if success:
            self.plot_manager.selected_indices = []
            self.plot_manager.update_plot(nodes, edges)
            self.update_status("Undo performed")
        else:
            self.update_status("Nothing to undo")

    def on_redo(self, event):
        if self.plot_manager is None: return
        nodes, edges, success = self.data_manager.redo()
        if success:
            self.plot_manager.selected_indices = []
            self.plot_manager.update_plot(nodes, edges)
            self.update_status("Redo performed")
        else:
            self.update_status("Nothing to redo")

    def on_finalize_draw(self, event):
        """Finalizes the drawing operation and updates the UI."""
        if not self.draw_mode or not self.curve_manager:
            return
        self.curve_manager.finalize_draw(self.selected_id)
        self.plot_manager.selected_indices = []
        self.update_point_sizes()
        print(f"Finalized {'curve' if self.curve_manager.is_curve else 'line'} with ID {self.selected_id}")
        self.update_status("Drawing finalized")
        # Go back to select mode
        self.clear_operation_modes(back_to_select=False)
        self.update_button_states()

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
