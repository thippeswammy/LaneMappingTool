import numpy as np


class EventHandler:
    def __init__(self, data_manager, plot_manager):
        self.data_manager = data_manager
        self.plot_manager = plot_manager
        self.selection_mode = False
        self.selected_id = 0
        self.id_set = False

    def on_toggle_mode(self, event):
        self.selection_mode = not self.selection_mode
        self.plot_manager.rs.set_active(self.selection_mode)
        self.plot_manager.btn_toggle.label.set_text(
            'Select Mode' if self.selection_mode else 'Add/Delete Mode')
        self.plot_manager.btn_toggle.color = 'lightcoral' if self.selection_mode else 'lightgreen'
        if not self.selection_mode:
            self.id_set = False
            if self.plot_manager.selected_indices:
                self.plot_manager.selected_indices = []
                for sc in self.plot_manager.scatter_plots:
                    sc.set_sizes([10] * len(sc.get_offsets()))
                print("Cleared selection")
        print(f"Entered {'selection' if self.selection_mode else 'add/delete'} mode")
        self.plot_manager.update_title()

    def on_click(self, event):
        if self.selection_mode:
            print("Click ignored: in selection mode")
            return
        if event.inaxes != self.plot_manager.ax or event.button != 1 or not self.id_set:
            print("Click ignored: invalid action")
            return
        self.plot_manager.selected_indices = []
        for sc in self.plot_manager.scatter_plots:
            sc.set_sizes([10] * len(sc.get_offsets()))
        self.data_manager.add_point(event.xdata, event.ydata, self.selected_id)
        self.plot_manager.update_plot(self.data_manager.data)
        print(f"Added point with ID {self.selected_id} ({self.data_manager.file_names[self.selected_id]})")

    def on_pick(self, event):
        if event.mouseevent.button != 3 or self.plot_manager.rs.active:
            return
        if not self.selection_mode:
            self.plot_manager.selected_indices = []
            for sc in self.plot_manager.scatter_plots:
                sc.set_sizes([10] * len(sc.get_offsets()))
        artist = event.artist
        ind = event.ind[0]
        file_index = self.plot_manager.scatter_plots.index(artist)
        global_ind = self.plot_manager.indices[file_index][ind]
        self.data_manager.delete_points([global_ind])
        self.plot_manager.update_plot(self.data_manager.data)
        print("Deleted single point")

    def on_select(self, eclick, erelease):
        if not self.selection_mode:
            return
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
        self.plot_manager.update_plot(self.data_manager.data)

    def on_key(self, event):
        key_map = {
            '1-9': lambda k: int(k) - 1 if int(k) - 1 < len(self.data_manager.file_names) else None,
            'ctrl+z': self.on_undo,
            'ctrl+y': self.on_redo,
            'tab': self.on_toggle_mode,
            'escape': self.on_escape,
            'delete': self.on_delete
        }

        if event.key in '123456789':
            new_id = key_map['1-9'](event.key)
            if new_id is not None:
                self.selected_id = new_id
                self.id_set = True
                print(f"Set ID {self.selected_id} ({self.data_manager.file_names[self.selected_id]})")
                if self.selection_mode and self.plot_manager.selected_indices:
                    self.data_manager.change_ids(self.plot_manager.selected_indices, self.selected_id)
                    self.plot_manager.update_plot(self.data_manager.data)
                    print(f"Changed {len(self.plot_manager.selected_indices)} points to ID {self.selected_id}")
                self.plot_manager.update_title()
            else:
                print(f"Invalid ID: only {len(self.data_manager.file_names)} files available")
                self.id_set = False
        elif event.key.lower() in key_map:
            key_map[event.key.lower()](event)

    def on_escape(self, event):
        self.selection_mode = False
        self.id_set = False
        self.plot_manager.rs.set_active(False)
        if self.plot_manager.selected_indices:
            self.plot_manager.selected_indices = []
            for sc in self.plot_manager.scatter_plots:
                sc.set_sizes([10] * len(sc.get_offsets()))
            print("Cleared selection")
        print("Entered add/delete mode")
        self.plot_manager.update_title()

    def on_delete(self, event):
        if self.selection_mode and self.plot_manager.selected_indices:
            self.data_manager.delete_points(self.plot_manager.selected_indices)
            self.plot_manager.selected_indices = []
            self.plot_manager.update_plot(self.data_manager.data)
            print("Deleted selected points")

    def on_undo(self, event):
        data, success = self.data_manager.undo()
        if success:
            self.plot_manager.update_plot(data)
            print("Undo performed")

    def on_redo(self, event):
        data, success = self.data_manager.redo()
        if success:
            self.plot_manager.update_plot(data)
            print("Redo performed")

    def on_save(self, event):
        filename = self.data_manager.save()
        print(f"Saved to {filename}")