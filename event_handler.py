import numpy as np
from curve_manager import CurveManager

class EventHandler:
    def __init__(self, data_manager):
        self.data_manager = data_manager
        self.plot_manager = None
        self.curve_manager = None
        self.selection_mode = True
        self.draw_mode = False
        self.selected_id = 0
        self.id_set = False
        # State for smoothing point selection
        self.smoothing_point_selection = False
        self.smoothing_start_idx = None
        self.smoothing_end_idx = None
        self.smoothing_selected_indices = None
        self.smoothing_lane_id = None
        self.smoothing_preview_line = None

    def set_plot_manager(self, plot_manager):
        self.plot_manager = plot_manager
        self.curve_manager = CurveManager(self.data_manager, self.plot_manager)

    def on_toggle_mode(self, event):
        self.draw_mode = False
        self.selection_mode = not self.selection_mode
        self.plot_manager.rs.set_active(self.selection_mode)
        self.plot_manager.btn_toggle.label.set_text(
            'Select Mode' if self.selection_mode else 'Add/Delete Mode')
        self.plot_manager.btn_toggle.color = 'lightcoral' if self.selection_mode else 'lightgreen'
        if not self.selection_mode:
            self.id_set = False
            self.clear_smoothing_state()
            if self.plot_manager.selected_indices:
                self.plot_manager.selected_indices = []
                for sc in self.plot_manager.scatter_plots:
                    sc.set_sizes([10] * len(sc.get_offsets()))
                print("Cleared selection")
        print(f"Entered {'selection' if self.selection_mode else 'add/delete'} mode")
        self.plot_manager.update_status()

    def on_toggle_draw_mode(self, event):
        self.selection_mode = False
        self.draw_mode = not self.draw_mode
        self.plot_manager.rs.set_active(False)
        self.plot_manager.btn_toggle.label.set_text('Select Mode')
        self.plot_manager.btn_toggle.color = 'lightcoral'
        if not self.draw_mode:
            self.id_set = False
            self.clear_smoothing_state()
            self.curve_manager.draw_points = []
            if self.curve_manager.current_line:
                self.curve_manager.current_line.remove()
                self.curve_manager.current_line = None
                self.plot_manager.fig.canvas.draw_idle()
            if self.plot_manager.selected_indices:
                self.plot_manager.selected_indices = []
                for sc in self.plot_manager.scatter_plots:
                    sc.set_sizes([10] * len(sc.get_offsets()))
                print("Cleared selection")
        print(f"Entered {'draw' if self.draw_mode else 'add/delete'} mode")
        self.plot_manager.update_status()

    def on_toggle_linecurve(self, event):
        if not self.draw_mode:
            print("Must be in Draw Mode to toggle line/curve")
            return
        self.curve_manager.is_curve = not self.curve_manager.is_curve
        self.plot_manager.btn_linecurve.label.set_text('Curve' if self.curve_manager.is_curve else 'Line')
        self.curve_manager.update_draw_line()
        print(f"Drawing {'curve' if self.curve_manager.is_curve else 'line'}")
        self.plot_manager.update_status()

    def on_straighten(self, event):
        if not self.selection_mode or not self.plot_manager.selected_indices:
            print("Must be in Selection Mode with points selected to smooth")
            return

        # Store the current state for smoothing
        self.smoothing_selected_indices = self.plot_manager.selected_indices
        self.smoothing_lane_id = self.selected_id  # Used for new points' lane ID
        self.smoothing_point_selection = True
        self.smoothing_start_idx = None
        self.smoothing_end_idx = None

        # Highlight selected points to guide the user
        self.update_point_sizes()
        self.plot_manager.fig.canvas.draw_idle()

        print(f"Please click on the starting point for smoothing (from selected points)")
        self.plot_manager.update_status("Click to select the starting point for smoothing")

    def on_confirm_start(self, event):
        if not self.smoothing_point_selection or self.smoothing_start_idx is None:
            print("Please select the starting point first")
            return
        print(f"Confirmed start point (index {self.smoothing_start_idx}). Now click on the ending point.")
        self.plot_manager.update_status("Click to select the ending point for smoothing")

    def on_confirm_end(self, event):
        if not self.smoothing_point_selection or self.smoothing_start_idx is None or self.smoothing_end_idx is None:
            print("Please select both start and end points")
            return
        print(f"End point confirmed (index {self.smoothing_end_idx}). Smoothing the segment...")

        # Perform smoothing
        new_indices = self.curve_manager.straighten_segment(
            self.smoothing_selected_indices,
            self.smoothing_lane_id,
            self.smoothing_start_idx,
            self.smoothing_end_idx
        )

        # Mark the smoothed area
        if new_indices:
            smoothed_points = self.data_manager.data[new_indices, :2]
            self.plot_manager.mark_smoothed_area(smoothed_points)

        # Reset smoothing state
        self.clear_smoothing_state()
        if new_indices:
            self.plot_manager.selected_indices = new_indices
            self.plot_manager.update_plot(self.data_manager.data)
            print(f"Smoothed {len(new_indices)} points")
        else:
            self.plot_manager.selected_indices = []
            print("Smoothing failed or returned empty result, selection cleared")

        # Reset point sizes
        for sc in self.plot_manager.scatter_plots:
            sc.set_sizes([10] * len(sc.get_offsets()))
        self.plot_manager.fig.canvas.draw_idle()
        self.plot_manager.update_status()

    def on_cancel_smoothing(self, event):
        print("Smoothing canceled")
        self.clear_smoothing_state()
        for sc in self.plot_manager.scatter_plots:
            sc.set_sizes([10] * len(sc.get_offsets()))
        self.plot_manager.fig.canvas.draw_idle()
        self.plot_manager.update_status()

    def on_clear_selection(self, event):
        if self.plot_manager.selected_indices:
            self.plot_manager.selected_indices = []
            for sc in self.plot_manager.scatter_plots:
                sc.set_sizes([10] * len(sc.get_offsets()))
            print("Cleared selection")
        self.clear_smoothing_state()
        self.plot_manager.clear_smoothed_area()
        self.plot_manager.fig.canvas.draw_idle()
        self.plot_manager.update_status()

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

    def on_click(self, event):
        if self.plot_manager is None or event.inaxes != self.plot_manager.ax or event.button != 1:
            print("Click ignored: invalid action")
            return

        # Handle smoothing point selection
        if self.smoothing_point_selection:
            # Find the closest point in selected_indices to the click
            click_x, click_y = event.xdata, event.ydata
            selected_points = self.data_manager.data[self.smoothing_selected_indices, :2]
            distances = np.sqrt((selected_points[:, 0] - click_x) ** 2 + (selected_points[:, 1] - click_y) ** 2)
            closest_idx = np.argmin(distances)
            global_idx = self.smoothing_selected_indices[closest_idx]

            if self.smoothing_start_idx is None:
                self.smoothing_start_idx = global_idx
                self.update_point_sizes()
                self.plot_manager.fig.canvas.draw_idle()
                print(f"Start point selected (index {self.smoothing_start_idx}). Click 'Confirm Start' or select the ending point.")
                self.plot_manager.update_status("Click 'Confirm Start' or select the ending point")
            elif self.smoothing_end_idx is None:
                self.smoothing_end_idx = global_idx
                self.update_point_sizes()
                # Preview the smoothed curve
                preview_points = self.curve_manager.preview_smooth(
                    self.smoothing_selected_indices,
                    self.smoothing_lane_id,
                    self.smoothing_start_idx,
                    self.smoothing_end_idx
                )
                if preview_points is not None:
                    if self.smoothing_preview_line:
                        self.smoothing_preview_line.remove()
                    self.smoothing_preview_line = self.plot_manager.ax.plot(
                        preview_points[:, 0], preview_points[:, 1], 'b--', alpha=0.5, label='Preview')[0]
                    self.plot_manager.ax.legend()
                    self.plot_manager.fig.canvas.draw_idle()
                print(f"End point selected (index {self.smoothing_end_idx}). Click 'Confirm End' to apply smoothing.")
                self.plot_manager.update_status("Click 'Confirm End' to apply smoothing or 'Cancel Smoothing' to abort")
            return

        # Existing click handling for drawing and adding points
        if self.draw_mode:
            if not self.id_set:
                print("Press 1-9 to select an ID before drawing")
                return
            self.curve_manager.add_draw_point(event.xdata, event.ydata)
            print(f"Added point to {'curve' if self.curve_manager.is_curve else 'line'}")
            self.plot_manager.update_status()
            return
        if self.selection_mode:
            print("Click ignored: in selection mode")
            return
        if not self.id_set:
            print("Press 1-9 to select an ID before adding a point")
            return
        self.plot_manager.selected_indices = []
        self.plot_manager.clear_smoothed_area()
        for sc in self.plot_manager.scatter_plots:
            sc.set_sizes([10] * len(sc.get_offsets()))
        self.data_manager.add_point(event.xdata, event.ydata, self.selected_id)
        self.plot_manager.update_plot(self.data_manager.data)
        print(f"Added point with ID {self.selected_id} ({self.data_manager.file_names[self.selected_id]})")
        self.plot_manager.update_status()

    def update_point_sizes(self):
        for sc in self.plot_manager.scatter_plots:
            sizes = [100 if i == self.smoothing_start_idx else
                     (80 if i == self.smoothing_end_idx else
                      (50 if i in self.smoothing_selected_indices else 10))
                     for i in range(len(self.data_manager.data))]
            sc.set_sizes(sizes)

    def on_pick(self, event):
        if self.plot_manager is None or event.mouseevent.button != 3 or self.plot_manager.rs.active:
            return
        if not self.selection_mode:
            self.plot_manager.selected_indices = []
            for sc in self.plot_manager.scatter_plots:
                sc.set_sizes([10] * len(sc.get_offsets()))
        artist = event.artist
        ind = event.ind[0]
        file_index = self.plot_manager.scatter_plots.index(artist)
        global_ind = self.plot_manager.indices[file_index][ind]
        self.data_manager.delete_points([global_ind])
        self.plot_manager.selected_indices = [i for i in self.plot_manager.selected_indices if i != global_ind]
        self.plot_manager.clear_smoothed_area()
        self.plot_manager.update_plot(self.data_manager.data)
        self.plot_manager.update_status()

    def on_select(self, eclick, erelease):
        if not self.selection_mode:
            return
        x1, y1 = eclick.xdata, eclick.ydata
        x2, y2 = erelease.xdata, erelease.ydata
        x_min, x_max = min(x1, x2), max(x1, x2)
        y_min, y_max = min(y1, y2), max(y1, y2)
        self.plot_manager.selected_indices = [
            i for i in range(len(self.data_manager.data))
            if x_min <= self.data_manager.data[i, 0] <= x_max and
               y_min <= self.data_manager.data[i, 1] <= y_max
        ]
        print(f"Selected {len(self.plot_manager.selected_indices)} points")
        self.plot_manager.clear_smoothed_area()
        self.plot_manager.update_plot(self.data_manager.data)
        self.plot_manager.update_status()

    def on_key(self, event):
        key_map = {
            '1-9': lambda k: int(k) - 1 if int(k) - 1 < len(self.data_manager.file_names) else None,
            'ctrl+z': self.on_undo,
            'ctrl+y': self.on_redo,
            'tab': self.on_toggle_mode,
            'd': self.on_toggle_draw_mode,
            'escape': self.on_escape,
            'delete': self.on_delete,
            'enter': self.on_finalize_draw
        }

        if event.key in '123456789':
            new_id = key_map['1-9'](event.key)
            if new_id is not None:
                self.selected_id = new_id
                self.id_set = True
                print(f"Set ID {self.selected_id} ({self.data_manager.file_names[self.selected_id]})")
                if self.selection_mode and self.plot_manager.selected_indices:
                    self.data_manager.change_ids(self.plot_manager.selected_indices, self.selected_id)
                    self.plot_manager.update_plot(self.data_manager.data)
                    print(f"Changed {len(self.plot_manager.selected_indices)} points to ID {self.selected_id}")
                self.plot_manager.update_status()
            else:
                print(f"Invalid ID: only {len(self.data_manager.file_names)} files available")
                self.id_set = False
        elif event.key.lower() in key_map:
            key_map[event.key.lower()](event)

    def on_escape(self, event):
        if self.plot_manager is None:
            return
        self.selection_mode = False
        self.draw_mode = False
        self.id_set = False
        self.clear_smoothing_state()
        self.plot_manager.rs.set_active(False)
        self.curve_manager.draw_points = []
        if self.curve_manager.current_line:
            self.curve_manager.current_line.remove()
            self.curve_manager.current_line = None
            self.plot_manager.fig.canvas.draw_idle()
        if self.plot_manager.selected_indices:
            self.plot_manager.selected_indices = []
            for sc in self.plot_manager.scatter_plots:
                sc.set_sizes([10] * len(sc.get_offsets()))
            print("Cleared selection")
        self.plot_manager.clear_smoothed_area()
        print("Entered add/delete mode")
        self.plot_manager.update_status()

    def on_delete(self, event):
        if self.plot_manager is None or not self.selection_mode or not self.plot_manager.selected_indices:
            return
        deleted_indices = self.plot_manager.selected_indices
        self.data_manager.delete_points(deleted_indices)
        self.plot_manager.selected_indices = [
            i for i in range(len(self.data_manager.data))
            if i not in deleted_indices and i in self.plot_manager.selected_indices
        ]
        self.plot_manager.clear_smoothed_area()
        self.plot_manager.update_plot(self.data_manager.data)
        print(
            f"Deleted {len(deleted_indices)} points, {len(self.plot_manager.selected_indices)} points remain selected")
        self.plot_manager.update_status()

    def on_undo(self, event):
        if self.plot_manager is None:
            return
        data, success = self.data_manager.undo()
        if success:
            self.plot_manager.selected_indices = []
            self.plot_manager.clear_smoothed_area()
            self.plot_manager.update_plot(data)
            print("Undo performed, selection cleared")
        self.plot_manager.update_status()

    def on_redo(self, event):
        if self.plot_manager is None:
            return
        data, success = self.data_manager.redo()
        if success:
            self.plot_manager.selected_indices = []
            self.plot_manager.clear_smoothed_area()
            self.plot_manager.update_plot(data)
            print("Redo performed, selection cleared")
        self.plot_manager.update_status()

    def on_save(self, event):
        filename = self.data_manager.save()
        print(f"Saved to {filename}")
        self.plot_manager.update_status()

    def on_finalize_draw(self, event):
        if not self.draw_mode:
            return
        self.curve_manager.finalize_draw(self.selected_id)
        self.plot_manager.selected_indices = []
        self.plot_manager.clear_smoothed_area()
        print(f"Finalized {'curve' if self.curve_manager.is_curve else 'line'} with ID {self.selected_id}")
        self.plot_manager.update_status()