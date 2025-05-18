import numpy as np


class DataManager:
    def __init__(self, data, file_names):
        self.data = data
        self.file_names = file_names
        self.total_cols = int(
            data.shape[1]) if data.size > 0 else 3  # Default to 3 columns (x, y, lane_id) if data is empty
        self.history = [data.copy()] if data.size > 0 else [np.array([])]
        self.redo_stack = []

    def add_point(self, x, y, lane_id):
        new_point = np.zeros((1, self.total_cols))
        new_point[0, 0] = x
        new_point[0, 1] = y
        new_point[0, -1] = lane_id
        self.data = np.vstack([self.data, new_point]) if self.data.size > 0 else new_point
        self.history.append(self.data.copy())
        self.redo_stack = []

    def delete_points(self, indices):
        if not indices:
            return
        mask = np.ones(len(self.data), dtype=bool)
        mask[indices] = False
        self.data = self.data[mask]
        self.history.append(self.data.copy())
        self.redo_stack = []

    def change_ids(self, indices, new_id):
        if not indices:
            return
        self.data[indices, -1] = new_id
        self.history.append(self.data.copy())
        self.redo_stack = []

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
