import numpy as np
import networkx as nx
import math
import matplotlib.pyplot as plt
import plotly.graph_objs as go

graph_file_path = "./workspace/output.pickle"
G1 = nx.read_gpickle(graph_file_path)

# # Retrieve data of the node based on its index
# node_data = G1.node[240]

# print("Node data: 240")
# print("x:", node_data['x'])
# print("y:", node_data['y'])
# print("yaw:", node_data['yaw'])

# # Retrieve data of the node based on its index
# node_data = G1.node[164]

# print("Node data: 164")
# print("x:", node_data['x'])
# print("y:", node_data['y'])
# print("yaw:", node_data['yaw'])





# Find the closest nodes to the current position and destination
def closest_node(x, y):
    distances = [(node, math.sqrt((data['x'] - x)**2 + (data['y'] - y)**2)) for node, data in G1.nodes(data=True)]
    # print(distances)
    closest = min(distances, key=lambda x: x[1])
    print(closest)
    return closest[0]

# # Your current position
# current_x, current_y = 17.3, -11.5

# # Your destination
# destination_x, destination_y = 112.4, 161.1

# current_node = closest_node(current_x, current_y)
# destination_node = closest_node(destination_x, destination_y)

# # Find the shortest path
# shortest_path = nx.shortest_path(G1, source=current_node, target=destination_node, weight='weight')
# a = len(shortest_path)*2
# print(type(shortest_path))
# print(len(shortest_path))

# # Find all simple paths from source to destination (including longer paths)
# longer_paths = list(nx.all_simple_paths(G1, source=current_node, target=destination_node, cutoff=a))  # No cutoff to consider all paths

# # print(type(shortest_path))
# # print(shortest_path)

# print(type(longer_paths))

#-------------------------------------------
# Visualize the graph matplot lib G1
pos = {i: (data['x'], data['y']) for i, data in G1.nodes(data=True)}
nx.draw(G1, pos, with_labels=True)
plt.show()

# Visualize the graph
# pos = {i: (data['x'], data['y']) for i, data in G1.nodes(data=True)}
# nx.draw(G1, pos, with_labels=True, node_size=500, node_color='lightblue')

# # Plot the shortest path
# shortest_edges = [(shortest_path[i], shortest_path[i+1]) for i in range(len(shortest_path)-1)]
# nx.draw_networkx_edges(G1, pos, edgelist=shortest_edges, edge_color='red', width=2)

# highlighted_nodes = set(shortest_path)
# node_colors = ['red' if node in highlighted_nodes else 'lightblue' for node in G1.nodes()]
# nx.draw(G1, pos, with_labels=True, node_size=500, node_color=node_colors)

# plt.show()

# # Create a list of scatter plot traces for nodes
# node_trace = go.Scatter(
#     x=[data['x'] for node, data in G1.nodes(data=True)],
#     y=[data['y'] for node, data in G1.nodes(data=True)],
#     mode='markers',
#     marker=dict(
#         size=10,
#         color='blue'  # Customize the color of nodes
#     )
# )

# # Create a list of line plot traces for edges
# edge_trace = go.Scatter(
#     x=[],
#     y=[],
#     mode='lines',
#     line=dict(width=0.5, color='black'),
#     hoverinfo='none'
# )

# for edge in G1.edges():
#     x0, y0 = pos[edge[0]]
#     x1, y1 = pos[edge[1]]
#     edge_trace['x'] += (x0, x1, None)
#     edge_trace['y'] += (y0, y1, None)

# # Create the plot layout
# layout = go.Layout(
#     showlegend=False,
#     hovermode='closest',
#     margin=dict(b=0, l=0, r=0, t=0),
#     xaxis=dict(showgrid=False, zeroline=False, showticklabels=False),
#     yaxis=dict(showgrid=False, zeroline=False, showticklabels=False)
# )

# # Create the plot figure
# fig = go.Figure(data=[edge_trace, node_trace], layout=layout)

# # Display the plotly figure
# fig.show()
