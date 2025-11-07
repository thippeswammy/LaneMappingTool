import pickle
import matplotlib.pyplot as plt
import networkx as nx
# Import the Button widget
from matplotlib.widgets import Button

# Define the path to your graph file
# Note: You might need to adjust this path depending on where you run the script.
graph_file_path = r"F:\RunningProjects\AutoSegmentor\DataVisualizationEditingTool\files\output.pickle"


class GraphViewer:
    """
    A class to display a NetworkX graph with a refresh button.
    """

    def __init__(self, graph_file_path):
        self.graph_file_path = graph_file_path
        self.G1 = None
        self.pos = None

        # 1. Setup the figure and axes
        self.fig, self.ax = plt.subplots(figsize=(12, 8))
        plt.subplots_adjust(bottom=0.15)  # Make space for the button

        # 2. Add the refresh button
        # Define the location [left, bottom, width, height] of the button axis
        ax_button = self.fig.add_axes([0.8, 0.02, 0.15, 0.05])
        self.refresh_button = Button(ax_button, 'Refresh Data')

        # 3. Connect the button click event to the plot function
        self.refresh_button.on_clicked(self.plot_graph)

        # Initial plot
        self.plot_graph(None)  # Pass None as the event object

    def load_graph_data(self):
        """Loads the graph data from the pickle file."""
        print(f"Loading graph from: {self.graph_file_path}")
        try:
            with open(self.graph_file_path, "rb") as f:
                data = pickle.load(f, encoding='latin1')

            # Extract graph
            if isinstance(data, (nx.Graph, nx.DiGraph)):
                self.G1 = data
            elif isinstance(data, dict):
                for k in data:
                    if isinstance(data[k], (nx.Graph, nx.DiGraph)):
                        self.G1 = data[k]
                        print(f"Graph extracted from key: {k}")
                        break
                else:
                    raise ValueError("No NetworkX graph found in pickle data.")
            else:
                raise ValueError("Pickle file does not contain a NetworkX graph.")

            print(f"Graph loaded: {self.G1}")
            return True

        except FileNotFoundError:
            print(f"Error: File not found at {self.graph_file_path}")
            self.G1 = None
            return False
        except Exception as e:
            print(f"An error occurred during loading: {e}")
            self.G1 = None
            return False

    def calculate_positions(self):
        """Calculates or re-calculates the node positions."""
        if self.G1 is None:
            self.pos = {}
            return

        try:
            # Try to use stored 'x' and 'y' attributes
            self.pos = {i: (attr['x'], attr['y']) for i, attr in self.G1.nodes(data=True)}
            print("Using 'x' and 'y' attributes for layout.")
        except KeyError:
            # Fallback to spring layout
            print("No 'x' and 'y' attributes, using spring_layout.")
            self.pos = nx.spring_layout(self.G1)

    def plot_graph(self, event):
        """
        Reloads data, clears the old plot, and draws the new graph.
        The 'event' parameter is required by the button widget callback.
        """
        # 1. Reload the data
        if not self.load_graph_data():
            return  # Stop if loading failed

        # 2. Calculate/Recalculate positions
        self.calculate_positions()

        # 3. Clear the previous plot (important for refresh)
        self.ax.clear()

        if self.G1 and self.pos:
            # 4. Draw the new graph
            nx.draw(
                self.G1,
                self.pos,
                with_labels=True,
                node_size=50,
                font_size=8,
                ax=self.ax
            )
            self.ax.set_title("Visualized Graph (Refreshed)")
        else:
            self.ax.set_title("No Graph Data Available")

        # 5. Redraw the canvas
        self.fig.canvas.draw_idle()


if __name__ == "__main__":
    # Create an instance of the viewer
    viewer = GraphViewer(graph_file_path)
    # Display the plot window
    plt.show()