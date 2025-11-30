import { useEffect, useRef } from 'react';
import { useStore } from './store';
import Plot from './components/Plot';
import Sidebar from './components/Sidebar';
import BottomBar from './components/BottomBar';
import './App.css';

function App() {
  console.log("App component rendering");
  // Get state and actions from the Zustand store
  const loading = useStore(state => state.loading);
  const status = useStore(state => state.status);
  const fetchData = useStore(state => state.fetchData);
  const nodes = useStore(state => state.nodes);
  const edges = useStore(state => state.edges);

  const plotRef = useRef(null);

  // Fetch initial data on component mount
  useEffect(() => {
    console.log("App useEffect: fetching data");
    fetchData();
  }, [fetchData]);

  // Keyboard Shortcuts
  useEffect(() => {
    const handleKeyDown = (e) => {
      if (e.target.tagName === 'INPUT' || e.target.tagName === 'TEXTAREA') return;

      const { performOperation, setMode, finalizeDraw, cancelDraw, mode } = useStore.getState();

      if (e.key === 'Escape') {
        if (mode === 'draw') {
          cancelDraw();
        }
        setMode('select');
        e.preventDefault();
      } else if (e.key === 'Enter') {
        if (mode === 'draw') {
          finalizeDraw();
        }
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
  }, []);

  const handleHome = () => {
    if (plotRef.current) {
      plotRef.current.resetZoom();
    }
  };

  const handleZoom = () => {
    if (plotRef.current) {
      plotRef.current.toggleZoom();
    }
  };

  const handlePan = () => {
    if (plotRef.current) {
      plotRef.current.togglePan();
    }
  };

  return (
    <div className="app-container" style={{ display: 'flex', height: '100vh', flexDirection: 'row', overflow: 'hidden' }}>
      {/* Left Sidebar */}
      <aside className="sidebar" style={{ width: '200px', flexShrink: 0 }}>
        <Sidebar />
      </aside>

      {/* Main Content Area */}
      <div className="main-content" style={{ flex: 1, display: 'flex', flexDirection: 'column', height: '100%' }}>

        {/* Header / Status Bar (Optional, maybe move to top or integrate) */}
        <header className="header" style={{ padding: '5px 10px', borderBottom: '1px solid #ddd', background: '#fff' }}>
          <h2 style={{ margin: 0, fontSize: '16px' }}>Lane Data Visualization</h2>
          <div className="status-bar" style={{ fontSize: '12px', color: '#666' }}>
            Status: <span className="status-message">{status}</span>
          </div>
        </header>

        {/* Plot Area */}
        <main className="plot-area" style={{ flex: 1, position: 'relative', overflow: 'hidden' }}>
          {loading ? (
            <div className="loading-overlay">Loading...</div>
          ) : (
            <Plot ref={plotRef} nodes={nodes} edges={edges} />
          )}
        </main>

        {/* Bottom Bar */}
        <footer className="bottom-bar" style={{ flexShrink: 0 }}>
          <BottomBar onHome={handleHome} onZoom={handleZoom} onPan={handlePan} />
        </footer>
      </div>
    </div>
  );
}

export default App;