import numpy as np


class DataManager:
    def __init__(self, data, file_names):
        # Validate data: expect x, y, yaw, frame_idx, index, lane_id
        if data.size > 0:
            if len(data.shape) != 2 or data.shape[1] < 6:
                raise ValueError(
                    f"Expected data to be a 2D array with at least 6 columns (x, y, yaw, frame_idx, index, lane_id), "
                    f"got shape {data.shape}"
                )
            if not np.issubdtype(data[:, -1].dtype, np.integer):
                data[:, -1] = data[:, -1].astype(int)
            if not np.issubdtype(data[:, 3].dtype, np.integer) or not np.issubdtype(data[:, -2].dtype, np.integer):
                data[:, 3] = data[:, 3].astype(int)
                data[:, -2] = data[:, -2].astype(int)
            # Ensure frame_idx and index are identical
            if not np.array_equal(data[:, 3], data[:, -2]):
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
        new_point[0, 3] = new_index  # frame_idx
        new_point[0, -2] = new_index  # index
        self.data = np.vstack([self.data, new_point]) if self.data.size > 0 else new_point
        self.history.append(self.data.copy())
        self.redo_stack = []
        print(
            f"Added point: ({x}, {y}, frame_idx={new_point[0, 3]}, index={new_point[0, -2]}, lane_id={lane_id}), "
            f"new data shape: {self.data.shape}"
        )

    def delete_points(self, indices):
        if not indices:
            return
        mask = np.ones(len(self.data), dtype=bool)
        mask[indices] = False
        self.data = self.data[mask]
        if self.data.size > 0:
            # Reassign both frame_idx and index
            new_indices = np.arange(len(self.data))
            self.data[:, 3] = new_indices  # frame_idx
            self.data[:, -2] = new_indices  # index
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
            np.save(filename, self.data[:, :3])  # Save x, y, yaw
        else:
            np.save(filename, np.array([]))
        print(f"Saved x, y, yaw to {filename}")
        return filename
