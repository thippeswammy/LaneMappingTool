import matplotlib.pyplot as plt
import numpy as np
from matplotlib.widgets import Button

from curve_manager import CurveManager


class EventHandler:
    def __init__(self, data_manager):
        self.data_manager = data_manager
        self.plot_manager = None
        self.curve_manager = None
        self.selection_mode = True
        self.draw_mode = False
        self.selected_id = 0
        self.id_set = True
        self.smoothing_point_selection = False
        self.smoothing_start_idx = None
        self.smoothing_end_idx = None
        self.smoothing_selected_indices = None
        self.smoothing_lane_id = None
        self.smoothing_preview_line = None
        self.merge_mode = False
        self.merge_lane_id = 1  # Start with lane 1
        self.merge_point_0 = None
        self.merge_point_target = None
        self.buttons = {}

    def set_plot_manager(self, plot_manager):
        self.plot_manager = plot_manager
        self.curve_manager = CurveManager(self.data_manager, self.plot_manager)
        self.fig = self.plot_manager.fig
        self.setup_event_handlers()
        self.setup_buttons()

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
        self.buttons['cancel'] = Button(ax_cancel, 'Cancel Smooth')
        self.buttons['cancel'].on_clicked(self.on_cancel_smoothing)

        ax_clear = plt.axes([0.01, 0.60, 0.1, 0.04])
        self.buttons['clear'] = Button(ax_clear, 'Clear Selection')
        self.buttons['clear'].on_clicked(self.on_clear_selection)

        ax_save = plt.axes([0.01, 0.55, 0.1, 0.04])
        self.buttons['save'] = Button(ax_save, 'Save')
        self.buttons['save'].on_clicked(self.save_data)

        ax_merge = plt.axes([0.01, 0.50, 0.1, 0.04])
        self.buttons['merge'] = Button(ax_merge, 'Merge Lanes')
        self.buttons['merge'].on_clicked(self.merge_lanes)

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
            if self.plot_manager.selected_indices:
                self.plot_manager.selected_indices = []
                self.update_point_sizes()
                print("Cleared selection")
        print(f"Entered {'selection' if self.selection_mode else 'add/delete'} mode")
        self.plot_manager.update_status()

    def on_toggle_draw_mode(self, event):
        self.selection_mode = False
        self.draw_mode = not self.draw_mode
        self.plot_manager.rs.set_active(False)
        self.buttons['toggle'].label.set_text('Select Mode')
        self.buttons['toggle'].color = 'lightcoral'
        if not self.draw_mode:
            self.id_set = True
            self.clear_smoothing_state()
            self.curve_manager.draw_points = []
            if self.curve_manager.current_line:
                self.curve_manager.current_line.remove()
                self.curve_manager.current_line = None
                self.plot_manager.fig.canvas.draw_idle()
            if self.plot_manager.selected_indices:
                self.plot_manager.selected_indices = []
                self.update_point_sizes()
                print("Cleared selection")
        print(f"Entered {'draw' if self.draw_mode else 'add/delete'} mode")
        self.plot_manager.update_status()

    def on_toggle_linecurve(self, event):
        if not self.draw_mode:
            print("Must be in Draw Mode to toggle line/curve")
            return
        self.curve_manager.is_curve = not self.curve_manager.is_curve
        self.buttons['linecurve'].label.set_text('Curve' if self.curve_manager.is_curve else 'Line')
        self.curve_manager.update_draw_line()
        print(f"Drawing {'curve' if self.curve_manager.is_curve else 'line'}")
        self.plot_manager.update_status()

    def on_straighten(self, event):
        if not self.selection_mode or not self.plot_manager.selected_indices:
            print("Must be in Selection Mode with points selected to smooth")
            return
        self.smoothing_selected_indices = self.plot_manager.selected_indices
        self.smoothing_lane_id = self.selected_id
        self.smoothing_point_selection = True
        self.smoothing_start_idx = None
        self.smoothing_end_idx = None
        self.update_point_sizes()
        self.plot_manager.fig.canvas.draw_idle()
        print("Please click on the starting point for smoothing (from selected points)")
        self.plot_manager.update_status("Click to select the starting point for smoothing")

    def on_confirm_start(self, event):
        if not self.smoothing_point_selection or self.smoothing_start_idx is None:
            print("Please select the starting point first")
            return
        print(f"Confirmed start point (index {self.smoothing_start_idx}). Now click on the ending point.")
        self.update_point_sizes()
        self.plot_manager.fig.canvas.draw_idle()
        self.plot_manager.update_status("Click to select the ending point for smoothing")

    def on_confirm_end(self, event):
        if not self.smoothing_point_selection or self.smoothing_start_idx is None or self.smoothing_end_idx is None:
            print("Please select both start and end points")
            return
        print(f"End point confirmed (index {self.smoothing_end_idx}). Smoothing the segment...")
        new_indices = self.curve_manager.straighten_segment(
            self.smoothing_selected_indices,
            self.smoothing_lane_id,
            self.smoothing_start_idx,
            self.smoothing_end_idx
        )
        self.clear_smoothing_state()
        if new_indices:
            self.plot_manager.selected_indices = new_indices
            self.plot_manager.update_plot(self.data_manager.data)
            print(f"Smoothed {len(new_indices)} points")
        else:
            self.plot_manager.selected_indices = []
            self.update_point_sizes()
            print("Smoothing failed or returned empty result, selection cleared")
        self.plot_manager.fig.canvas.draw_idle()
        self.plot_manager.update_status()

    def on_cancel_smoothing(self, event):
        print("Smoothing canceled")
        self.clear_smoothing_state()
        self.update_point_sizes()
        self.plot_manager.fig.canvas.draw_idle()
        self.plot_manager.update_status()

    def on_clear_selection(self, event):
        if self.plot_manager.selected_indices:
            self.plot_manager.selected_indices = []
            print("Cleared selection")
        self.clear_smoothing_state()
        self.clear_merge_state()
        self.update_point_sizes()
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

    def clear_merge_state(self):
        self.merge_mode = False
        self.merge_point_0 = None
        self.merge_point_target = None
        self.plot_manager.update_status()

    def merge_lanes(self, event):
        unique_lanes = np.unique(self.data_manager.data[:, -1])
        if len(unique_lanes) <= 1:
            print("Only one lane present, no merging needed")
            self.clear_merge_state()
            return
        if self.merge_lane_id not in unique_lanes:
            print(f"Lane {self.merge_lane_id} does not exist")
            self.clear_merge_state()
            return
        self.merge_mode = True
        self.merge_point_0 = None
        self.merge_point_target = None
        self.plot_manager.update_status(f"Select a point in lane 0")
        print("Please select a point in lane 0")
        self.update_point_sizes()
        self.plot_manager.fig.canvas.draw_idle()

    def finalize_merge(self):
        if self.merge_point_0 is None or self.merge_point_target is None:
            print("Both points must be selected for merging")
            return
        self.data_manager.merge_lanes(0, self.merge_lane_id, self.merge_point_0, self.merge_point_target)
        self.plot_manager.selected_indices = []
        self.plot_manager.file_names = self.data_manager.file_names
        self.plot_manager.update_plot(self.data_manager.data)
        print(f"Merged lane {self.merge_lane_id} into lane 0")
        self.merge_lane_id += 1  # Move to next lane
        self.clear_merge_state()
        self.update_point_sizes()
        self.plot_manager.update_status()

    def save_data(self, event):
        filename = self.data_manager.save()
        print(f"Saved to {filename}")
        self.plot_manager.update_plot(self.data_manager.data)
        self.plot_manager.update_status()

    def on_click(self, event):
        if self.plot_manager is None or event.inaxes != self.plot_manager.ax or event.button != 1:
            print("Click ignored: invalid action")
            return
        if self.merge_mode:
            click_x, click_y = event.xdata, event.ydata
            if self.merge_point_0 is None:
                lane_0_indices = np.where(self.data_manager.data[:, -1] == 0)[0]
                if len(lane_0_indices) == 0:
                    print("No points in lane 0")
                    self.clear_merge_state()
                    return
                lane_0_points = self.data_manager.data[lane_0_indices, :2]
                distances = np.sqrt((lane_0_points[:, 0] - click_x) ** 2 + (lane_0_points[:, 1] - click_y) ** 2)
                closest_idx = np.argmin(distances)
                self.merge_point_0 = lane_0_indices[closest_idx]
                print(f"Selected point in lane 0 (index {self.merge_point_0})")
                self.plot_manager.update_status(f"Select a point in lane {self.merge_lane_id}")
                self.update_point_sizes()
                self.plot_manager.fig.canvas.draw_idle()
            elif self.merge_point_target is None:
                target_indices = np.where(self.data_manager.data[:, -1] == self.merge_lane_id)[0]
                if len(target_indices) == 0:
                    print(f"No points in lane {self.merge_lane_id}")
                    self.clear_merge_state()
                    return
                target_points = self.data_manager.data[target_indices, :2]
                distances = np.sqrt((target_points[:, 0] - click_x) ** 2 + (target_points[:, 1] - click_y) ** 2)
                closest_idx = np.argmin(distances)
                self.merge_point_target = target_indices[closest_idx]
                print(f"Selected point in lane {self.merge_lane_id} (index {self.merge_point_target})")
                self.finalize_merge()
            return
        if self.smoothing_point_selection:
            click_x, click_y = event.xdata, event.ydata
            selected_points = self.data_manager.data[self.smoothing_selected_indices, :2]
            distances = np.sqrt((selected_points[:, 0] - click_x) ** 2 + (selected_points[:, 1] - click_y) ** 2)
            closest_idx = np.argmin(distances)
            global_idx = self.smoothing_selected_indices[closest_idx]
            if self.smoothing_start_idx is None:
                self.smoothing_start_idx = global_idx
                self.update_point_sizes()
                self.plot_manager.fig.canvas.draw_idle()
                print(
                    f"Start point selected (index {self.smoothing_start_idx}). Click 'Confirm Start' or select the ending point.")
                self.plot_manager.update_status("Click 'Confirm Start' or select the ending point")
            elif self.smoothing_end_idx is None:
                self.smoothing_end_idx = global_idx
                self.update_point_sizes()
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
        if self.draw_mode:
            self.curve_manager.add_draw_point(event.xdata, event.ydata)
            print(f"Added point to {'curve' if self.curve_manager.is_curve else 'line'}")
            self.plot_manager.update_status()
            return
        if self.selection_mode:
            print("Click ignored: in selection mode")
            return
        self.plot_manager.selected_indices = []
        self.update_point_sizes()
        self.data_manager.add_point(event.xdata, event.ydata, self.selected_id)
        self.plot_manager.update_plot(self.data_manager.data)
        print(f"Added point with ID {self.selected_id} ({self.data_manager.file_names[self.selected_id]})")
        self.plot_manager.update_status()

    def update_point_sizes(self):
        print("Updating point sizes for highlighting")
        if self.plot_manager is None:
            print("Plot manager not set, skipping update_point_sizes")
            return
        for lane_id, sc in enumerate(self.plot_manager.scatter_plots):
            indices = self.plot_manager.indices[lane_id]
            if len(indices) == 0:
                continue
            sizes = np.full(len(indices), 10, dtype=float)
            for local_idx, global_idx in enumerate(indices):
                if self.merge_mode:
                    if global_idx == self.merge_point_0:
                        sizes[local_idx] = 100
                    elif global_idx == self.merge_point_target:
                        sizes[local_idx] = 80
                elif self.smoothing_point_selection:
                    if global_idx == self.smoothing_start_idx:
                        sizes[local_idx] = 100
                    elif global_idx == self.smoothing_end_idx:
                        sizes[local_idx] = 80
                    elif global_idx in self.smoothing_selected_indices:
                        sizes[local_idx] = 50
                elif global_idx in self.plot_manager.selected_indices:
                    sizes[local_idx] = 30
            print(f"Setting sizes for lane {lane_id}: (total {len(sizes)} points)")
            sc.set_sizes(sizes)
        self.plot_manager.fig.canvas.draw_idle()
        self.plot_manager.fig.canvas.flush_events()

    def on_pick(self, event):
        if self.plot_manager is None or event.mouseevent.button != 3 or self.plot_manager.rs.active:
            return
        if not self.selection_mode:
            self.plot_manager.selected_indices = []
            self.update_point_sizes()
        artist = event.artist
        ind = event.ind[0]
        file_index = self.plot_manager.scatter_plots.index(artist)
        global_ind = self.plot_manager.indices[file_index][ind]
        self.data_manager.delete_points([global_ind])
        self.plot_manager.selected_indices = [i for i in self.plot_manager.selected_indices if i != global_ind]
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
        self.update_point_sizes()
        self.plot_manager.fig.canvas.draw_idle()
        self.plot_manager.update_status()

    def on_key(self, event):
        key_map = {
            'ctrl+z': self.on_undo,
            'ctrl+y': self.on_redo,
            'tab': self.on_toggle_mode,
            'd': self.on_toggle_draw_mode,
            'escape': self.on_escape,
            'delete': self.on_delete,
            'enter': self.on_finalize_draw
        }
        if event.key in '123456789':
            print("Lane ID selection disabled; use default ID 0 or Merge Lanes button")
        elif event.key.lower() in key_map:
            key_map[event.key.lower()](event)

    def on_escape(self, event):
        if self.plot_manager is None:
            return
        self.selection_mode = False
        self.draw_mode = False
        self.id_set = True
        self.clear_smoothing_state()
        self.clear_merge_state()
        self.plot_manager.rs.set_active(False)
        self.curve_manager.draw_points = []
        if self.curve_manager.current_line:
            self.curve_manager.current_line.remove()
            self.curve_manager.current_line = None
            self.plot_manager.fig.canvas.draw_idle()
        if self.plot_manager.selected_indices:
            self.plot_manager.selected_indices = []
            self.update_point_sizes()
            print("Cleared selection")
        print("Entered add/delete mode")
        self.plot_manager.update_status()

    def on_delete(self, event):
        if self.plot_manager is None or not self.selection_mode or not self.plot_manager.selected_indices:
            return
        deleted_indices = self.plot_manager.selected_indices
        self.data_manager.delete_points(deleted_indices)
        self.plot_manager.selected_indices = []
        self.plot_manager.update_plot(self.data_manager.data)
        print(f"Deleted {len(deleted_indices)} points")
        self.plot_manager.update_status()

    def on_undo(self, event):
        if self.plot_manager is None:
            return
        data, success = self.data_manager.undo()
        if success:
            self.plot_manager.selected_indices = []
            self.plot_manager.update_plot(data)
            print("Undo performed, selection cleared")
        self.plot_manager.update_status()

    def on_redo(self, event):
        if self.plot_manager is None:
            return
        data, success = self.data_manager.redo()
        if success:
            self.plot_manager.selected_indices = []
            self.plot_manager.update_plot(data)
            print("Redo performed")
        self.plot_manager.update_status()

    def on_finalize_draw(self, event):
        if not self.draw_mode:
            return
        self.curve_manager.finalize_draw(self.selected_id)
        self.plot_manager.selected_indices = []
        self.update_point_sizes()
        print(f"Finalized {'curve' if self.curve_manager.is_curve else 'line'} with ID {self.selected_id}")
        self.plot_manager.update_status()
