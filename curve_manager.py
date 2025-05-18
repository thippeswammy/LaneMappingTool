import numpy as np
from scipy.signal import savgol_filter
from scipy.interpolate import splprep, splev
import matplotlib.pyplot as plt


class CurveManager:
    def __init__(self, data_manager, plot_manager):
        self.data_manager = data_manager
        self.plot_manager = plot_manager
        self.draw_points = []
        self.is_curve = False
        self.current_line = None

    def add_draw_point(self, x, y):
        self.draw_points.append([x, y])
        self.update_draw_line()

    def update_draw_line(self):
        if self.current_line:
            self.current_line.remove()
            self.current_line = None
        if len(self.draw_points) < 2:
            return
        points = np.array(self.draw_points)
        x, y = points[:, 0], points[:, 1]
        if self.is_curve and len(points) >= 5:
            try:
                # Apply Savitzky-Golay smoothing
                window_length = 5 if len(y) >= 5 else len(y) // 2 * 2 + 1
                polyorder = 2
                y_smooth = savgol_filter(y, window_length, polyorder)
                y_smooth[0], y_smooth[-1] = y[0], y[-1]  # Keep endpoints fixed
                smooth_points = np.stack((x, y_smooth), axis=1)
                self.current_line = self.plot_manager.ax.plot(
                    smooth_points[:, 0], smooth_points[:, 1], 'k-', alpha=0.5)[0]
            except Exception as e:
                print(f"Smoothing failed: {e}")
                self.current_line = self.plot_manager.ax.plot(x, y, 'k-', alpha=0.5)[0]
        else:
            self.current_line = self.plot_manager.ax.plot(x, y, 'k-', alpha=0.5)[0]
        self.plot_manager.fig.canvas.draw_idle()

    def finalize_draw(self, file_id):
        if len(self.draw_points) < 2:
            self.draw_points = []
            if self.current_line:
                self.current_line.remove()
                self.current_line = None
            return
        points = np.array(self.draw_points)
        x, y = points[:, 0], points[:, 1]
        if self.is_curve and len(points) >= 5:
            try:
                window_length = 5 if len(y) >= 5 else len(y) // 2 * 2 + 1
                polyorder = 2
                y_smooth = savgol_filter(y, window_length, polyorder)
                y_smooth[0], y_smooth[-1] = y[0], y[-1]
                points = np.stack((x, y_smooth), axis=1)
            except Exception as e:
                print(f"Smoothing during finalize failed: {e}")
        for x, y in points:
            self.data_manager.add_point(x, y, file_id)
        self.draw_points = []
        if self.current_line:
            self.current_line.remove()
            self.current_line = None
        self.plot_manager.update_plot(self.data_manager.data)

    def straighten_segment(self, selected_indices):
        if len(selected_indices) < 2:
            print("Need at least 2 points to smooth")
            return []
        selected_indices = sorted(selected_indices)
        file_id = int(self.data_manager.data[selected_indices[0], self.data_manager.D])

        # Extract selected points
        points = self.data_manager.data[selected_indices, :2]
        start_point = points[0]
        end_point = points[-1]

        # Find adjacent points for natural tangent alignment
        all_indices = np.where(self.data_manager.data[:, self.data_manager.D] == file_id)[0]
        all_indices = sorted(all_indices)
        selected_set = set(selected_indices)
        prev_point = None
        next_point = None

        # Find the point before the selected segment
        for idx in reversed(all_indices):
            if idx < selected_indices[0] and idx not in selected_set:
                prev_point = self.data_manager.data[idx, :2]
                break

        # Find the point after the selected segment
        for idx in all_indices:
            if idx > selected_indices[-1] and idx not in selected_set:
                next_point = self.data_manager.data[idx, :2]
                break

        # Include adjacent points in the spline fitting for natural tangent alignment
        fitting_points = points.copy()
        if prev_point is not None:
            fitting_points = np.vstack([prev_point, fitting_points])
        if next_point is not None:
            fitting_points = np.vstack([fitting_points, next_point])

        try:
            # Use a parametric smoothing spline to approximate the points
            x, y = fitting_points[:, 0], fitting_points[:, 1]

            # Compute cumulative distance as the parameter for better spline fitting
            distances = np.sqrt(np.sum(np.diff(fitting_points, axis=0) ** 2, axis=1))
            u = np.zeros(len(fitting_points))
            u[1:] = np.cumsum(distances)
            u = u / u[-1] if u[-1] > 0 else np.linspace(0, 1, len(fitting_points))  # Normalize to [0, 1]

            # Fit a smoothing spline (not interpolating all points)
            smoothing_factor = len(points) * 1.0  # Increased for more smoothness
            tck, u_fitted = splprep([x, y], u=u, s=smoothing_factor, k=3)

            # Generate new points on the smoothed curve, only for the selected segment
            # Map the original u values of the selected points to the fitted u
            start_idx = 1 if prev_point is not None else 0
            end_idx = len(fitting_points) - (2 if next_point is not None else 1)
            u_segment = u_fitted[start_idx:end_idx]
            u_segment_normalized = (u_segment - u_segment[0]) / (u_segment[-1] - u_segment[0]) if u_segment[-1] != \
                                                                                                  u_segment[
                                                                                                      0] else np.linspace(
                0, 1, len(u_segment))

            # Generate new points for the selected segment
            num_new_points = max(10, len(points) * 2)  # More points for smoother curve
            u_fine = np.linspace(0, 1, num_new_points)
            x_smooth, y_smooth = splev(u_fine, tck)

            new_points = np.stack((x_smooth, y_smooth), axis=1)

            # Ensure start and end points are exactly the same (numerical precision)
            new_points[0] = start_point
            new_points[-1] = end_point

        except ValueError as e:
            print(f"Smoothing failed: {e}")
            return []

        # Debugging: Plot original and smoothed points in a separate figure
        plt.figure(figsize=(8, 6))
        plt.plot(points[:, 0], points[:, 1], 'ro-', label='Original')
        plt.plot(new_points[:, 0], new_points[:, 1], 'g.-', label='Smoothed')
        if prev_point is not None:
            plt.plot([prev_point[0], points[0, 0]], [prev_point[1], points[0, 1]], 'b--', label='Previous Segment')
        if next_point is not None:
            plt.plot([points[-1, 0], next_point[0]], [points[-1, 1], next_point[1]], 'b--', label='Next Segment')
        plt.legend()
        plt.title("Waypoint Smoothing")
        plt.xlabel("x")
        plt.ylabel("y")
        plt.grid(True)
        plt.show()

        # Remove old points
        self.data_manager.delete_points(selected_indices)

        # Add new smoothed points
        new_indices = []
        for x, y in new_points:
            self.data_manager.add_point(x, y, file_id)
            new_indices.append(len(self.data_manager.data) - 1)

        self.plot_manager.update_plot(self.data_manager.data)
        return new_indices