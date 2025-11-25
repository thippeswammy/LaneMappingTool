import { useEffect } from 'react';
import { useStore } from './store';
import Plot from './components/Plot';
import Toolbar from './components/Toolbar';
import './App.css';

function App() {
  // Get state and actions from the Zustand store
  const {
    loading,
    status,
    fetchData,
    nodes,
    edges,
  } = useStore(state => ({
    loading: state.loading,
    status: state.status,
    fetchData: state.fetchData,
    nodes: state.nodes,
    edges: state.edges
  }));

  // Fetch initial data on component mount
  useEffect(() => {
    fetchData();
  }, [fetchData]);

  // Keyboard Shortcuts
  useEffect(() => {
    const handleKeyDown = (e) => {
      if (e.target.tagName === 'INPUT' || e.target.tagName === 'TEXTAREA') return;

      const { performOperation, setMode } = useStore.getState();

      if (e.key === 'Escape') {
        setMode('select');
        e.preventDefault();
      } else if (e.key === 'd') {
        setMode('draw');
        e.preventDefault();
      } else if (e.key === 'Delete' || e.key === 'Backspace') {
        const { selectedNodeIds } = useStore.getState();
        if (selectedNodeIds.length > 0) {
          performOperation('delete_points', { point_ids: selectedNodeIds });
        }
        e.preventDefault();
      } else if ((e.ctrlKey || e.metaKey) && e.key === 'z') {
        performOperation('undo');
        e.preventDefault();
      } else if ((e.ctrlKey || e.metaKey) && e.key === 'y') {
        performOperation('redo');
        e.preventDefault();
      }
    };

    window.addEventListener('keydown', handleKeyDown);
    return () => window.removeEventListener('keydown', handleKeyDown);
  }, []); // Empty dependency array ensures this runs only once


  return (
    <div className="app-container">
      <header className="header">
        <h1>Data Visualization Editing Tool</h1>
        <div className="status-bar">
          Status: <span className="status-message">{status}</span>
        </div>
      </header>
      {loading ? (
        <div className="loading-overlay">Loading...</div>
      ) : (
        <div className="main-content">
          <aside className="sidebar">
            <Toolbar />
          </aside>
          <main className="plot-area">
            <Plot nodes={nodes} edges={edges} />
          </main>
        </div>
      )}
    </div>
  );
}

export default App;