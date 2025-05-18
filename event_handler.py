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
            if self.plot_manager.selected_indices:
                self.plot_manager.selected_indices = []
                for sc in self.plot_manager.scatter_plots:
                    sc.set_sizes([10] * len(sc.get_offsets()))
                print("Cleared selection")
        print(f"Entered {'selection' if self.selection_mode else 'add/delete'} mode")
        self.plot_manager.update_title()

    def on_toggle_draw_mode(self, event):
        self.selection_mode = False
        self.draw_mode = not self.draw_mode
        self.plot_manager.rs.set_active(False)
        self.plot_manager.btn_toggle.label.set_text('Select Mode')
        self.plot_manager.btn_toggle.color = 'lightcoral'
        if not self.draw_mode:
            self.id_set = False
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
        self.plot_manager.update_title()

    def on_toggle_linecurve(self, event):
        if not self.draw_mode:
            print("Must be in Draw Mode to toggle line/curve")
            return
        self.curve_manager.is_curve = not self.curve_manager.is_curve
        self.plot_manager.btn_linecurve.label.set_text('Curve' if self.curve_manager.is_curve else 'Line')
        self.curve_manager.update_draw_line()
        print(f"Drawing {'curve' if self.curve_manager.is_curve else 'line'}")

    def on_straighten(self, event):
        if not self.selection_mode or not self.plot_manager.selected_indices:
            print("Must be in Selection Mode with points selected to smooth")
            return

        # Store the current state for smoothing
        self.smoothing_selected_indices = self.plot_manager.selected_indices
        self.smoothing_lane_id = self.selected_id  # Use the current selected ID as lane_id
        self.smoothing_point_selection = True
        self.smoothing_start_idx = None
        self.smoothing_end_idx = None

        # Highlight selected points to guide the user
        for sc in self.plot_manager.scatter_plots:
            sizes = [50 if i in self.smoothing_selected_indices else 10 for i in range(len(self.data_manager.data))]
            sc.set_sizes(sizes)
        self.plot_manager.fig.canvas.draw_idle()

        print(
            f"Please click on the starting point for smoothing (from selected points with lane ID {self.smoothing_lane_id})")

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

            selected_indices = set(self.smoothing_selected_indices)
            selected_indices = list(selected_indices)
            # Verify the point matches the lane_id
            if int(self.data_manager.data[global_idx, self.data_manager.D]) != self.smoothing_lane_id:
                print(f"Clicked point (index {global_idx}) does not match lane ID {self.smoothing_lane_id}")
                return

            if self.smoothing_start_idx is None:
                self.smoothing_start_idx = global_idx
                print(f"Start point selected (index {self.smoothing_start_idx}). Now click on the ending point.")
                # Highlight the start point
                for sc in self.plot_manager.scatter_plots:
                    sizes = [
                        100 if i == self.smoothing_start_idx else (50 if i in self.smoothing_selected_indices else 10)
                        for i in range(len(self.data_manager.data))]
                    sc.set_sizes(sizes)
                self.plot_manager.fig.canvas.draw_idle()
            elif self.smoothing_end_idx is None:
                self.smoothing_end_idx = global_idx
                print(f"End point selected (index {self.smoothing_end_idx}). Smoothing the segment...")

                selected_indices = set(self.smoothing_selected_indices)
                selected_indices = list(selected_indices)
                if len(selected_indices) == 1:
                    self.smoothing_lane_id = selected_indices[0]
                # Perform smoothing
                new_indices = self.curve_manager.straighten_segment(
                    self.smoothing_selected_indices,
                    self.smoothing_lane_id,
                    self.smoothing_start_idx,
                    self.smoothing_end_idx
                )

                # Reset smoothing state
                self.smoothing_point_selection = True
                self.smoothing_start_idx = None
                self.smoothing_end_idx = None
                self.smoothing_selected_indices = None
                self.smoothing_lane_id = None

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
            return

        # Existing click handling for drawing and adding points
        if self.draw_mode:
            if not self.id_set:
                print("Press 1-9 to select an ID before drawing")
                return
            self.curve_manager.add_draw_point(event.xdata, event.ydata)
            print(f"Added point to {'curve' if self.curve_manager.is_curve else 'line'}")
            return
        if self.selection_mode:
            print("Click ignored: in selection mode")
            return
        if not self.id_set:
            print("Press 1-9 to select an ID before adding a point")
            return
        self.plot_manager.selected_indices = []
        for sc in self.plot_manager.scatter_plots:
            sc.set_sizes([10] * len(sc.get_offsets()))
        self.data_manager.add_point(event.xdata, event.ydata, self.selected_id)
        self.plot_manager.update_plot(self.data_manager.data)
        print(f"Added point with ID {self.selected_id} ({self.data_manager.file_names[self.selected_id]})")

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
        self.plot_manager.update_plot(self.data_manager.data)

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
        self.plot_manager.update_plot(self.data_manager.data)

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
                self.plot_manager.update_title()
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
        # Reset smoothing state if in point selection mode
        self.smoothing_point_selection = False
        self.smoothing_start_idx = None
        self.smoothing_end_idx = None
        self.smoothing_selected_indices = None
        self.smoothing_lane_id = None
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
        print("Entered add/delete mode")
        self.plot_manager.update_title()

    def on_delete(self, event):
        if self.plot_manager is None or not self.selection_mode or not self.plot_manager.selected_indices:
            return
        deleted_indices = self.plot_manager.selected_indices
        self.data_manager.start_action("Delete selected points")
        self.data_manager.delete_points(deleted_indices)
        self.plot_manager.selected_indices = [
            i for i in range(len(self.data_manager.data))
            if i not in deleted_indices and i in self.plot_manager.selected_indices
        ]
        self.plot_manager.update_plot(self.data_manager.data)
        print(
            f"Deleted {len(deleted_indices)} points, {len(self.plot_manager.selected_indices)} points remain selected")

    def on_undo(self, event):
        if self.plot_manager is None:
            return
        data, success = self.data_manager.undo()
        if success:
            self.plot_manager.selected_indices = []
            self.plot_manager.update_plot(data)
            print("Undo performed, selection cleared")

    def on_redo(self, event):
        if self.plot_manager is None:
            return
        data, success = self.data_manager.redo()
        if success:
            self.plot_manager.selected_indices = []
            self.plot_manager.update_plot(data)
            print("Redo performed, selection cleared")

    def on_save(self, event):
        filename = self.data_manager.save()
        print(f"Saved to {filename}")

    def on_finalize_draw(self, event):
        if not self.draw_mode:
            return
        self.data_manager.start_action(f"Finalize draw (ID {self.selected_id})")
        self.curve_manager.finalize_draw(self.selected_id)
        self.plot_manager.selected_indices = []
        self.data_manager.end_action()
        print(f"Finalized {'curve' if self.curve_manager.is_curve else 'line'} with ID {self.selected_id}")
