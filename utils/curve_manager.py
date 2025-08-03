import matplotlib.pyplot as plt
import numpy as np
from scipy.interpolate import splprep, splev
from scipy.signal import savgol_filter


class CurveManager:
    def __init__(self, data_manager, plot_manager):
        self.data_manager = data_manager
        self.plot_manager = plot_manager
        self.draw_points = []
        self.is_curve = False
        self.current_line = None
        self.show_debug_plot = False  # Disabled by default
        self.smoothing_weight = 20 # Default value, updated via text box

    def add_draw_point(self, x, y):
        try:
            self.draw_points.append([x, y])
            self.update_draw_line()
        except Exception as e:
            print(f"Error adding draw point: {e}")

    def update_draw_line(self):
        if self.current_line:
            self.current_line.remove()
            self.current_line = None
        if len(self.draw_points) < 2:
            return
        points = np.array(self.draw_points)
        x, y = points[:, 0], points[:, 1]
        try:
            if self.is_curve and len(points) >= 5:
                window_length = min(5, len(y) // 2 * 2 + 1)
                polyorder = 2
                y_smooth = savgol_filter(y, window_length, polyorder)
                y_smooth[0], y_smooth[-1] = y[0], y[-1]
                smooth_points = np.stack((x, y_smooth), axis=1)
                self.current_line = self.plot_manager.ax.plot(
                    smooth_points[:, 0], smooth_points[:, 1], 'k-', alpha=0.5)[0]
            else:
                self.current_line = self.plot_manager.ax.plot(x, y, 'k-', alpha=0.5)[0]
            self.plot_manager.fig.canvas.draw_idle()
        except Exception as e:
            print(f"Error updating draw line: {e}")

    def finalize_draw(self, file_id):
        if len(self.draw_points) < 2:
            self.draw_points = []
            if self.current_line:
                self.current_line.remove()
                self.current_line = None
            return
        points = np.array(self.draw_points)
        x, y = points[:, 0], points[:, 1]
        try:
            if self.is_curve and len(points) >= 5:
                window_length = min(5, len(y) // 2 * 2 + 1)
                polyorder = 2
                y_smooth = savgol_filter(y, window_length, polyorder)
                y_smooth[0], y_smooth[-1] = y[0], y[-1]
                points = np.stack((x, y_smooth), axis=1)
            for x, y in points:
                self.data_manager.add_point(x, y, file_id)
            self.draw_points = []
            if self.current_line:
                self.current_line.remove()
                self.current_line = None
            self.plot_manager.update_plot(self.data_manager.data)
        except Exception as e:
            print(f"Error finalizing draw: {e}")

    def preview_smooth(self, selected_indices, lane_id, start_idx, end_idx):
        try:
            new_points = self._smooth_segment(selected_indices, lane_id, start_idx, end_idx, preview=True)
            return new_points
        except Exception as e:
            print(f"Error previewing smooth: {e}")
            return None

    def straighten_segment(self, selected_indices, lane_id, start_idx, end_idx):
        try:
            new_points = self._smooth_segment(selected_indices, lane_id, start_idx, end_idx, preview=False)
            if new_points is None:
                return []

            selected_indices = sorted(selected_indices)
            start_pos = selected_indices.index(start_idx)
            end_pos = selected_indices.index(end_idx)
            if start_pos > end_pos:
                start_idx, end_idx = end_idx, start_idx
                start_pos, end_pos = end_pos, start_pos
            segment_indices = selected_indices[start_pos:end_pos + 1]

            if len(new_points) != len(segment_indices):
                print(f"Warning: Expected {len(segment_indices)} new points, got {len(new_points)}")
                return []

            self.data_manager.data[segment_indices, 0:2] = new_points

            for i, idx in enumerate(segment_indices):
                if i < len(new_points) - 1:
                    dx = new_points[i + 1, 0] - new_points[i, 0]
                    dy = new_points[i + 1, 1] - new_points[i, 1]
                    self.data_manager.data[idx, 2] = np.arctan2(dy, dx)
                else:
                    self.data_manager.data[idx, 2] = self.data_manager.data[segment_indices[-2], 2] if len(
                        segment_indices) > 1 else 0.0

            self.data_manager.data[segment_indices, -1] = lane_id

            self.data_manager.history.append(self.data_manager.data.copy())
            self.data_manager.redo_stack = []

            self.plot_manager.selected_indices = []

            self.plot_manager.update_plot(self.data_manager.data)
            return segment_indices
        except Exception as e:
            print(f"Error straightening segment: {e}")
            return []

    def _smooth_segment(self, selected_indices, lane_id, start_idx, end_idx, preview=False):
        if len(selected_indices) < 2:
            print("Need at least 2 points to smooth")
            return None

        selected_indices = sorted(selected_indices)

        if start_idx not in selected_indices or end_idx not in selected_indices:
            print("Start or end index not in selected indices")
            return None

        start_pos = selected_indices.index(start_idx)
        end_pos = selected_indices.index(end_idx)
        if start_pos > end_pos:
            start_idx, end_idx = end_idx, start_idx
            start_pos, end_pos = end_pos, start_pos

        segment_indices = selected_indices[start_pos:end_pos + 1]
        points = self.data_manager.data[segment_indices, :2]

        # Original start and end points of the selected segment (for final assignment)
        original_start_point = self.data_manager.data[start_idx, :2]
        original_end_point = self.data_manager.data[end_idx, :2]

        all_indices = np.arange(len(self.data_manager.data))
        selected_set = set(segment_indices)
        prev_point, next_point = None, None

        # Find the adjacent points outside the selected segment
        for idx in reversed(all_indices):
            if idx < start_idx and idx not in selected_set:
                prev_point = self.data_manager.data[idx, :2]
                break

        for idx in all_indices:
            if idx > end_idx and idx not in selected_set:
                next_point = self.data_manager.data[idx, :2]
                break

        fitting_points = points.copy()
        weights = np.ones(len(fitting_points)) * self.smoothing_weight  # Default weight for segment points

        segment_start_in_fitting = 0
        segment_end_in_fitting = len(fitting_points) - 1

        # High weight for the segment's true start and end points
        HIGH_WEIGHT = 100

        if prev_point is not None:
            fitting_points = np.vstack([prev_point, fitting_points])
            weights = np.concatenate(([1], weights))  # Low weight for the distant prev_point
            segment_start_in_fitting += 1  # Shift index due to prev_point
            segment_end_in_fitting += 1  # Shift index due to prev_point

        if next_point is not None:
            fitting_points = np.vstack([fitting_points, next_point])
            weights = np.concatenate((weights, [1]))  # Low weight for the distant next_point

        # Apply high weights to the actual start and end points of the *selected segment*
        # within the now potentially expanded `fitting_points` and `weights` arrays.
        weights[segment_start_in_fitting] = HIGH_WEIGHT
        weights[segment_end_in_fitting] = HIGH_WEIGHT
        # --- MODIFICATION END ---

        try:
            x, y = fitting_points[:, 0], fitting_points[:, 1]
            distances = np.sqrt(np.sum(np.diff(fitting_points, axis=0) ** 2, axis=1))
            u = np.zeros(len(fitting_points))
            u[1:] = np.cumsum(distances)
            u = u / u[-1] if u[-1] > 0 else np.linspace(0, 1, len(fitting_points))

            smoothing_factor = len(points) * self.plot_manager.slider_smooth.val

            if smoothing_factor < 0.1:
                smoothing_factor = 0.1
            tck, u_fitted = splprep([x, y], u=u, s=smoothing_factor, k=3, w=weights)

            # Determine the range of 'u' values corresponding to the selected segment
            # This is tricky because u_fitted corresponds to the entire fitting_points array.
            # We need to find the u values for the *original* start and end points of the segment.
            # Using original start/end points' u-values from the initial 'u' array.

            # Find the u-values corresponding to the original start and end points of the segment.
            # These are the u-values at indices `segment_start_in_fitting` and `segment_end_in_fitting`
            # in the `u` array that was passed to splprep.
            u_start_segment = u[segment_start_in_fitting]
            u_end_segment = u[segment_end_in_fitting]

            num_new_points = len(segment_indices)
            # Generate new u values that span only the segment, distributing points evenly.
            u_fine = np.linspace(u_start_segment, u_end_segment, num_new_points)

            x_smooth, y_smooth = splev(u_fine, tck)

            new_points = np.stack((x_smooth, y_smooth), axis=1)

            # Re-assert the exact start and end points to counter any residual deviation
            new_points[0] = original_start_point
            new_points[-1] = original_end_point

            if self.show_debug_plot and not preview:
                plt.figure(figsize=(8, 6))
                plt.plot(points[:, 0], points[:, 1], 'ro-', label='Original Segment')
                plt.plot(new_points[:, 0], new_points[:, 1], 'g.-', label='Smoothed Segment')
                plt.plot(fitting_points[:, 0], fitting_points[:, 1], 'bx', markersize=10,
                         label='Fitting Points (incl. adjacent)')

                # Highlight the points that were given high weights in fitting_points
                plt.plot(fitting_points[segment_start_in_fitting, 0], fitting_points[segment_start_in_fitting, 1], 'ko',
                         markersize=12, fillstyle='none', label='High Weight Start')
                plt.plot(fitting_points[segment_end_in_fitting, 0], fitting_points[segment_end_in_fitting, 1], 'ko',
                         markersize=12, fillstyle='none', label='High Weight End')

                if prev_point is not None:
                    plt.plot([prev_point[0], points[0, 0]], [prev_point[1], points[0, 1]], 'c--',
                             label='Prev Adjacent Link')
                if next_point is not None:
                    plt.plot([points[-1, 0], next_point[0]], [points[-1, 1], next_point[1]], 'm--',
                             label='Next Adjacent Link')
                plt.legend()
                plt.title("Smoothing Segment with High Endpoint Weights")
                plt.xlabel("x")
                plt.ylabel("y")
                plt.grid(True)
                plt.show()

            return new_points
        except ValueError as e:
            print(f"Spline fitting failed: {e}")
            return None
