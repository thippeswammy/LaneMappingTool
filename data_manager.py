import numpy as np


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

        print(f"DataManager initialized with {len(self.data)} points, total_cols={self.total_cols}")
        if self.data.size > 0:
            print(f"Sample data:\n{self.data[:5]}")

    def add_point(self, x, y, lane_id):
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
        print(
            f"Added point: ({x}, {y}, frame_idx={new_point[0, 3]}, index={new_point[0, 4]}, lane_id={lane_id}), "
            f"new data shape: {self.data.shape}"
        )

    def delete_points(self, indices):
        if not indices:
            return
        mask = np.ones(len(self.data), dtype=bool)
        mask[indices] = False
        self.data = self.data[mask]
        if self.data.size > 0:
            new_indices = np.arange(len(self.data))
            self.data[:, 3] = new_indices
            self.data[:, 4] = new_indices
        self.history.append(self.data.copy())
        self.redo_stack = []
        print(f"Deleted {len(indices)} points, new data shape: {self.data.shape}")

    def change_ids(self, indices, new_id):
        if not indices:
            return
        self.data[indices, -1] = new_id
        self.history.append(self.data.copy())
        self.redo_stack = []
        print(f"Changed lane IDs for {len(indices)} points to {new_id}")

    def merge_lanes(self, lane_id_0, lane_id_target, point_0, point_target):
        if self.data.size == 0:
            print("No data to merge")
            return
        lane_0_mask = self.data[:, -1] == lane_id_0
        lane_target_mask = self.data[:, -1] == lane_id_target
        if not np.any(lane_0_mask) or not np.any(lane_target_mask):
            print(f"One or both lanes ({lane_id_0}, {lane_id_target}) are empty")
            return

        lane_0_data = self.data[lane_0_mask]
        lane_target_data = self.data[lane_target_mask]

        lane_0_indices = np.where(lane_0_mask)[0]
        lane_target_indices = np.where(lane_target_mask)[0]

        point_0_local = np.where(lane_0_indices == point_0)[0][0]
        point_target_local = np.where(lane_target_indices == point_target)[0][0]

        lane_0_sorted = lane_0_data[np.argsort(lane_0_data[:, 4])]
        lane_target_sorted = lane_target_data[np.argsort(lane_target_data[:, 4])]

        if point_0_local < len(lane_0_sorted) - 1:
            lane_0_part = lane_0_sorted[:point_0_local + 1]
        else:
            lane_0_part = lane_0_sorted

        if point_target_local > 0:
            lane_target_part = lane_target_sorted[point_target_local:]
        else:
            lane_target_part = lane_target_sorted

        merged_data = np.vstack([lane_0_part, lane_target_part])
        merged_data[:, -1] = lane_id_0

        N = len(merged_data)
        for i in range(N - 1):
            dx = merged_data[i + 1, 0] - merged_data[i, 0]
            dy = merged_data[i + 1, 1] - merged_data[i, 1]
            merged_data[i, 2] = np.arctan2(dy, dx)
        merged_data[-1, 2] = merged_data[-2, 2] if N > 1 else 0.0

        new_indices = np.arange(N)
        merged_data[:, 3] = new_indices
        merged_data[:, 4] = new_indices

        other_lanes_mask = ~np.logical_or(lane_0_mask, lane_target_mask)
        other_data = self.data[other_lanes_mask]
        self.data = np.vstack([merged_data, other_data]) if other_data.size > 0 else merged_data

        self.file_names = [self.file_names[0] if i == lane_id_0 else f"Lane_{i}" for i in
                           range(max(len(self.file_names), 1))]
        self.history.append(self.data.copy())
        self.redo_stack = []
        print(f"Merged lane {lane_id_target} into lane {lane_id_0}, new data shape: {self.data.shape}")

    def undo(self):
        if len(self.history) <= 1:
            return self.data, False
        self.redo_stack.append(self.history.pop())
        self.data = self.history[-1].copy()
        return self.data, True

    def redo(self):
        if not self.redo_stack:
            return self.data, False
        self.data = self.redo_stack.pop()
        self.history.append(self.data.copy())
        return self.data, True

    def save(self):
        filename = "WorkingLane.npy"
        if self.data.size > 0:
            np.save(filename, self.data[:, :3])
        else:
            np.save(filename, np.array([]))
        print(f"Saved x, y, yaw to {filename}")
        return filename
