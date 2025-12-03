# Lane Mapping Tool - Backend

This directory contains the Flask-based backend for the Lane Mapping Tool. It handles graph operations, data persistence, and communicates with the React frontend.

## 🔧 Setup

### Prerequisites

*   Python 3.8 or higher

### Installation

1.  Navigate to this directory:
    ```bash
    cd web/backend
    ```

2.  Create a virtual environment (recommended):
    ```bash
    python -m venv venv
    ```

3.  Activate the virtual environment:
    *   **Windows:**
        ```bash
        venv\Scripts\activate
        ```
    *   **macOS/Linux:**
        ```bash
        source venv/bin/activate
        ```

4.  Install dependencies:
    ```bash
    pip install -r requirements.txt
    ```

## 🚀 Running the Server

Start the Flask application:

```bash
python app.py
```

The server will start on `http://localhost:5000`.

## 📂 Structure

*   `app.py`: The main Flask application entry point. Defines API endpoints.
*   `utils/`: Contains utility modules for data management, geometry, and plotting.
    *   `data_manager.py`: Handles loading, saving, and modifying the graph data structure.
    *   `curve_utils.py`: Implements B-Spline smoothing logic.
    *   `plot_utils.py`: Helper functions for plotting (legacy/backend-side).
*   `files/`: Directory where output files (`WorkingNodes.npy`, `output.pickle`) are saved.
*   `originalData/`: Directory for input `.npy` files.

## 🧪 Testing

Run the test suite (if available) using pytest:

```bash
pytest
```
