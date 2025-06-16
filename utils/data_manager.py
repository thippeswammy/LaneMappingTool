import os
import shutil
import time

import numpy as np

from DataVisualizationEditingTool.utils.network_ import pickerGenerateViewer


class DataManager:
    def __init__(self, data, file_names):
        if data.size > 0:
            if len(data.shape) != 2 or data.shape[1] != 6:
                raise ValueError(
                    f"Expected data to be a 2D array with 6 columns (x, y, yaw, frame_idx, index, lane_id), "
                    f"got shape {data.shape}"
                )
            if not np.issubdtype(data[:, -1].dtype, np.integer):
                data[:, -1] = data[:, -1].astype(int)
            if not np.issubdtype(data[:, 3].dtype, np.integer) or not np.issubdtype(data[:, 4].dtype, np.integer):
                data[:, 3] = data[:, 3].astype(int)
                data[:, 4] = data[:, 4].astype(int)
            if not np.array_equal(data[:, 3], data[:, 4]):
                raise ValueError("frame_idx and index columns must be identical")
            self.data = data.copy()
        else:
            self.data = np.array([])

        self.file_names = file_names
        self.total_cols = data.shape[1] if data.size > 0 else 0
        self.history = [self.data.copy()] if self.data.size > 0 else [np.array([])]
        self.redo_stack = []
        self.last_backup = time.time()
        self.backup_interval = 300  # 5 minutes

        print(f"DataManager initialized with {len(self.data)} points")

    def add_point(self, x, y, lane_id):
        try:
            new_point = np.zeros((1, self.total_cols))
            new_point[0, 0] = x
            new_point[0, 1] = y
            new_point[0, -1] = lane_id
            new_index = len(self.data)
            new_point[0, 3] = new_index
            new_point[0, 4] = new_index
            self.data = np.vstack([self.data, new_point]) if self.data.size > 0 else new_point
            self.history.append(self.data.copy())
            self.redo_stack = []
            self._auto_save_backup()
            print(f"Added point: ({x:.2f}, {y:.2f}, lane_id={lane_id})")
        except Exception as e:
            print(f"Error adding point: {e}")

    def delete_points(self, indices):
        """Delete points at specified indices from the data array."""
        if not indices:
            return
        try:
            # Validate indices
            indices = np.asarray(indices, dtype=int)
            if np.any(indices < 0) or np.any(indices >= len(self.data)):
                print(f"Error: Indices {indices} out of bounds for data of length {len(self.data)}")
                return
            mask = np.ones(len(self.data), dtype=bool)
            mask[indices] = False
            self.data = self.data[mask]
            # Handle empty data case
            if self.data.size == 0:
                self.data = np.array([], dtype=self.data.dtype).reshape(0, self.total_cols)
            else:
                new_indices = np.arange(len(self.data))
                self.data[:, 3] = new_indices
                self.data[:, 4] = new_indices
            self.history.append(self.data.copy())
            self.redo_stack = []
            self._auto_save_backup()
            print(f"Deleted {len(indices)} points")
        except Exception as e:
            print(f"Error deleting points: {e}")

    def change_ids(self, indices, new_id):
        if not indices:
            return
        try:
            self.data[indices, -1] = new_id
            self.history.append(self.data.copy())
            self.redo_stack = []
            self._auto_save_backup()
            print(f"Changed lane IDs for {len(indices)} points to {new_id}")
        except Exception as e:
            print(f"Error changing IDs: {e}")

    def remove_points_above(self, index, lane_id):
        """Remove points in the specified lane with local indices >= the local index of the given global index."""
        try:
            # Validate index and lane
            if index < 0 or index >= len(self.data) or int(self.data[index, -1]) != lane_id:
                print(f"Invalid index {index} or lane mismatch for lane {lane_id}")
                return
            lane_mask = self.data[:, -1] == lane_id
            lane_indices = np.where(lane_mask)[0]
            if len(lane_indices) == 0:
                print(f"No points found in lane {lane_id}")
                return
            lane_data = self.data[lane_mask]
            # Check for duplicate indices
            indices = lane_data[:, 4]
            if len(indices) != len(np.unique(indices)):
                print(f"Warning: Duplicate indices found in lane {lane_id}: {indices}")
            # Sort by index column (data[:, 4])
            sorted_indices = lane_data[:, 4].argsort()
            sorted_global_indices = lane_indices[sorted_indices]
            # Find the local index of the clicked point
            target_global_idx = np.where(sorted_global_indices == index)[0]
            if len(target_global_idx) == 0:
                print(f"Global index {index} not found in lane {lane_id}")
                return
            if len(target_global_idx) > 1:
                print(f"Warning: Multiple matches for global index {index} in lane {lane_id}, using first match")
            local_index = target_global_idx[0]
            indices_to_remove = sorted_global_indices[:local_index]
            list_ = []
            for i in indices_to_remove:
                list_.append(i)
            self.delete_points(list_)
            print(
                f"Removed {len(indices_to_remove)} points above local index {local_index} (global index {index}) in lane {lane_id}")
        except Exception as e:
            print(f"Error removing points above: {e}")

    def remove_points_below(self, index, lane_id):
        """Remove points in the specified lane with global indices <= the given index."""
        try:
            # Validate index
            if index < 0 or index >= len(self.data):
                print(f"Invalid index {index}")
                return
            # Filter points by lane_id
            lane_mask = self.data[:, -1] == lane_id
            lane_indices = np.where(lane_mask)[0]
            if len(lane_indices) == 0:
                print(f"No points found in lane {lane_id}")
                return
            # Select points with global indices <= index
            indices_to_remove = lane_indices[lane_indices >= index]
            # print('indices_to_remove=>', indices_to_remove)
            if len(indices_to_remove) == 0:
                print(f"No points with global indices <= {index} in lane {lane_id}")
                return
            list_ = []
            for i in indices_to_remove:
                list_.append(i)
            self.delete_points(list_)
            print(f"Removed {len(indices_to_remove)} points below index {index} in lane {lane_id}")
        except Exception as e:
            print(f"Error removing points below: {e}")

    def merge_lanes(self, lane_id_1, lane_id_2, point_1, point_2, point_1_type, point_2_type):
        """Merge lane_id_2 into lane_id_1, ensuring continuous index sequence with correct start/end connections."""
        # lane_1_mask = self.data[:, -1] == lane_id_1
        # lane_2_mask = self.data[:, -1] == lane_id_2
        # if not np.any(lane_1_mask) or not np.any(lane_2_mask):
        #     print(f"One or both lanes ({lane_id_1}, {lane_id_2}) are empty")
        #     return
        #
        # lane_1_indices = np.where(lane_1_mask)[0]
        # lane_2_indices = np.where(lane_2_mask)[0]
        # print('lane_1_indices=>', lane_1_indices)
        # print('lane_2_indices=>', lane_2_indices)
        # print('-' * 50)
        # print(lane_2_indices[-1] > lane_1_indices[0], ' ||', point_1 > point_2)
        # print('point_1=>', point_1, 'point_2=>', point_2)
        # print('==>', lane_2_indices[-1], lane_1_indices[0])
        # if point_1 > point_2:
        #     lane_id_1, point_1, point_1_type, lane_id_2, point_2, point_2_type = (
        #         lane_id_2, point_2, point_2_type, lane_id_1, point_1, point_1_type)

        if self.data.size == 0:
            print("No data to merge")
            return
        try:
            lane_1_mask = self.data[:, -1] == lane_id_1
            lane_2_mask = self.data[:, -1] == lane_id_2
            if not np.any(lane_1_mask) or not np.any(lane_2_mask):
                print(f"One or both lanes ({lane_id_1}, {lane_id_2}) are empty")
                return

            lane_1_data = self.data[lane_1_mask]
            lane_2_data = self.data[lane_2_mask]
            lane_1_indices = np.where(lane_1_mask)[0]
            lane_2_indices = np.where(lane_2_mask)[0]

            # Find local indices of selected points
            point_1_local = np.where(lane_1_indices == point_1)[0]
            point_2_local = np.where(lane_2_indices == point_2)[0]
            if len(point_1_local) == 0 or len(point_2_local) == 0:
                print(f"Invalid points: point_1={point_1}, point_2={point_2}")
                return
            point_1_local = point_1_local[0]
            point_2_local = point_2_local[0]

            # Sort lanes by index column (data[:, 4]) for consistent ordering
            lane_1_sorted = lane_1_data[np.argsort(lane_1_data[:, 4])]
            lane_2_sorted = lane_2_data[np.argsort(lane_2_data[:, 4])]

            # Debug: Print input points and their coordinates
            print(
                f"Point 1 ({point_1_type}): index={point_1}, local={point_1_local}, coords=({lane_1_sorted[point_1_local, 0]}, {lane_1_sorted[point_1_local, 1]})")
            print(
                f"Point 2 ({point_2_type}): index={point_2}, local={point_2_local}, coords=({lane_2_sorted[point_2_local, 0]}, {lane_2_sorted[point_2_local, 1]})")

            # Select parts based on start/end
            if point_1_type == 'end':
                lane_1_part = lane_1_sorted[:point_1_local + 1]
            else:  # start
                lane_1_part = lane_1_sorted[point_1_local:]
            print(f"Lane 1 part indices: {lane_1_part[:, 4]}")

            # Determine lane_2_part direction based on connection
            if point_2_type == 'start' and point_1_type == 'end':
                lane_2_part = lane_2_sorted
            elif point_2_type == 'end' and point_1_type == 'start':
                lane_2_part = lane_2_sorted
            elif point_2_type == 'start' and point_1_type == 'start':
                lane_2_part = lane_2_sorted[::-1]  # Reverse for start-to-start
            elif point_2_type == 'end' and point_1_type == 'end':
                lane_2_part = lane_2_sorted[::-1]  # Reverse for end-to-end
            print(f"Lane 2 part indices: {lane_2_part[:, 4]}")

            # Check connection point proximity
            connection_x1 = lane_1_part[-1, 0]
            connection_y1 = lane_1_part[-1, 1]
            connection_x2 = lane_2_part[0, 0]
            connection_y2 = lane_2_part[0, 1]
            distance = np.sqrt((connection_x2 - connection_x1) ** 2 + (connection_y2 - connection_y1) ** 2)
            print(f"Connection distance between lanes: {distance}")

            # Combine parts, preserving original index order
            merged_data = np.vstack([lane_1_part, lane_2_part])
            merged_data[:, -1] = lane_id_1

            # Debug: Print merged data before indexing
            print(f"Merged data x-coordinates: {merged_data[:, 0]}")
            print(f"Merged data original indices: {merged_data[:, 4]}")

            # Recalculate yaw based on new order
            N = len(merged_data)
            if N > 1:
                dx = np.diff(merged_data[:, 0])
                dy = np.diff(merged_data[:, 1])
                merged_data[:-1, 2] = np.arctan2(dy, dx)
                merged_data[-1, 2] = merged_data[-2, 2]
            else:
                merged_data[:, 2] = 0.0 if N > 0 else 0.0

            # Assign indices for merged lane (0 to N-1, +1 increments)
            merged_data[:, 3] = np.arange(N)
            merged_data[:, 4] = np.arange(N)

            # Check for duplicate indices
            if len(np.unique(merged_data[:, 4])) != len(merged_data):
                print(f"Warning: Duplicate indices in merged lane {lane_id_1}: {merged_data[:, 4]}")

            # Collect other lanes' data
            other_lanes_mask = ~np.logical_or(lane_1_mask, lane_2_mask)
            other_data = self.data[other_lanes_mask].copy() if np.any(other_lanes_mask) else np.array([])

            # Reindex other lanes starting from N
            if other_data.size > 0:
                unique_lanes = np.unique(other_data[:, -1])
                offset = N
                for lane_id in unique_lanes:
                    lane_mask = other_data[:, -1] == lane_id
                    lane_size = np.sum(lane_mask)
                    other_data[lane_mask, 3] = np.arange(offset, offset + lane_size)
                    other_data[lane_mask, 4] = np.arange(offset, offset + lane_size)
                    offset += lane_size
                # Check for duplicates in other lanes
                if len(np.unique(other_data[:, 4])) != len(other_data):
                    print(f"Warning: Duplicate indices in other lanes: {other_data[:, 4]}")

            # Combine merged and other lanes
            self.data = np.vstack([merged_data, other_data]) if other_data.size > 0 else merged_data

            # Debug: Print final indices
            print(f"Merged lane {lane_id_1} indices: {self.data[self.data[:, -1] == lane_id_1][:, 4]}")
            if other_data.size > 0:
                print(f"Other lanes indices: {self.data[self.data[:, -1] != lane_id_1][:, 4]}")

            # Update file names
            self.file_names = [self.file_names[i] if i < len(self.file_names) else f"Lane_{i}" for i in
                               range(max(np.unique(self.data[:, -1]).astype(int)) + 1)]
            self.history.append(self.data.copy())
            self.redo_stack = []
            self._auto_save_backup()
            print(f"Merged lane {lane_id_2} into lane {lane_id_1}")
            return point_1, point_1 + 1
        except Exception as e:
            print(f"Error merging lanes: {e}")

    def save_all_lanes(self):
        folder = "workspace-Temp"
        try:
            os.makedirs(folder, exist_ok=True)
            for filename in os.listdir(folder):
                file_path = os.path.join(folder, filename)
                try:
                    if os.path.isfile(file_path) or os.path.islink(file_path):
                        os.unlink(file_path)
                    elif os.path.isdir(file_path):
                        shutil.rmtree(file_path)
                except Exception as e:
                    print(f"Failed to delete {file_path}: {e}")
            unique_lane_ids = np.unique(self.data[:, -1])
            for lane_id in unique_lane_ids:
                mask = self.data[:, -1] == lane_id
                lane_data = self.data[mask]
                if lane_data.size > 0:
                    filename = os.path.join(folder, f"Lane_{int(lane_id)}.npy")
                    np.save(filename, lane_data[:, :3])
                    print(f"Saved lane {lane_id} to {filename}")
                else:
                    print(f"No data for lane {lane_id}, skipping save")
        except Exception as e:
            print(f"Error saving lanes: {e}")

    def clear_data(self):
        try:
            self.data = np.array([])
            self.history = [np.array([])]
            self.redo_stack = []
            self.file_names = []
            self._auto_save_backup()
            print("Cleared all data")
        except Exception as e:
            print(f"Error clearing data: {e}")

    def undo(self):
        try:
            if len(self.history) <= 1:
                print("Nothing to undo")
                return self.data, False
            self.redo_stack.append(self.history.pop())
            self.data = self.history[-1].copy()
            self._auto_save_backup()
            return self.data, True
        except Exception as e:
            print(f"Error during undo: {e}")
            return self.data, False

    def redo(self):
        try:
            if not self.redo_stack:
                print("Nothing to redo")
                return self.data, False
            self.data = self.redo_stack.pop()
            self.history.append(self.data.copy())
            self._auto_save_backup()
            return self.data, True
        except Exception as e:
            print(f"Error during redo: {e}")
            return self.data, False

    def save(self):
        try:
            filename = "./files/WorkingLane.npy"
            if self.data.size > 0:
                np.save(filename, self.data[:, :3])
            else:
                np.save(filename, np.array([]))
            print(f"Saved x, y, yaw to {filename}")
            self._auto_save_backup()
            pickerGenerateViewer()
            return filename
        except Exception as e:
            print(f"Error saving data: {e}")
            return None

    def _auto_save_backup(self):
        try:
            if time.time() - self.last_backup < self.backup_interval:
                return
            os.makedirs("workspace-Backup", exist_ok=True)
            timestamp = time.strftime("%Y%m%d_%H%M%S")
            filename = os.path.join("workspace-Backup", f"backup_{timestamp}.npy")
            if self.data.size > 0:
                np.save(filename, self.data[:, :3])
                print(f"Auto-saved backup to {filename}")
            self.last_backup = time.time()
        except Exception as e:
            print(f"Backup failed: {e}")
