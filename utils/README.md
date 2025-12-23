# Utilities Documentation

[← Back to Project Root](../README.md)

This directory contains shared Python utilities, scripts, and legacy tools used by the Lane Mapping Tool backend and analysis modules.

## Core Modules

These files form the backbone of the Python backend logic (`web/backend/`).

-   **`data_manager.py`**: The central class managing the graph state (nodes, edges). Handles operations like adding/deleting nodes, history (undo/redo), and saving data.
-   **`data_loader.py`**: Responsible for loading raw `.npy` lane files and existing graph sessions.
-   **`event_handler.py`**: Manages user interactions (mouse clicks, keyboard shortcuts) and orchestrates actions between the PlotManager and DataManager.
-   **`plot_manager.py`**: Handles Matplotlib visualization, including scatter plots, zooming, panning, and rendering the graph.
-   **`curve_manager.py`**: Implements B-Spline smoothing logic for path refinement.

## Standalone Scripts

Utilities for specific maintenance or testing tasks.

-   **`fix_pickle_yaw.py`**: Recalculates yaw values for nodes in a pickle file based on path direction. Used to fix steering jerk issues.
-   **`visualize_yaw_matplotlib.py`**: A dedicated script to visualize the yaw vectors of a graph for verification.
-   **`vehicle_test.py`**: Simulation script to test vehicle pathfinding and steering logic.
-   **`make_dummy_pickle.py`**: Generates dummy graph data for testing purposes.
-   **`json_to_pickle.py`**: Converter tool to transform JSON graph data into Python pickle format.

## Legacy & Experimental

-   **`network_.py`**, **`network_view2.py`**, **`network_view3.py`**: Older iterations of network visualization and logic. Preserved for reference.
