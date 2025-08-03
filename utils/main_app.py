import sys
import time

import matplotlib.pyplot as plt
import numpy as np
from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import (
    QMainWindow, QDockWidget, QWidget, QVBoxLayout, QHBoxLayout, QPushButton,
    QRadioButton, QGroupBox, QLineEdit, QLabel, QComboBox,
    QApplication, QStatusBar, QStackedWidget
)
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure

from curve_manager import CurveManager
from data_loader import DataLoader
# Import provided classes (assumed to be in the same directory)
from data_manager import DataManager


class PlotCanvas(FigureCanvas):
    def __init__(self, parent=None, width=12, height=8, dpi=100):
        fig = Figure(figsize=(width, height), dpi=dpi)
        self.ax = fig.add_subplot(111)
        super().__init__(fig)
        self.setParent(parent)
        self.data_manager = None
        self.file_names = []
        self.D = 1.0
        self.selected_indices = []
        self.highlighted_lane = None
        self.grid_visible = False
        self.tooltip = self.ax.text(0, 0, '', bbox=dict(facecolor='white', alpha=0.8), visible=False)
        self.nearest_point = None
        self.lane_scatter_plots = []
        self.start_point_plots = []
        self.extra_scatter_plots = []
        self.indices = []

    def update_plot(self, data, selected_indices=None, merge_points=None, smoothing_preview=None):
        self.ax.clear()
        self.lane_scatter_plots = []
        self.start_point_plots = []
        self.extra_scatter_plots = []
        self.indices = []
        self.tooltip.set_visible(False)
        if self.nearest_point:
            self.nearest_point.remove()
            self.nearest_point = None

        if selected_indices is not None:
            self.selected_indices = selected_indices

        if data.size == 0:
            self.ax.set_title("No Data")
            self.draw()
            return

        unique_lane_ids = np.unique(data[:, -1])
        colors = plt.cm.get_cmap('tab10')(np.linspace(0, 1, max(len(unique_lane_ids), 10)))

        for lane_id in unique_lane_ids:
            mask = data[:, -1] == lane_id
            lane_data = data[mask]
            if len(lane_data) > 0:
                label = self.file_names[int(lane_id)] if int(lane_id) < len(self.file_names) else f"Lane {lane_id}"
                size = 50 if self.highlighted_lane == lane_id else 20
                sc = self.ax.scatter(lane_data[:, 0], lane_data[:, 1], s=size, label=label,
                                     color=colors[int(lane_id)], marker='o')
                self.lane_scatter_plots.append(sc)
                self.indices.append(np.where(mask)[0])

                start_idx = lane_data[:, 4].argmin()
                start_point = lane_data[start_idx]
                start_sc = self.ax.scatter(start_point[0], start_point[1], s=100, color=colors[int(lane_id)],
                                           marker='s', label=f'Lane {lane_id} Start')
                self.start_point_plots.append(start_sc)

        if merge_points:
            for idx, point_type, lane_id in merge_points:
                point = data[idx]
                marker = '>' if point_type == 'end' else '<'
                color = 'purple' if merge_points.index((idx, point_type, lane_id)) == 0 else 'orange'
                sc = self.ax.scatter(point[0], point[1], s=150, color=color, marker=marker,
                                     label=f'Lane {lane_id} {point_type}')
                self.extra_scatter_plots.append(sc)

        if smoothing_preview is not None:
            self.ax.plot(smoothing_preview[:, 0], smoothing_preview[:, 1], 'b--', alpha=0.5, label='Preview')

        if self.selected_indices:
            selected_points = data[np.array(self.selected_indices, dtype=int)]
            sc = self.ax.scatter(selected_points[:, 0], selected_points[:, 1], s=80, color='red', marker='o',
                                 label='Selected')
            self.extra_scatter_plots.append(sc)

        self.ax.set_xlabel('X')
        self.ax.set_ylabel('Y')
        self.ax.set_title('Lane Data Visualization')
        self.ax.grid(self.grid_visible)
        self.ax.legend()
        self.draw()

    def on_motion(self, event):
        if event.inaxes != self.ax or self.data_manager.data.size == 0:
            self.tooltip.set_visible(False)
            if self.nearest_point:
                self.nearest_point.remove()
                self.nearest_point = None
            self.draw()
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
                self.tooltip.set_visible(True)
                if self.nearest_point:
                    self.nearest_point.remove()
                self.nearest_point = self.ax.scatter(point[0], point[1], s=60, color='cyan', marker='o', alpha=0.5)
            else:
                self.tooltip.set_visible(False)
                if self.nearest_point:
                    self.nearest_point.remove()
                    self.nearest_point = None
            self.draw()
        except Exception as e:
            print(f"Error during motion: {e}")


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Lane Data Visualization and Editing Tool")
        self.setGeometry(100, 100, 1200, 800)

        # Initialize Data
        loader = DataLoader("../workspace-Temp")
        data, file_names = loader.load_data()
        self.data_manager = DataManager(data, file_names)
        self.curve_manager = CurveManager(self.data_manager, self)

        # Canvas
        self.canvas = PlotCanvas(self)
        self.canvas.data_manager = self.data_manager
        self.canvas.file_names = file_names
        self.canvas.D = loader.D
        self.setCentralWidget(self.canvas)

        # Control Panel
        self.control_dock = QDockWidget("Controls", self)
        self.control_widget = QWidget()
        self.control_layout = QVBoxLayout()
        self.control_widget.setLayout(self.control_layout)
        self.control_dock.setWidget(self.control_widget)
        self.addDockWidget(Qt.DockWidgetArea.LeftDockWidgetArea, self.control_dock)

        # Mode Selection
        self.mode_group = QGroupBox("Mode")
        self.mode_layout = QVBoxLayout()
        self.mode_select = QRadioButton("Select")
        self.mode_add_delete = QRadioButton("Add/Delete")
        self.mode_draw = QRadioButton("Draw")
        self.mode_merge = QRadioButton("Merge Lanes")
        self.mode_remove_above = QRadioButton("Remove Above")
        self.mode_remove_below = QRadioButton("Remove Below")
        self.mode_smooth = QRadioButton("Smooth")
        self.mode_select.setChecked(True)
        for mode in [self.mode_select, self.mode_add_delete, self.mode_draw, self.mode_merge,
                     self.mode_remove_above, self.mode_remove_below, self.mode_smooth]:
            self.mode_layout.addWidget(mode)
            mode.toggled.connect(self.on_mode_change)
        self.mode_group.setLayout(self.mode_layout)
        self.control_layout.addWidget(self.mode_group)

        # Contextual Controls
        self.context_stack = QStackedWidget()
        self.control_layout.addWidget(self.context_stack)

        # Select Mode Controls
        self.select_controls = QWidget()
        self.select_layout = QVBoxLayout()
        self.select_controls.setLayout(self.select_layout)
        self.context_stack.addWidget(self.select_controls)

        # Draw Mode Controls
        self.draw_controls = QWidget()
        self.draw_layout = QVBoxLayout()
        self.draw_linecurve = QPushButton("Line")
        self.draw_linecurve.clicked.connect(self.on_toggle_linecurve)
        self.draw_layout.addWidget(self.draw_linecurve)
        self.draw_lane_id = QComboBox()
        self.draw_lane_id.addItems([f"Lane {i}" for i in range(len(file_names))] + ["New Lane"])
        self.draw_layout.addWidget(QLabel("Lane ID:"))
        self.draw_layout.addWidget(self.draw_lane_id)
        self.draw_controls.setLayout(self.draw_layout)
        self.context_stack.addWidget(self.draw_controls)

        # Smooth Mode Controls
        self.smooth_controls = QWidget()
        self.smooth_layout = QVBoxLayout()
        self.smooth_weight = QLineEdit("20")
        self.smooth_weight.textChanged.connect(self.update_smoothing_weight)
        self.smooth_layout.addWidget(QLabel("Smoothing Weight:"))
        self.smooth_layout.addWidget(self.smooth_weight)
        self.smooth_smoothness = QLineEdit("1.0")
        self.smooth_smoothness.textChanged.connect(self.update_smoothness)
        self.smooth_layout.addWidget(QLabel("Smoothness:"))
        self.smooth_layout.addWidget(self.smooth_smoothness)
        self.smooth_start = QPushButton("Confirm Start")
        self.smooth_start.clicked.connect(self.on_confirm_start)
        self.smooth_layout.addWidget(self.smooth_start)
        self.smooth_end = QPushButton("Confirm End")
        self.smooth_end.clicked.connect(self.on_confirm_end)
        self.smooth_layout.addWidget(self.smooth_end)
        self.smooth_controls.setLayout(self.smooth_layout)
        self.context_stack.addWidget(self.smooth_controls)

        # Merge Mode Controls
        self.merge_controls = QWidget()
        self.merge_layout = QVBoxLayout()
        self.merge_status = QLabel("Select first point (start or end)")
        self.merge_layout.addWidget(self.merge_status)
        self.merge_controls.setLayout(self.merge_layout)
        self.context_stack.addWidget(self.merge_controls)

        # Remove Mode Controls
        self.remove_controls = QWidget()
        self.remove_layout = QVBoxLayout()
        self.remove_status = QLabel("Click a point to remove above/below")
        self.remove_layout.addWidget(self.remove_status)
        self.remove_controls.setLayout(self.remove_layout)
        self.context_stack.addWidget(self.remove_controls)

        # Common Controls
        self.common_group = QGroupBox("Common Actions")
        self.common_layout = QHBoxLayout()
        self.save_btn = QPushButton("Save")
        self.save_btn.clicked.connect(self.save_data)
        self.export_btn = QPushButton("Export Selected")
        self.export_btn.clicked.connect(self.export_selected)
        self.undo_btn = QPushButton("Undo")
        self.undo_btn.clicked.connect(self.on_undo)
        self.redo_btn = QPushButton("Redo")
        self.redo_btn.clicked.connect(self.on_redo)
        self.grid_btn = QPushButton("Toggle Grid")
        self.grid_btn.clicked.connect(self.toggle_grid)
        self.clear_btn = QPushButton("Clear Selection")
        self.clear_btn.clicked.connect(self.on_clear_selection)
        for btn in [self.save_btn, self.export_btn, self.undo_btn, self.redo_btn, self.grid_btn, self.clear_btn]:
            self.common_layout.addWidget(btn)
        self.common_group.setLayout(self.common_layout)
        self.control_layout.addWidget(self.common_group)

        # Status Bar
        self.status_bar = QStatusBar()
        self.setStatusBar(self.status_bar)

        # State Variables
        self.mode = "select"
        self.draw_is_curve = False
        self.smoothing_point_selection = False
        self.smoothing_start_idx = None
        self.smoothing_end_idx = None
        self.smoothing_selected_indices = None
        self.smoothing_lane_id = None
        self.merge_point_1 = None
        self.merge_point_2 = None
        self.merge_lane_1 = None
        self.merge_lane_2 = None
        self.merge_point_1_type = None
        self.merge_point_2_type = None
        self.remove_point_idx = None
        self.remove_lane_id = None
        self.selected_id = 0

        # Connect Canvas Events
        self.canvas.mpl_connect('button_press_event', self.on_click)
        self.canvas.mpl_connect('motion_notify_event', self.canvas.on_motion)
        self.canvas.mpl_connect('scroll_event', self.on_scroll)

        # Initial Plot
        self.canvas.update_plot(self.data_manager.data)
        self.update_button_states()

    def on_mode_change(self):
        self.clear_state()
        if self.mode_select.isChecked():
            self.mode = "select"
            self.context_stack.setCurrentWidget(self.select_controls)
        elif self.mode_add_delete.isChecked():
            self.mode = "add_delete"
            self.context_stack.setCurrentWidget(self.select_controls)
        elif self.mode_draw.isChecked():
            self.mode = "draw"
            self.context_stack.setCurrentWidget(self.draw_controls)
        elif self.mode_merge.isChecked():
            self.mode = "merge"
            self.context_stack.setCurrentWidget(self.merge_controls)
            self.merge_status.setText("Select first point (start or end)")
        elif self.mode_remove_above.isChecked():
            self.mode = "remove_above"
            self.context_stack.setCurrentWidget(self.remove_controls)
            self.remove_status.setText("Click a point to remove above")
        elif self.mode_remove_below.isChecked():
            self.mode = "remove_below"
            self.context_stack.setCurrentWidget(self.remove_controls)
            self.remove_status.setText("Click a point to remove below")
        elif self.mode_smooth.isChecked():
            self.mode = "smooth"
            self.context_stack.setCurrentWidget(self.smooth_controls)
            if self.canvas.selected_indices:
                self.smoothing_selected_indices = self.canvas.selected_indices
                self.smoothing_lane_id = int(self.data_manager.data[self.canvas.selected_indices[0], -1])
                self.smoothing_point_selection = True
                self.status_bar.showMessage("Click to select smoothing start point")
        self.update_button_states()
        self.status_bar.showMessage(f"Mode: {self.mode.replace('_', ' ').title()}")

    def clear_state(self):
        self.smoothing_point_selection = False
        self.smoothing_start_idx = None
        self.smoothing_end_idx = None
        self.smoothing_selected_indices = None
        self.smoothing_lane_id = None
        self.merge_point_1 = None
        self.merge_point_2 = None
        self.merge_lane_1 = None
        self.merge_lane_2 = None
        self.merge_point_1_type = None
        self.merge_point_2_type = None
        self.remove_point_idx = None
        self.remove_lane_id = None
        self.curve_manager.draw_points = []
        if self.curve_manager.current_line:
            self.curve_manager.current_line.remove()
            self.curve_manager.current_line = None
        if self.mode != "select" and self.canvas.selected_indices:
            self.canvas.selected_indices = []
        self.canvas.update_plot(self.data_manager.data)
        self.update_button_states()

    def update_button_states(self):
        self.export_btn.setEnabled(bool(self.canvas.selected_indices))
        self.smooth_start.setEnabled(self.smoothing_point_selection and self.smoothing_start_idx is not None)
        self.smooth_end.setEnabled(self.smoothing_point_selection and self.smoothing_start_idx is not None and
                                   self.smoothing_end_idx is not None)
        self.clear_btn.setEnabled(bool(self.canvas.selected_indices) or self.smoothing_point_selection or
                                  self.mode in ["merge", "remove_above", "remove_below", "draw"])

    def on_toggle_linecurve(self):
        self.draw_is_curve = not self.draw_is_curve
        self.curve_manager.is_curve = self.draw_is_curve
        self.draw_linecurve.setText("Curve" if self.draw_is_curve else "Line")
        self.curve_manager.update_draw_line()
        self.status_bar.showMessage(f"Drawing {'curve' if self.draw_is_curve else 'line'}")

    def update_smoothing_weight(self, text):
        try:
            val = float(text)
            if val < 1:
                val = 1
            elif val > 100:
                val = 100
            self.curve_manager.smoothing_weight = val
            self.update_smoothing_preview()
            self.status_bar.showMessage(f"Smoothing weight set to {val}")
        except ValueError:
            self.smooth_weight.setText("20")
            self.status_bar.showMessage("Invalid weight, using 20")

    def update_smoothness(self, text):
        try:
            val = float(text)
            if val < 0.1:
                val = 0.1
            elif val > 30.0:
                val = 30.0
            self.smooth_smoothness.setText(str(val))
            self.update_smoothing_preview()
            self.status_bar.showMessage(f"Smoothness set to {val}")
        except ValueError:
            self.smooth_smoothness.setText("1.0")
            self.status_bar.showMessage("Invalid smoothness, using 1.0")

    def update_smoothing_preview(self):
        if self.smoothing_point_selection and self.smoothing_start_idx is not None and self.smoothing_end_idx is not None:
            preview_points = self.curve_manager.preview_smooth(
                self.smoothing_selected_indices, self.smoothing_lane_id,
                self.smoothing_start_idx, self.smoothing_end_idx
            )
            self.canvas.update_plot(self.data_manager.data, self.canvas.selected_indices, None, preview_points)

    def on_confirm_start(self):
        if not self.smoothing_point_selection or self.smoothing_start_idx is None:
            self.status_bar.showMessage("Select start point first")
            return
        self.status_bar.showMessage("Click to select smoothing end point")

    def on_confirm_end(self):
        if not self.smoothing_point_selection or self.smoothing_start_idx is None or self.smoothing_end_idx is None:
            self.status_bar.showMessage("Select both start and end points")
            return
        new_indices = self.curve_manager.straighten_segment(
            self.smoothing_selected_indices, self.smoothing_lane_id,
            self.smoothing_start_idx, self.smoothing_end_idx
        )
        self.clear_state()
        if new_indices:
            self.canvas.selected_indices = new_indices
            self.canvas.update_plot(self.data_manager.data)
            self.status_bar.showMessage(f"Smoothed {len(new_indices)} points")
        else:
            self.canvas.selected_indices = []
            self.canvas.update_plot(self.data_manager.data)
            self.status_bar.showMessage("Smoothing failed")

    def save_data(self):
        filename = self.data_manager.save()
        if filename:
            self.status_bar.showMessage(f"Saved to {filename}")
        else:
            self.status_bar.showMessage("Save failed")

    def export_selected(self):
        if not self.canvas.selected_indices:
            self.status_bar.showMessage("Select points to export")
            return
        selected_points = self.data_manager.data[np.array(self.canvas.selected_indices, dtype=int)]
        filename = f"selected_points_{int(time.time())}.npy"
        np.save(filename, selected_points[:, :3])
        self.status_bar.showMessage(f"Exported {len(selected_points)} points")

    def toggle_grid(self):
        self.canvas.grid_visible = not self.canvas.grid_visible
        self.canvas.update_plot(self.data_manager.data)
        self.status_bar.showMessage(f"Grid {'enabled' if self.canvas.grid_visible else 'disabled'}")

    def on_clear_selection(self):
        self.clear_state()
        self.status_bar.showMessage("Selection cleared")

    def on_undo(self):
        data, success = self.data_manager.undo()
        if success:
            self.canvas.selected_indices = []
            self.canvas.update_plot(data)
            self.status_bar.showMessage("Undo performed")
        else:
            self.status_bar.showMessage("Nothing to undo")

    def on_redo(self):
        data, success = self.data_manager.redo()
        if success:
            self.canvas.selected_indices = []
            self.canvas.update_plot(data)
            self.status_bar.showMessage("Redo performed")
        else:
            self.status_bar.showMessage("Nothing to redo")

    def on_scroll(self, event):
        if event.inaxes != self.canvas.ax:
            return
        base_scale = 1.1
        cur_xlim = self.canvas.ax.get_xlim()
        cur_ylim = self.canvas.ax.get_ylim()
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
        self.canvas.ax.set_xlim([xdata - new_width * (xdata - cur_xlim[0]) / (cur_xlim[1] - cur_xlim[0]),
                                 xdata + new_width * (cur_xlim[1] - xdata) / (cur_xlim[1] - cur_xlim[0])])
        self.canvas.ax.set_ylim([ydata - new_height * (ydata - cur_ylim[0]) / (cur_ylim[1] - cur_ylim[0]),
                                 ydata + new_height * (cur_ylim[1] - ydata) / (cur_ylim[1] - cur_ylim[0])])
        self.canvas.draw()

    def on_click(self, event):
        if event.inaxes != self.canvas.ax or event.button != 1:
            return
        click_x, click_y = event.xdata, event.ydata
        distances = np.sqrt((self.data_manager.data[:, 0] - click_x) ** 2 +
                            (self.data_manager.data[:, 1] - click_y) ** 2)
        closest_idx = np.argmin(distances)
        lane_id = int(self.data_manager.data[closest_idx, -1])

        if self.mode == "remove_above":
            self.remove_point_idx = closest_idx
            self.remove_lane_id = lane_id
            self.data_manager.remove_points_above(self.remove_point_idx, self.remove_lane_id)
            self.canvas.update_plot(self.data_manager.data)
            self.clear_state()
            self.status_bar.showMessage(f"Removed points above index {closest_idx} in lane {lane_id}")
            return

        if self.mode == "remove_below":
            self.remove_point_idx = closest_idx
            self.remove_lane_id = lane_id
            self.data_manager.remove_points_below(self.remove_point_idx, self.remove_lane_id)
            self.canvas.update_plot(self.data_manager.data)
            self.clear_state()
            self.status_bar.showMessage(f"Removed points below index {closest_idx} in lane {lane_id}")
            return

        if self.mode == "merge":
            lane_indices = np.where(self.data_manager.data[:, -1] == lane_id)[0]
            lane_data = self.data_manager.data[lane_indices]
            min_idx = lane_data[:, 4].argmin()
            max_idx = lane_data[:, 4].argmax()
            point_type = 'start' if closest_idx == lane_indices[min_idx] else 'end' if closest_idx == lane_indices[
                max_idx] else None
            if point_type is None:
                self.status_bar.showMessage("Select a start or end point")
                return
            if self.merge_point_1 is None:
                self.merge_point_1 = closest_idx
                self.merge_lane_1 = lane_id
                self.merge_point_1_type = point_type
                self.merge_status.setText(f"Selected {point_type} point in lane {lane_id}. Select second point.")
                self.canvas.update_plot(self.data_manager.data, self.canvas.selected_indices,
                                        [(self.merge_point_1, self.merge_point_1_type, self.merge_lane_1)])
            elif self.merge_point_2 is None and lane_id != self.merge_lane_1:
                self.merge_point_2 = closest_idx
                self.merge_lane_2 = lane_id
                self.merge_point_2_type = point_type
                self.merge_status.setText(f"Selected {point_type} point in lane {lane_id}. Merging...")
                self.finalize_merge()
            return

        if self.mode == "smooth" and self.smoothing_point_selection:
            selected_points = self.data_manager.data[self.smoothing_selected_indices, :2]
            distances = np.sqrt((selected_points[:, 0] - click_x) ** 2 + (selected_points[:, 1] - click_y) ** 2)
            closest_idx = np.argmin(distances)
            global_idx = self.smoothing_selected_indices[closest_idx]
            if self.smoothing_start_idx is None:
                self.smoothing_start_idx = global_idx
                self.status_bar.showMessage("Confirm start or select end point")
                self.canvas.update_plot(self.data_manager.data, self.canvas.selected_indices)
            elif self.smoothing_end_idx is None:
                self.smoothing_end_idx = global_idx
                preview_points = self.curve_manager.preview_smooth(
                    self.smoothing_selected_indices, self.smoothing_lane_id,
                    self.smoothing_start_idx, self.smoothing_end_idx
                )
                self.canvas.update_plot(self.data_manager.data, self.canvas.selected_indices, None, preview_points)
                self.status_bar.showMessage("Confirm end or cancel")
            return

        if self.mode == "draw":
            self.selected_id = self.draw_lane_id.currentIndex()
            if self.draw_lane_id.currentText() == "New Lane":
                self.selected_id = len(self.data_manager.file_names)
            self.curve_manager.add_draw_point(click_x, click_y)
            self.canvas.update_plot(self.data_manager.data)
            self.status_bar.showMessage(f"Added point to {'curve' if self.draw_is_curve else 'line'}")
            return

        if self.mode == "add_delete":
            self.data_manager.add_point(click_x, click_y, self.selected_id)
            self.canvas.update_plot(self.data_manager.data)
            self.status_bar.showMessage(f"Added point in lane {self.selected_id}")
            return

        if self.mode == "select":
            # Rectangle selection logic would require a custom drag event, simplified here to single-point selection
            if distances[closest_idx] < self.canvas.D / 100:
                self.canvas.selected_indices = [closest_idx]
                self.canvas.update_plot(self.data_manager.data, self.canvas.selected_indices)
                self.status_bar.showMessage(f"Selected point {closest_idx}")
            return

    def finalize_merge(self):
        if self.merge_point_1 is None or self.merge_point_2 is None or self.merge_lane_1 == self.merge_lane_2:
            self.status_bar.showMessage("Select two different lanes")
            self.clear_state()
            return
        self.merge_point_1, self.merge_point_2 = self.data_manager.merge_lanes(
            self.merge_lane_1, self.merge_lane_2, self.merge_point_1, self.merge_point_2,
            self.merge_point_1_type, self.merge_point_2_type
        )
        self.data_manager.save_all_lanes()
        self.data_manager.clear_data()
        temp_loader = DataLoader("../workspace-Temp")
        data, file_names = temp_loader.load_data()
        self.data_manager.__init__(data, file_names)
        self.canvas.file_names = file_names
        self.canvas.selected_indices = []
        self.canvas.update_plot(self.data_manager.data)
        self.draw_lane_id.clear()
        self.draw_lane_id.addItems([f"Lane {i}" for i in range(len(file_names))] + ["New Lane"])
        self.status_bar.showMessage(f"Merged lane {self.merge_lane_2} into lane {self.merge_lane_1}")
        self.clear_state()


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec())
