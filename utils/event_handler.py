import time

import matplotlib.pyplot as plt
import numpy as np
from matplotlib.widgets import Button

from DataVisualizationEditingTool.utils.curve_manager import CurveManager
from DataVisualizationEditingTool.utils.data_loader import DataLoader


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
        self.merge_point_1 = None
        self.merge_point_2 = None
        self.merge_lane_1 = None
        self.merge_lane_2 = None
        self.merge_point_1_type = None
        self.merge_point_2_type = None
        self.remove_above_mode = False
        self.remove_below_mode = False
        self.remove_point_idx = None
        self.remove_lane_id = None
        self.buttons = {}
        self.status_timeout = 5
        self.last_status_time = 0

    def set_plot_manager(self, plot_manager):
        self.plot_manager = plot_manager
        self.curve_manager = CurveManager(self.data_manager, self.plot_manager)
        self.fig = self.plot_manager.fig
        self.setup_event_handlers()
        self.setup_buttons()
        self.update_button_states()

    def setup_event_handlers(self):
        self.fig.canvas.mpl_connect('button_press_event', self.on_click)
        self.fig.canvas.mpl_connect('key_press_event', self.on_key)
        self.fig.canvas.mpl_connect('pick_event', self.on_pick)
        self.plot_manager.rs.onselect = self.on_select

    def on_select_mode(self, event):
        self.toggle_mode(event)
        self.update_status("Switched to Select Mode" if self.selection_mode else "Switched to Draw Mode")

    def setup_buttons(self):
        ax_toolbar = plt.axes([0.01, 0.95, 0.98, 0.05])
        button_labels = [
            'Select Mode', 'Draw', 'Line', 'Smooth', 'Confirm Start', 'Confirm End',
            'Cancel', 'Clear Selection', 'Save', 'Merge Lanes', 'Export', 'Toggle Grid',
            'Remove Above', 'Remove Below'
        ]
        self.buttons = {}
        for i, label in enumerate(button_labels):
            btn_ax = plt.axes([0.01 + i * 0.07, 0.06, 0.06, 0.04], facecolor='lightgray',
                              transform=ax_toolbar.transAxes)
            self.buttons[label] = Button(btn_ax, label)
            method_name = f'on_{label.lower().replace(" ", "_")}'
            if hasattr(self, method_name):
                self.buttons[label].on_clicked(getattr(self, method_name))
            else:
                print(f"Warning: No method '{method_name}' found for button '{label}'. Skipping callback.")
                self.buttons[label].on_clicked(
                    lambda x, l=label: print(f"Button '{l}' clicked, but no action defined."))
        self.fig.canvas.draw()

    def update_button_states(self):
        # Enable/Disable buttons based on current mode
        self.buttons['Draw'].eventson = not self.selection_mode
        self.buttons['Draw'].ax.set_facecolor('white' if not self.selection_mode else 'lightgray')
        self.buttons['Draw'].label.set_color('black' if not self.selection_mode else 'gray')

        self.buttons['Line'].eventson = self.draw_mode
        self.buttons['Line'].ax.set_facecolor('white' if self.draw_mode else 'lightgray')
        self.buttons['Line'].label.set_color('black' if self.draw_mode else 'gray')

        self.buttons['Smooth'].eventson = self.selection_mode and self.plot_manager.selected_indices
        self.buttons['Smooth'].ax.set_facecolor(
            'white' if self.selection_mode and self.plot_manager.selected_indices else 'lightgray')
        self.buttons['Smooth'].label.set_color(
            'black' if self.selection_mode and self.plot_manager.selected_indices else 'gray')

        self.buttons['Confirm Start'].eventson = self.smoothing_point_selection
        self.buttons['Confirm Start'].ax.set_facecolor('white' if self.smoothing_point_selection else 'lightgray')
        self.buttons['Confirm Start'].label.set_color('black' if self.smoothing_point_selection else 'gray')

        self.buttons['Confirm End'].eventson = self.smoothing_point_selection and self.smoothing_start_idx is not None
        self.buttons['Confirm End'].ax.set_facecolor(
            'white' if self.smoothing_point_selection and self.smoothing_start_idx is not None else 'lightgray')
        self.buttons['Confirm End'].label.set_color(
            'black' if self.smoothing_point_selection and self.smoothing_start_idx is not None else 'gray')

        self.buttons['Cancel'].eventson = any([self.smoothing_point_selection, self.merge_mode, self.draw_mode,
                                               self.remove_above_mode, self.remove_below_mode])
        self.buttons['Cancel'].ax.set_facecolor('white' if self.buttons['Cancel'].eventson else 'lightgray')
        self.buttons['Cancel'].label.set_color('black' if self.buttons['Cancel'].eventson else 'gray')

        self.buttons['Export'].eventson = bool(self.plot_manager.selected_indices)
        self.buttons['Export'].ax.set_facecolor('white' if self.plot_manager.selected_indices else 'lightgray')
        self.buttons['Export'].label.set_color('black' if self.plot_manager.selected_indices else 'gray')

        self.buttons['Remove Above'].eventson = not (
                    self.remove_below_mode or self.smoothing_point_selection or self.merge_mode)
        self.buttons['Remove Above'].ax.set_facecolor('white' if self.buttons['Remove Above'].eventson else 'lightgray')
        self.buttons['Remove Above'].label.set_color('black' if self.buttons['Remove Above'].eventson else 'gray')

        self.buttons['Remove Below'].eventson = not (
                    self.remove_above_mode or self.smoothing_point_selection or self.merge_mode)
        self.buttons['Remove Below'].ax.set_facecolor('white' if self.buttons['Remove Below'].eventson else 'lightgray')
        self.buttons['Remove Below'].label.set_color('black' if self.buttons['Remove Below'].eventson else 'gray')

        self.fig.canvas.draw_idle()

    # Add missing callback methods
    def on_draw(self, event):
        self.selection_mode = False
        self.draw_mode = True
        self.plot_manager.rs.set_active(False)
        self.update_status("Entered Draw Mode")
        self.update_button_states()

    def on_line(self, event):
        if not self.draw_mode:
            self.update_status("Enter Draw Mode first")
            return
        self.curve_manager.is_curve = False
        self.update_status("Drawing Line")
        self.update_draw_line()

    def on_smooth(self, event):
        if not self.selection_mode or not self.plot_manager.selected_indices:
            self.update_status("Select points in Selection Mode")
            return
        self.smoothing_selected_indices = self.plot_manager.selected_indices
        self.smoothing_lane_id = int(self.data_manager.data[self.plot_manager.selected_indices[0], -1])
        self.smoothing_point_selection = True
        self.smoothing_start_idx = None
        self.smoothing_end_idx = None
        self.update_point_sizes()
        self.update_button_states()
        self.update_status("Click to select smoothing start point")

    def on_cancel(self, event):
        self.on_cancel_operation(event)

    def on_save(self, event):
        self.save_data(event)

    def on_merge_lanes(self, event):
        self.merge_lanes(event)

    def on_export(self, event):
        self.export_selected(event)

    def on_toggle_grid(self, event):
        self.toggle_grid(event)

    def update_point_sizes(self, val=None):
        if self.plot_manager is None or val is None:
            val = float(self.plot_manager.text_point_size.text) if self.plot_manager.text_point_size.text else 10
        try:
            val = float(val)
            if val < 1:
                val = 1
            elif val > 100:
                val = 100
            for plot_idx, sc in enumerate(self.plot_manager.lane_scatter_plots):
                indices = self.plot_manager.indices[plot_idx]
                if len(indices) == 0:
                    continue
                lane_id = int(self.data_manager.data[indices[0], -1])
                base_size = val if self.plot_manager.highlighted_lane == lane_id else val / 2
                sizes = np.full(len(indices), base_size, dtype=float)
                for local_idx, global_idx in enumerate(indices):
                    if self.merge_mode:
                        if global_idx == self.merge_point_1:
                            sizes[local_idx] = 100
                        elif global_idx == self.merge_point_2:
                            sizes[local_idx] = 80
                    elif self.smoothing_point_selection:
                        if global_idx == self.smoothing_start_idx:
                            sizes[local_idx] = 100
                        elif global_idx == self.smoothing_end_idx:
                            sizes[local_idx] = 80
                        elif global_idx in self.smoothing_selected_indices:
                            sizes[local_idx] = 50
                    elif (self.remove_above_mode or self.remove_below_mode) and global_idx == self.remove_point_idx:
                        sizes[local_idx] = 100
                    elif global_idx in self.plot_manager.selected_indices:
                        sizes[local_idx] = val * 1.5
                sc.set_sizes(sizes)
            self.plot_manager.fig.canvas.draw_idle()
            self.plot_manager.fig.canvas.flush_events()
            self.update_button_states()
            self.update_status(f"Point size set to {val}")
        except ValueError:
            self.update_status("Invalid point size, using 10")
            self.plot_manager.text_point_size.set_val('10')
            self.update_point_sizes(10)

    def update_smoothing_weight(self, val=None):
        if self.plot_manager is None or val is None:
            val = float(self.plot_manager.text_weight.text) if self.plot_manager.text_weight.text else 20
        try:
            val = float(val)
            if val < 1:
                val = 1
            elif val > 100:
                val = 100
            self.curve_manager.smoothing_weight = val
            self.plot_manager.text_weight.set_text(str(val))
            self.update_status(f"Smoothing weight set to {val}")
            if self.smoothing_point_selection and self.smoothing_start_idx and self.smoothing_end_idx:
                preview_points = self.curve_manager.preview_smooth(
                    self.smoothing_selected_indices,
                    self.smoothing_lane_id,
                    self.smoothing_start_idx,
                    self.smoothing_end_idx
                )
                if preview_points is not None and self.smoothing_preview_line:
                    self.smoothing_preview_line.remove()
                    self.smoothing_preview_line = self.plot_manager.ax.plot(
                        preview_points[:, 0], preview_points[:, 1], 'b--', alpha=0.5, label='Preview')[0]
                    self.plot_manager.ax.legend()
                    self.plot_manager.fig.canvas.draw_idle()
        except ValueError:
            self.update_status("Invalid weight, using 20")
            self.plot_manager.text_weight.set_text('20')
            self.update_smoothing_weight(20)

    def update_smoothness(self, val=None):
        if self.plot_manager is None or val is None:
            val = float(self.plot_manager.text_smoothness.text) if self.plot_manager.text_smoothness.text else 1.0
        try:
            val = float(val)
            if val < 0.1:
                val = 0.1
            elif val > 30.0:
                val = 30.0
            self.plot_manager.text_smoothness.set_val(str(val))
            self.update_status(f"Smoothness set to {val}")
            # Update preview if smoothing is active
            if self.smoothing_point_selection and self.smoothing_start_idx and self.smoothing_end_idx:
                preview_points = self.curve_manager.preview_smooth(
                    self.smoothing_selected_indices,
                    self.smoothing_lane_id,
                    self.smoothing_start_idx,
                    self.smoothing_end_idx
                )
                if preview_points is not None and self.smoothing_preview_line:
                    self.smoothing_preview_line.remove()
                    self.smoothing_preview_line = self.plot_manager.ax.plot(
                        preview_points[:, 0], preview_points[:, 1], 'b--', alpha=0.5, label='Preview')[0]
                    self.plot_manager.ax.legend()
                    self.plot_manager.fig.canvas.draw_idle()
        except ValueError:
            self.update_status("Invalid smoothness, using 1.0")
            self.plot_manager.text_smoothness.set_val('1.0')
            self.update_smoothness(1.0)

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
        self.selection_mode = False
        self.draw_mode = not self.draw_mode
        self.plot_manager.rs.set_active(False)
        self.buttons['toggle'].label.set_text('Select Mode')
        self.buttons['toggle'].color = 'lightcoral'
        if not self.draw_mode:
            self.id_set = True
            self.clear_smoothing_state()
            self.clear_remove_state()
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
        self.update_button_states()
        self.update_status()

    def on_toggle_linecurve(self, event):
        if not self.draw_mode:
            print("Must be in Draw Mode to toggle line/curve")
            self.update_status("Enter Draw Mode first")
            return
        self.curve_manager.is_curve = not self.curve_manager.is_curve
        self.buttons['linecurve'].label.set_text('Curve' if self.curve_manager.is_curve else 'Line')
        self.curve_manager.update_draw_line()
        print(f"Drawing {'curve' if self.curve_manager.is_curve else 'line'}")
        self.update_status()

    def on_straighten(self, event):
        if not self.selection_mode or not self.plot_manager.selected_indices:
            print("Must be in Selection Mode with points selected to smooth")
            self.update_status("Select points in Selection Mode")
            return
        self.smoothing_selected_indices = self.plot_manager.selected_indices
        self.smoothing_lane_id = self.selected_id
        self.smoothing_point_selection = True
        self.smoothing_start_idx = None
        self.smoothing_end_idx = None
        self.update_point_sizes()
        self.update_button_states()
        print("Please click on the starting point for smoothing")
        self.update_status("Click to select smoothing start point")

    def on_confirm_start(self, event):
        if not self.smoothing_point_selection or self.smoothing_start_idx is None:
            print("Please select the starting point first")
            self.update_status("Select start point first")
            return
        print(f"Confirmed start point (index {self.smoothing_start_idx})")
        self.update_point_sizes()
        self.update_status("Click to select smoothing end point")

    def on_confirm_end(self, event):
        if not self.smoothing_point_selection or self.smoothing_start_idx is None or self.smoothing_end_idx is None:
            print("Please select both start and end points")
            self.update_status("Select both start and end points")
            return
        print(f"End point confirmed (index {self.smoothing_end_idx})")
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
            self.update_status(f"Smoothed {len(new_indices)} points")
        else:
            self.plot_manager.selected_indices = []
            self.update_point_sizes()
            print("Smoothing failed, selection cleared")
            self.update_status("Smoothing failed")
        self.update_button_states()

    def on_remove_above(self, event):
        if self.remove_below_mode or self.smoothing_point_selection or self.merge_mode:
            print("Cannot enter Remove Above mode while other operations are active")
            self.update_status("Cancel other operations first")
            return
        self.remove_above_mode = True
        self.remove_below_mode = False
        self.remove_point_idx = None
        self.remove_lane_id = None
        self.plot_manager.rs.set_active(False)
        self.update_point_sizes()
        self.update_button_states()
        print("Please click on a point to remove points above it in the same lane")
        self.update_status("Click to select point for Remove Above")

    def on_remove_below(self, event):
        if self.remove_above_mode or self.smoothing_point_selection or self.merge_mode:
            print("Cannot enter Remove Below mode while other operations are active")
            self.update_status("Cancel other operations first")
            return
        self.remove_below_mode = True
        self.remove_above_mode = False
        self.remove_point_idx = None
        self.remove_lane_id = None
        self.plot_manager.rs.set_active(False)
        self.update_point_sizes()
        self.update_button_states()
        print("Please click on a point to remove points below it in the same lane")
        self.update_status("Click to select point for Remove Below")

    def on_cancel_operation(self, event):
        print("Operation canceled")
        self.clear_smoothing_state()
        self.clear_merge_state()
        self.clear_remove_state()
        self.draw_mode = False
        self.selection_mode = False
        self.plot_manager.rs.set_active(False)
        self.curve_manager.draw_points = []
        if self.curve_manager.current_line:
            self.curve_manager.current_line.remove()
            self.curve_manager.current_line = None
            self.plot_manager.fig.canvas.draw_idle()
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
        self.merge_mode = False
        self.merge_point_1 = None
        self.merge_point_2 = None
        self.merge_lane_1 = None
        self.merge_lane_2 = None
        self.merge_point_1_type = None
        self.merge_point_2_type = None
        self.update_status()

    def clear_remove_state(self):
        self.remove_above_mode = False
        self.remove_below_mode = False
        self.remove_point_idx = None
        self.remove_lane_id = None

    def merge_lanes(self, event):
        unique_lanes = np.unique(self.data_manager.data[:, -1])
        if len(unique_lanes) <= 1:
            print("Only one lane present, no merging needed")
            self.update_status("Only one lane present")
            self.clear_merge_state()
            return
        self.merge_mode = True
        self.merge_point_1 = None
        self.merge_point_2 = None
        self.merge_lane_1 = None
        self.merge_lane_2 = None
        self.merge_point_1_type = None
        self.merge_point_2_type = None
        print("Please select first point (start or end)")
        self.update_status("Select first point (start or end)")
        self.update_point_sizes()

    def finalize_merge(self):
        if self.merge_point_1 is None or self.merge_point_2 is None or self.merge_lane_1 == self.merge_lane_2:
            print("Two different lanes must be selected for merging")
            self.update_status("Select two different lanes")
            self.clear_merge_state()
            return
        self.merge_point_1, self.merge_point_2 = self.data_manager.merge_lanes(
            self.merge_lane_1, self.merge_lane_2,
            self.merge_point_1, self.merge_point_2,
            self.merge_point_1_type, self.merge_point_2_type
        )
        self.data_manager.save_all_lanes()
        self.data_manager.clear_data()
        temp_loader = DataLoader("workspace-Temp")
        data, file_names = temp_loader.load_data()
        self.data_manager.__init__(data, file_names)
        self.plot_manager.selected_indices = []
        self.plot_manager.file_names = file_names
        self.plot_manager.update_plot(self.data_manager.data)
        print(f"Merged lane {self.merge_lane_2} into lane {self.merge_lane_1}")
        self.clear_merge_state()
        self.update_point_sizes()
        self.update_status(f"Merged lane {self.merge_lane_2} into lane {self.merge_lane_1}")

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
            selected_points = self.data_manager.data[np.array(self.plot_manager.selected_indices, dtype=int)]
            filename = f"selected_points_{int(time.time())}.npy"
            np.save(filename, selected_points[:, :3])
            print(f"Exported {len(selected_points)} points to {filename}")
            self.update_status(f"Exported {len(selected_points)} points")
        except Exception as e:
            print(f"Error exporting points: {e}")
            self.update_status("Export failed")

    def on_click(self, event):
        if self.plot_manager is None or event.inaxes != self.plot_manager.ax or event.button != 1:
            return
        click_x, click_y = event.xdata, event.ydata
        distances = np.sqrt(
            (self.data_manager.data[:, 0] - click_x) ** 2 +
            (self.data_manager.data[:, 1] - click_y) ** 2
        )
        closest_idx = np.argmin(distances)
        lane_id = int(self.data_manager.data[closest_idx, -1])

        if self.remove_above_mode:
            self.remove_point_idx = closest_idx
            self.remove_lane_id = lane_id
            self.data_manager.remove_points_above(self.remove_point_idx, self.remove_lane_id)
            self.plot_manager.update_plot(self.data_manager.data)
            self.clear_remove_state()
            self.update_point_sizes()
            self.update_button_states()
            self.update_status(f"Removed points above index {closest_idx} in lane {lane_id}")
            return

        if self.remove_below_mode:
            self.remove_point_idx = closest_idx
            self.remove_lane_id = lane_id
            self.data_manager.remove_points_below(self.remove_point_idx, self.remove_lane_id)
            self.plot_manager.update_plot(self.data_manager.data)
            self.clear_remove_state()
            self.update_point_sizes()
            self.update_button_states()
            self.update_status(f"Removed points below index {closest_idx} in lane {lane_id}")
            return

        if self.merge_mode:
            lane_indices = np.where(self.data_manager.data[:, -1] == lane_id)[0]
            lane_data = self.data_manager.data[lane_indices]
            min_idx = lane_data[:, 4].argmin()
            max_idx = lane_data[:, 4].argmax()
            point_type = 'start' if closest_idx == lane_indices[min_idx] else 'end' if closest_idx == lane_indices[
                max_idx] else None

            if point_type is None:
                print("Please select a start or end point")
                self.update_status("Select a start or end point")
                return

            if self.merge_point_1 is None:
                self.merge_point_1 = closest_idx
                self.merge_lane_1 = lane_id
                self.merge_point_1_type = point_type
                print(f"Selected {point_type} point in lane {lane_id} (index {closest_idx})")
                self.update_status("Select second point in different lane")
                self.update_point_sizes()
                self.plot_manager.fig.canvas.draw_idle()
            elif self.merge_point_2 is None and lane_id != self.merge_lane_1:
                self.merge_point_2 = closest_idx
                self.merge_lane_2 = lane_id
                self.merge_point_2_type = point_type
                print(f"Selected {point_type} point in lane {lane_id} (index {closest_idx})")
                self.finalize_merge()
            return

        if self.smoothing_point_selection:
            selected_points = self.data_manager.data[self.smoothing_selected_indices, :2]
            distances = np.sqrt((selected_points[:, 0] - click_x) ** 2 + (selected_points[:, 1] - click_y) ** 2)
            closest_idx = np.argmin(distances)
            global_idx = self.smoothing_selected_indices[closest_idx]
            if self.smoothing_start_idx is None:
                self.smoothing_start_idx = global_idx
                self.update_point_sizes()
                print(f"Start point selected (index {self.smoothing_start_idx})")
                self.update_status("Confirm start or select end point")
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
                print(f"End point selected (index {self.smoothing_end_idx})")
                self.update_status("Confirm end or cancel")
            return

        if self.draw_mode:
            self.curve_manager.add_draw_point(event.xdata, event.ydata)
            print(f"Added point to {'curve' if self.curve_manager.is_curve else 'line'}")
            self.update_status()
            return

        if self.selection_mode:
            return

        self.plot_manager.selected_indices = []
        self.update_point_sizes()
        self.data_manager.add_point(event.xdata, event.ydata, self.selected_id)
        self.plot_manager.update_plot(self.data_manager.data)
        print(f"Added point with ID {self.selected_id} ({self.data_manager.file_names[self.selected_id]})")
        self.update_status("Point added")

    def on_pick(self, event):
        if self.plot_manager is None or event.mouseevent.button != 3 or self.plot_manager.rs.active:
            return
        if not self.selection_mode:
            self.plot_manager.selected_indices = []
            self.update_point_sizes()
        artist = event.artist
        if artist not in self.plot_manager.lane_scatter_plots:
            return
        ind = event.ind[0]
        file_index = self.plot_manager.lane_scatter_plots.index(artist)
        global_ind = self.plot_manager.indices[file_index][ind]
        self.data_manager.delete_points([global_ind])
        self.plot_manager.selected_indices = [i for i in self.plot_manager.selected_indices if i != global_ind]
        self.plot_manager.update_plot(self.data_manager.data)
        self.update_status("Point deleted")

    def on_select(self, eclick, erelease):
        if not self.selection_mode:
            return
        try:
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
            self.update_status(f"Selected {len(self.plot_manager.selected_indices)} points")
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
        elif key in '123456789':
            print("Lane ID selection disabled; use default ID 0 or Merge Lanes button")
            self.update_status("Lane ID selection disabled")

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
        self.update_button_states()
        self.update_status("Entered add/delete mode")

    def on_delete(self, event):
        if self.plot_manager is None or not self.selection_mode or not self.plot_manager.selected_indices:
            return
        deleted_indices = self.plot_manager.selected_indices
        self.data_manager.delete_points(deleted_indices)
        self.plot_manager.selected_indices = []
        self.plot_manager.update_plot(self.data_manager.data)
        print(f"Deleted {len(deleted_indices)} points")
        self.update_status(f"Deleted {len(deleted_indices)} points")

    def on_undo(self, event):
        if self.plot_manager is None:
            return
        data, success = self.data_manager.undo()
        if success:
            self.plot_manager.selected_indices = []
            self.plot_manager.update_plot(data)
            print("Undo performed")
            self.update_status("Undo performed")
        else:
            self.update_status("Nothing to undo")

    def on_redo(self, event):
        if self.plot_manager is None:
            return
        data, success = self.data_manager.redo()
        if success:
            self.plot_manager.selected_indices = []
            self.plot_manager.update_plot(data)
            print("Redo performed")
            self.update_status("Redo performed")
        else:
            self.update_status("Nothing to redo")

    def on_finalize_draw(self, event):
        if not self.draw_mode:
            return
        self.curve_manager.finalize_draw(self.selected_id)
        self.plot_manager.selected_indices = []
        self.update_point_sizes()
        print(f"Finalized {'curve' if self.curve_manager.is_curve else 'line'} with ID {self.selected_id}")
        self.update_status("Drawing finalized")

    def update_status(self, message=""):
        try:
            self.plot_manager.update_status(message)
            self.last_status_time = time.time()
            if message:
                # Use Tkinter's after method if available, otherwise update immediately
                try:
                    self.fig.canvas.manager.window.after(
                        int(self.status_timeout * 1000),
                        lambda: self._clear_status_if_timeout()
                    )
                except AttributeError:
                    # Fallback for non-Tkinter backends or environments without after
                    self.fig.canvas.draw_idle()
        except Exception as e:
            print(f"Error updating status: {e}")

    def _clear_status_if_timeout(self):
        try:
            if time.time() - self.last_status_time >= self.status_timeout:
                self.plot_manager.update_status("")
                self.fig.canvas.draw_idle()
        except Exception as e:
            print(f"Error clearing status: {e}")
