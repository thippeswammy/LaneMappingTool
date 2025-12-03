# Lane Mapping Tool - Frontend

This directory contains the React-based frontend for the Lane Mapping Tool. It provides an interactive interface for visualizing and editing lane graphs.

## 🔧 Setup

### Prerequisites

*   Node.js 16 or higher
*   npm (Node Package Manager)

### Installation

1.  Navigate to this directory:
    ```bash
    cd web/frontend
    ```

2.  Install dependencies:
    ```bash
    npm install
    ```

## 🚀 Development

Start the development server:

```bash
npm run dev
```

The application will be accessible at `http://localhost:5173` (or the port shown in the terminal). Ensure the backend server is running on port 5000 for full functionality.

## 📜 Scripts

*   `npm run dev`: Starts the development server.
*   `npm run build`: Builds the application for production.
*   `npm run lint`: Runs ESLint to check for code quality issues.
*   `npm run preview`: Previews the production build locally.

## 🧩 Key Components

*   `src/App.jsx`: Main application layout and state management.
*   `src/components/Plot.jsx`: Handles the D3/SVG visualization of the lane graph.
*   `src/components/Sidebar.jsx`: Controls for editing modes and settings.
*   `src/components/BottomBar.jsx`: Additional controls and status information.
*   `src/store.js`: Centralized state management (if applicable) or API interaction logic.
