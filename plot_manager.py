import matplotlib.pyplot as plt
import matplotlib.widgets as widgets
import matplotlib.patches as patches
import numpy as np

class PlotManager:
    def __init__(self, data, file_names, D, data_manager, event_handler):
        self.data = data
        self.file_names = file_names
        self.D = D
        self.data_manager = data_manager
        self.event_handler = event_handler
        self.colors = plt.cm.tab10(np.linspace(0, 1, max(len(file_names), 1)))
        self.selected_indices = []
        self.scatter_plots = []
        self.indices = []
        self.smoothed_area_patch = None  # To store the patch marking the smoothed area

        self.fig = plt.figure(figsize=(12, 8))
        self.ax = self.fig.add_subplot(111)
        self.setup_widgets()
        self.setup_plot()
        self.setup_events()
        self.update_status()

    def setup_plot(self):
        current_xlim = self.ax.get_xlim() if self.ax.get_xlim() != (0, 1) else None
        current_ylim = self.ax.get_ylim() if self.ax.get_ylim() != (0, 1) else None

        self.ax.clear()
        self.scatter_plots = []
        self.indices = []
        for i in range(len(self.file_names)):
            mask = self.data[:, -1] == i
            indices = np.where(mask)[0]
            self.indices.append(indices)
            sc = self.ax.scatter(self.data[indices, 0], self.data[indices, 1],
                                 c=[self.colors[i]], label=f'{self.file_names[i]}',
                                 picker=5, s=10, alpha=0.6)
            self.scatter_plots.append(sc)
        if not self.file_names:
            self.scatter_plots.append(self.ax.scatter([], [], c=[self.colors[0]],
                                                      label='Empty', s=10))
            self.indices.append(np.array([]))
        self.ax.legend()

        # Redraw the smoothed area patch if it exists
        if self.smoothed_area_patch is not None:
            self.ax.add_patch(self.smoothed_area_patch)

        if current_xlim and current_ylim:
            self.ax.set_xlim(current_xlim)
            self.ax.set_ylim(current_ylim)

        self.update_status()

    def setup_widgets(self):
        self.fig.subplots_adjust(top=0.85, bottom=0.15)

        self.status_ax = self.fig.add_axes([0.1, 0.92, 0.8, 0.05], frame_on=False)
        self.status_ax.xaxis.set_visible(False)
        self.status_ax.yaxis.set_visible(False)
        self.status_text = self.status_ax.text(0.5, 0.5, "", ha='center', va='center', fontsize=10)

        ax_save = self.fig.add_axes([0.91, 0.02, 0.08, 0.04])
        self.btn_save = widgets.Button(ax_save, 'Save', color='lightgreen', hovercolor='lightblue')
        self.btn_save.on_clicked(self.event_handler.on_save)
        self.btn_save.label.set_fontsize(8)

        ax_toggle = self.fig.add_axes([0.01, 0.06, 0.12, 0.04])
        self.btn_toggle = widgets.Button(ax_toggle, 'Select Mode', color='lightcoral', hovercolor='lightblue')
        self.btn_toggle.on_clicked(self.event_handler.on_toggle_mode)
        self.btn_toggle.label.set_fontsize(8)

        ax_undo = self.fig.add_axes([0.81, 0.02, 0.04, 0.04])
        self.btn_undo = widgets.Button(ax_undo, 'Undo', color='lightyellow', hovercolor='lightblue')
        self.btn_undo.on_clicked(self.event_handler.on_undo)
        self.btn_undo.label.set_fontsize(8)

        ax_redo = self.fig.add_axes([0.86, 0.02, 0.04, 0.04])
        self.btn_redo = widgets.Button(ax_redo, 'Redo', color='lightyellow', hovercolor='lightblue')
        self.btn_redo.on_clicked(self.event_handler.on_redo)
        self.btn_redo.label.set_fontsize(8)

        ax_linecurve = self.fig.add_axes([0.14, 0.06, 0.08, 0.04])
        self.btn_linecurve = widgets.Button(ax_linecurve, 'Line', color='lightblue', hovercolor='cyan')
        self.btn_linecurve.on_clicked(self.event_handler.on_toggle_linecurve)
        self.btn_linecurve.label.set_fontsize(8)

        ax_straighten = self.fig.add_axes([0.23, 0.06, 0.08, 0.04])
        self.btn_straighten = widgets.Button(ax_straighten, 'Smooth', color='lightpink', hovercolor='cyan')
        self.btn_straighten.on_clicked(self.event_handler.on_straighten)
        self.btn_straighten.label.set_fontsize(8)

        ax_clear = self.fig.add_axes([0.32, 0.06, 0.12, 0.04])
        self.btn_clear = widgets.Button(ax_clear, 'Clear Selection', color='lightgray', hovercolor='cyan')
        self.btn_clear.on_clicked(self.event_handler.on_clear_selection)
        self.btn_clear.label.set_fontsize(8)

        ax_confirm_start = self.fig.add_axes([0.45, 0.06, 0.12, 0.04])
        self.btn_confirm_start = widgets.Button(ax_confirm_start, 'Confirm Start', color='lightgreen', hovercolor='cyan')
        self.btn_confirm_start.on_clicked(self.event_handler.on_confirm_start)
        self.btn_confirm_start.label.set_fontsize(8)

        ax_confirm_end = self.fig.add_axes([0.58, 0.06, 0.12, 0.04])
        self.btn_confirm_end = widgets.Button(ax_confirm_end, 'Confirm End', color='lightgreen', hovercolor='cyan')
        self.btn_confirm_end.on_clicked(self.event_handler.on_confirm_end)
        self.btn_confirm_end.label.set_fontsize(8)

        ax_cancel_smoothing = self.fig.add_axes([0.71, 0.06, 0.12, 0.04])
        self.btn_cancel_smoothing = widgets.Button(ax_cancel_smoothing, 'Cancel Smoothing', color='salmon', hovercolor='cyan')
        self.btn_cancel_smoothing.on_clicked(self.event_handler.on_cancel_smoothing)
        self.btn_cancel_smoothing.label.set_fontsize(8)

        ax_slider = self.fig.add_axes([0.01, 0.02, 0.3, 0.03])
        self.slider_smooth = widgets.Slider(ax_slider, 'Smooth Factor', 0.5, 5.0, valinit=2.0, valstep=0.5)
        self.slider_smooth.label.set_fontsize(8)

        self.rs = widgets.RectangleSelector(self.ax, self.event_handler.on_select,
                                            useblit=True, button=[1], minspanx=5,
                                            minspany=5, spancoords='pixels',
                                            interactive=True, props=dict(facecolor='cyan',
                                                                         alpha=0.3))
        self.rs.set_active(False)

    def setup_events(self):
        self.fig.canvas.mpl_connect('button_press_event', self.event_handler.on_click)
        self.fig.canvas.mpl_connect('pick_event', self.event_handler.on_pick)
        self.fig.canvas.mpl_connect('key_press_event', self.event_handler.on_key)

    def mark_smoothed_area(self, smoothed_points):
        """Mark the area of the smoothed segment with a bounding box."""
        if smoothed_points.shape[0] < 2:
            return

        # Clear any existing smoothed area patch
        self.clear_smoothed_area()

        # Compute the bounding box of the smoothed points
        x_min, x_max = np.min(smoothed_points[:, 0]), np.max(smoothed_points[:, 0])
        y_min, y_max = np.min(smoothed_points[:, 1]), np.max(smoothed_points[:, 1])

        # Add some padding to the bounding box
        padding = 0.5
        width = x_max - x_min + 2 * padding
        height = y_max - y_min + 2 * padding
        x_min -= padding
        y_min -= padding

        # Create a rectangle patch
        self.smoothed_area_patch = patches.Rectangle(
            (x_min, y_min), width, height,
            linewidth=1, edgecolor='purple', facecolor='purple', alpha=0.1, label='Smoothed Area'
        )
        self.ax.add_patch(self.smoothed_area_patch)
        self.ax.legend()
        self.fig.canvas.draw_idle()

    def clear_smoothed_area(self):
        """Remove the marking of the smoothed area."""
        if self.smoothed_area_patch is not None:
            self.smoothed_area_patch.remove()
            self.smoothed_area_patch = None
            self.ax.legend()
            self.fig.canvas.draw_idle()

    def update_status(self, instruction=None):
        mode = "Draw" if self.event_handler.draw_mode else (
            "Selection" if self.event_handler.selection_mode else "Add/Delete")
        mode_color = "green" if self.event_handler.selection_mode else ("blue" if self.event_handler.draw_mode else "black")
        status = f"Mode: <{mode}> | Lane ID: {self.event_handler.selected_id + 1} | Selected Points: {len(self.selected_indices)}"
        if instruction:
            status += f"\nInstruction: {instruction}"
        if hasattr(self, 'status_text'):
            self.status_text.set_text(status)
            self.status_text.set_color(mode_color)
            self.fig.canvas.draw_idle()

    def update_plot(self, data):
        self.data = data
        valid_indices = [idx for idx in self.selected_indices if idx < len(self.data)]
        self.selected_indices = valid_indices
        self.setup_plot()
        if self.selected_indices:
            for idx in self.selected_indices:
                if idx < len(self.data):
                    file_idx = int(self.data[idx, -1])
                    sc = self.scatter_plots[file_idx]
                    current_sizes = sc.get_sizes()
                    offset_idx = np.where(self.indices[file_idx] == idx)[0]
                    if offset_idx.size > 0 and offset_idx[0] < len(current_sizes):
                        current_sizes[offset_idx[0]] = 30
                        sc.set_sizes(current_sizes)
        self.update_status()