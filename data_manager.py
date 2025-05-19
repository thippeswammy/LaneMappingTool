import numpy as np


class DataManager:
    def __init__(self, data, file_names):
        # Validate input data
        if data.size > 0:
            if len(data.shape) != 2 or data.shape[1] < 3:
                raise ValueError(
                    f"Expected data to be a 2D array with at least 3 columns (x, y, lane_id), got shape {data.shape}")
            if not np.issubdtype(data[:, -1].dtype, np.integer):
                # print("Warning: Lane IDs are not integers, converting to int")
                data[:, -1] = data[:, -1].astype(int)
            # Reduce data to 3 columns: x, y, lane_id
            self.data = data[:, [0, 1, -1]]  # Keep only x, y, and the last column (lane_id)
        else:
            self.data = np.array([])

        self.file_names = file_names
        self.total_cols = 3  # Now fixed to 3 columns: x, y, lane_id
        self.history = [self.data.copy()] if self.data.size > 0 else [np.array([])]
        self.redo_stack = []

        # Debug: Log initial state
        print(f"DataManager initialized with {len(self.data)} points, total_cols={self.total_cols}")
        # if self.data.size > 0:
        #     print(f"Sample data:\n{self.data[:5]}")

    def add_point(self, x, y, lane_id):
        new_point = np.zeros((1, self.total_cols))
        new_point[0, 0] = x
        new_point[0, 1] = y
        new_point[0, -1] = lane_id
        self.data = np.vstack([self.data, new_point]) if self.data.size > 0 else new_point
        self.history.append(self.data.copy())
        self.redo_stack = []
        print(f"Added point: ({x}, {y}, {lane_id}), new data shape: {self.data.shape}")

    def delete_points(self, indices):
        if not indices:
            return
        mask = np.ones(len(self.data), dtype=bool)
        mask[indices] = False
        self.data = self.data[mask]
        self.history.append(self.data.copy())
        self.redo_stack = []
        print(f"Deleted {len(indices)} points, new data shape: {self.data.shape}")

    def change_ids(self, indices, new_id):
        if not indices:
            return
        self.data[indices, -1] = new_id
        self.history.append(self.data.copy())
        self.redo_stack = []
        print(f"Changed IDs for {len(indices)} points to {new_id}")

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
        filename = "output.npy"
        np.save(filename, self.data)
        return filename
