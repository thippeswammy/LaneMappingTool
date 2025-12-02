import { useEffect, useLayoutEffect, useRef, useState } from 'react';
import { useStore } from './store';
import Plot from './components/Plot';
import Sidebar from './components/Sidebar';
import BottomBar from './components/BottomBar';
import { IconMenu } from './components/Icons';
import './App.css';

/**
 * Renders the main application component with a sidebar, header, plot area, and bottom bar.
 *
 * The component manages its state using Zustand for loading status, nodes, edges, and fetches data on mount.
 * It also sets up keyboard shortcuts for various operations and handles resizing of the plot area using ResizeObserver.
 * The sidebar can be toggled open or closed, and the plot area displays loading status or the plot based on dimensions.
 *
 * @returns {JSX.Element} The rendered application component.
 */
function App() {
  console.log("App component rendering");
  // Get state and actions from the Zustand store
  const loading = useStore(state => state.loading);
  const status = useStore(state => state.status);
  const fetchData = useStore(state => state.fetchData);
  const nodes = useStore(state => state.nodes);
  const edges = useStore(state => state.edges);

  const [isSidebarOpen, setIsSidebarOpen] = useState(true);
  const [plotDimensions, setPlotDimensions] = useState({ width: 0, height: 0 });

  const plotRef = useRef(null);
  const plotContainerRef = useRef(null);

  useLayoutEffect(() => {
    if (!plotContainerRef.current) return;

    const resizeObserver = new ResizeObserver((entries) => {
      for (let entry of entries) {
        const { width, height } = entry.contentRect;
        setPlotDimensions({ width, height });
      }
    });

    resizeObserver.observe(plotContainerRef.current);

    return () => {
      resizeObserver.disconnect();
    };
  }, []);

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

  return (
    <div className="app-container" style={{ display: 'flex', height: '100vh', flexDirection: 'row', overflow: 'hidden', background: 'var(--bg-primary)' }}>
      {/* Left Sidebar */}
      {isSidebarOpen && (
        <aside className="sidebar" style={{ width: '240px', flexShrink: 0 }}>
          <Sidebar />
        </aside>
      )}

      {/* Main Content Area */}
      <div className="main-content" style={{ flex: 1, display: 'flex', flexDirection: 'column', height: '100%' }}>

        {/* Header / Status Bar */}
        <header className="header" style={{ padding: '10px 20px', borderBottom: '1px solid var(--border-color)', background: 'var(--bg-secondary)', display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '15px' }}>
            <button
              onClick={() => setIsSidebarOpen(!isSidebarOpen)}
              style={{ background: 'transparent', border: 'none', color: 'var(--text-primary)', padding: '5px', cursor: 'pointer', display: 'flex', alignItems: 'center' }}
              title={isSidebarOpen ? "Collapse Sidebar" : "Expand Sidebar"}
            >
              <IconMenu size={24} />
            </button>
            <h2 style={{ margin: 0, fontSize: '1.2rem', fontWeight: 600 }}>Lane Mapping Tool</h2>
          </div>
          <div className="status-bar" style={{ fontSize: '0.9rem', color: 'var(--text-secondary)' }}>
            Status: <span className="status-message" style={{ color: 'var(--accent-color)' }}>{status}</span>
          </div>
        </header>

        {/* Plot Area */}
        <main className="plot-area" ref={plotContainerRef} style={{ flex: 1, position: 'relative', overflow: 'hidden', background: '#121212' }}>
          {loading ? (
            <div className="loading-overlay" style={{ color: 'var(--text-primary)' }}>Loading...</div>
          ) : (
            plotDimensions.width > 0 && plotDimensions.height > 0 && (
              <Plot ref={plotRef} nodes={nodes} edges={edges} width={plotDimensions.width} height={plotDimensions.height} />
            )
          )}
        </main>

        {/* Bottom Bar */}
        <footer className="bottom-bar" style={{ flexShrink: 0 }}>
          <BottomBar onHome={handleHome} />
        </footer>
      </div>
    </div>
  );
}

export default App;