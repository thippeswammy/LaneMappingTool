import os
import pickle

import matplotlib.pyplot as plt
import networkx as nx
# Import the Button widget
from matplotlib.widgets import Button

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

# Adjust this join if your folder structure is different
graph_file_path = os.path.join(BASE_DIR, "..", "files", "output.pickle")


class GraphViewer:
    """
    A class to display a NetworkX graph with a refresh button.
    """

    def __init__(self, graph_file_path):
        self.graph_file_path = graph_file_path
        self.G1 = None
        self.pos = None

        # Setup the figure and axes
        self.fig, self.ax = plt.subplots(figsize=(12, 8))
        plt.subplots_adjust(bottom=0.15)  # Make space for the button

        # Add the refresh button
        # Define the location [left, bottom, width, height] of the button axis
        ax_button = self.fig.add_axes([0.8, 0.02, 0.15, 0.05])
        self.refresh_button = Button(ax_button, 'Refresh Data')

        # Connect the button click event to the plot function
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
            # The updated data_manager saves the Graph object directly
            if isinstance(data, (nx.Graph, nx.DiGraph)):
                self.G1 = data
            elif isinstance(data, dict):
                # Fallback for older formats wrapping the graph in a dict
                for k in data:
                    if isinstance(data[k], (nx.Graph, nx.DiGraph)):
                        self.G1 = data[k]
                        print(f"Graph extracted from key: {k}")
                        break
                else:
                    raise ValueError("No NetworkX graph found in pickle data.")
            else:
                raise ValueError(f"Pickle file contains unexpected data type: {type(data)}")

            print(f"Graph loaded successfully. Nodes: {self.G1.number_of_nodes()}, Edges: {self.G1.number_of_edges()}")
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
            # Try to use stored 'x' and 'y' attributes from the graph nodes
            self.pos = {i: (attr['x'], attr['y']) for i, attr in self.G1.nodes(data=True)}
            print("Using 'x' and 'y' attributes for layout.")
        except KeyError:
            # Fallback to spring layout if x/y are missing
            print("No 'x' and 'y' attributes, using spring_layout.")
            self.pos = nx.spring_layout(self.G1)

    def plot_graph(self, event):
        """
        Reloads data, clears the old plot, and draws the new graph.
        The 'event' parameter is required by the button widget callback.
        """
        # Reload the data
        if not self.load_graph_data():
            return  # Stop if loading failed

        # Calculate/Recalculate positions
        self.calculate_positions()

        # Clear the previous plot (important for refresh)
        self.ax.clear()

        if self.G1 and self.pos:
            # Draw the new graph
            # Explicitly drawing with arrows to verify directions
            nx.draw(
                self.G1,
                self.pos,
                with_labels=True,
                node_size=50,
                font_size=8,
                ax=self.ax,
                arrows=True,  #
                arrowstyle='-|>',
                arrowsize=10
            )
            self.ax.set_title("Visualized Graph (Refreshed)")
            self.ax.set_xlabel("X Coordinate")
            self.ax.set_ylabel("Y Coordinate")
            self.ax.grid(True)
            # self.ax.axis('equal')
        else:
            self.ax.set_title("No Graph Data Available")

        # Redraw the canvas
        self.fig.canvas.draw_idle()


if __name__ == "__main__":
    # Create an instance of the viewer
    viewer = GraphViewer(graph_file_path)
    # Display the plot window
    plt.show()
