import { useState, useEffect, useCallback } from 'react'
import axios from 'axios'
import PlotComponent from './components/Plot'
import Toolbar from './components/Toolbar'
import './App.css'

function App() {
  const [data, setData] = useState({ nodes: [], edges: [], file_names: [], D: 1.0 })
  const [loading, setLoading] = useState(true)
  const [status, setStatus] = useState("Initializing...")
  const [selectedPoints, setSelectedPoints] = useState([])

  // View Settings
  const [pointSize, setPointSize] = useState(10)
  const [smoothness, setSmoothness] = useState(1.0)

  const fetchState = async () => {
    try {
      const response = await axios.get('/api/state')
      setData(response.data)
      setLoading(false)
      setStatus("Ready")
    } catch (error) {
      console.error("Error fetching state:", error)
      setStatus("Error fetching state")
    }
  }

  useEffect(() => {
    const init = async () => {
      try {
        await axios.get('/api/init')
        fetchState()
      } catch (error) {
        console.error("Error initializing:", error)
        setStatus("Error initializing")
      }
    }
    init()
  }, [])

  const handleAddNode = async (x, y, laneId) => {
    try {
      await axios.post('/api/action/add_node', { x, y, lane_id: laneId })
      fetchState()
      setStatus("Node added")
    } catch (error) {
      console.error("Error adding node:", error)
    }
  }

  const handleAddEdge = async () => {
    if (selectedPoints.length !== 2) return
    try {
      await axios.post('/api/action/add_edge', { from_id: selectedPoints[0], to_id: selectedPoints[1] })
      fetchState()
      setStatus("Edge added")
    } catch (error) {
      console.error("Error adding edge:", error)
    }
  }

  const handleDelete = async () => {
    if (selectedPoints.length === 0) return
    try {
      await axios.post('/api/action/delete', { point_ids: selectedPoints })
      setSelectedPoints([])
      fetchState()
      setStatus("Deleted selected points")
    } catch (error) {
      console.error("Error deleting:", error)
    }
  }

  const handleUndo = async () => {
    try {
      await axios.post('/api/action/undo')
      fetchState()
      setStatus("Undo performed")
    } catch (error) {
      console.error("Error undoing:", error)
    }
  }

  const handleRedo = async () => {
    try {
      await axios.post('/api/action/redo')
      fetchState()
      setStatus("Redo performed")
    } catch (error) {
      console.error("Error redoing:", error)
    }
  }

  const handleSave = async () => {
    try {
      setStatus("Saving...")
      const res = await axios.post('/api/save')
      setStatus(`Saved to ${res.data.path}`)
      setTimeout(() => setStatus("Ready"), 3000)
    } catch (error) {
      console.error("Error saving:", error)
      setStatus("Error saving")
    }
  }

  // Keyboard Shortcuts
  useEffect(() => {
    const handleKeyDown = (e) => {
      // Ignore if input is focused (though we don't have many inputs)
      if (e.target.tagName === 'INPUT') return;

      if (e.key === 'Delete' || e.key === 'Backspace') {
        handleDelete();
      } else if ((e.ctrlKey || e.metaKey) && e.key === 'z') {
        if (e.shiftKey) {
          handleRedo();
        } else {
          handleUndo();
        }
        e.preventDefault();
      } else if ((e.ctrlKey || e.metaKey) && e.key === 'y') {
        handleRedo();
        e.preventDefault();
      }
    };

    window.addEventListener('keydown', handleKeyDown);
    return () => window.removeEventListener('keydown', handleKeyDown);
  }, [selectedPoints]); // Re-bind when selectedPoints changes to ensure handleDelete has current state? 
  // Actually, handleDelete uses selectedPoints from closure. 
  // Better to use useCallback or ref for selectedPoints if we don't want to re-bind often, 
  // but re-binding on selection change is acceptable here.

  return (
    <div className="app-container">
      <div className="header">
        <h2>Lane Visualization Tool</h2>
        <div className="status-badge">{status}</div>
      </div>

      <div className="main-content">
        <div className="plot-area">
          {!loading && (
            <PlotComponent
              data={data}
              selectedPoints={selectedPoints}
              setSelectedPoints={setSelectedPoints}
              onAddNode={handleAddNode}
              pointSize={pointSize}
            />
          )}
        </div>
        <div className="sidebar">
          <Toolbar
            onDelete={handleDelete}
            onUndo={handleUndo}
            onRedo={handleRedo}
            onSave={handleSave}
            onAddEdge={handleAddEdge}
            selectionCount={selectedPoints.length}
            pointSize={pointSize}
            setPointSize={setPointSize}
            smoothness={smoothness}
            setSmoothness={setSmoothness}
          />
        </div>
      </div>
    </div>
  )
}

export default App
