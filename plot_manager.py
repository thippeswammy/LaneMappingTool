import matplotlib.pyplot as plt
import matplotlib.widgets as widgets
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

        self.fig = plt.figure(figsize=(10, 8))
        self.ax = self.fig.add_subplot(111)
        self.setup_plot()
        self.setup_widgets()
        self.setup_events()

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

        if current_xlim and current_ylim:
            self.ax.set_xlim(current_xlim)
            self.ax.set_ylim(current_ylim)

        self.update_title()

    def setup_widgets(self):
        ax_save = self.fig.add_axes([0.81, 0.02, 0.1, 0.04])
        self.btn_save = widgets.Button(ax_save, 'Save', color='lightgreen',
                                       hovercolor='lightblue')
        self.btn_save.on_clicked(self.event_handler.on_save)

        ax_toggle = self.fig.add_axes([0.01, 0.02, 0.1, 0.04])
        self.btn_toggle = widgets.Button(ax_toggle, 'Select Mode',
                                         color='lightcoral', hovercolor='lightblue')
        self.btn_toggle.on_clicked(self.event_handler.on_toggle_mode)

        ax_undo = self.fig.add_axes([0.71, 0.02, 0.05, 0.04])
        self.btn_undo = widgets.Button(ax_undo, 'Undo', color='lightyellow',
                                       hovercolor='lightblue')
        self.btn_undo.on_clicked(self.event_handler.on_undo)

        ax_redo = self.fig.add_axes([0.66, 0.02, 0.05, 0.04])
        self.btn_redo = widgets.Button(ax_redo, 'Redo', color='lightyellow',
                                       hovercolor='lightblue')
        self.btn_redo.on_clicked(self.event_handler.on_redo)

        ax_linecurve = self.fig.add_axes([0.11, 0.02, 0.1, 0.04])
        self.btn_linecurve = widgets.Button(ax_linecurve, 'Line',
                                            color='lightblue', hovercolor='cyan')
        self.btn_linecurve.on_clicked(self.event_handler.on_toggle_linecurve)

        ax_straighten = self.fig.add_axes([0.21, 0.02, 0.1, 0.04])
        self.btn_straighten = widgets.Button(ax_straighten, 'Smooth',
                                             color='lightpink', hovercolor='cyan')
        self.btn_straighten.on_clicked(self.event_handler.on_straighten)

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

    def update_title(self):
        mode = "Draw" if self.event_handler.draw_mode else (
            "Selection" if self.event_handler.selection_mode else "Add/Delete")
        self.ax.set_title(
            f'ID {self.event_handler.selected_id + 1}, Mode: {mode}, '
            f'[{len(self.selected_indices)} points selected]'
        )
        self.fig.canvas.draw_idle()

    def update_plot(self, data):
        self.data = data
        valid_indices = [idx for idx in self.selected_indices if idx < len(self.data)]
        self.selected_indices = valid_indices
        self.setup_plot()
        if self.selected_indices:
            for idx in self.selected_indices:
                if idx < len(self.data):
                    import matplotlib.pyplot as plt
                    import matplotlib.widgets as widgets
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

                            self.fig = plt.figure(figsize=(10, 8))
                            self.ax = self.fig.add_subplot(111)
                            self.setup_plot()
                            self.setup_widgets()
                            self.setup_events()

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

                            if current_xlim and current_ylim:
                                self.ax.set_xlim(current_xlim)
                                self.ax.set_ylim(current_ylim)

                            self.update_title()

                        def setup_widgets(self):
                            ax_save = self.fig.add_axes([0.81, 0.02, 0.1, 0.04])
                            self.btn_save = widgets.Button(ax_save, 'Save', color='lightgreen',
                                                           hovercolor='lightblue')
                            self.btn_save.on_clicked(self.event_handler.on_save)

                            ax_toggle = self.fig.add_axes([0.01, 0.02, 0.1, 0.04])
                            self.btn_toggle = widgets.Button(ax_toggle, 'Select Mode',
                                                             color='lightcoral', hovercolor='lightblue')
                            self.btn_toggle.on_clicked(self.event_handler.on_toggle_mode)

                            ax_undo = self.fig.add_axes([0.71, 0.02, 0.05, 0.04])
                            self.btn_undo = widgets.Button(ax_undo, 'Undo', color='lightyellow',
                                                           hovercolor='lightblue')
                            self.btn_undo.on_clicked(self.event_handler.on_undo)

                            ax_redo = self.fig.add_axes([0.66, 0.02, 0.05, 0.04])
                            self.btn_redo = widgets.Button(ax_redo, 'Redo', color='lightyellow',
                                                           hovercolor='lightblue')
                            self.btn_redo.on_clicked(self.event_handler.on_redo)

                            ax_linecurve = self.fig.add_axes([0.11, 0.02, 0.1, 0.04])
                            self.btn_linecurve = widgets.Button(ax_linecurve, 'Line',
                                                                color='lightblue', hovercolor='cyan')
                            self.btn_linecurve.on_clicked(self.event_handler.on_toggle_linecurve)

                            ax_straighten = self.fig.add_axes([0.21, 0.02, 0.1, 0.04])
                            self.btn_straighten = widgets.Button(ax_straighten, 'Smooth',
                                                                 color='lightpink', hovercolor='cyan')
                            self.btn_straighten.on_clicked(self.event_handler.on_straighten)

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

                        def update_title(self):
                            mode = "Draw" if self.event_handler.draw_mode else (
                                "Selection" if self.event_handler.selection_mode else "Add/Delete")
                            self.ax.set_title(
                                f'ID {self.event_handler.selected_id + 1}, Mode: {mode}, '
                                f'[{len(self.selected_indices)} points selected]'
                            )
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
                            self.update_title()

                    file_idx = int(self.data[idx, -1])
                    sc = self.scatter_plots[file_idx]
                    current_sizes = sc.get_sizes()
                    offset_idx = np.where(self.indices[file_idx] == idx)[0]
                    if offset_idx.size > 0 and offset_idx[0] < len(current_sizes):
                        current_sizes[offset_idx[0]] = 30
                        sc.set_sizes(current_sizes)
        self.update_title()