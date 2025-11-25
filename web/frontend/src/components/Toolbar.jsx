import React from 'react';
import { useStore } from '../store';
import './Toolbar.css';

const Toolbar = () => {
  const {
    mode,
    setMode,
    performOperation,
    saveData,
    selectedNodeIds,
    operationStartNodeId,
    smoothingPreview,
    applySmooth,
    smoothness,
    weight,
    setSmoothness,
    setWeight
  } = useStore(state => ({
    mode: state.mode,
    setMode: state.setMode,
    performOperation: state.performOperation,
    saveData: state.saveData,
    selectedNodeIds: state.selectedNodeIds,
    operationStartNodeId: state.operationStartNodeId,
    smoothingPreview: state.smoothingPreview,
    applySmooth: state.applySmooth,
    smoothness: state.smoothness,
    weight: state.weight,
    setSmoothness: state.setSmoothness,
    setWeight: state.setWeight
  }));

  const handleUndo = () => performOperation('undo');
  const handleRedo = () => performOperation('redo');

  const getButtonClass = (buttonMode) => {
    return mode === buttonMode ? 'toolbar-button active' : 'toolbar-button';
  };

  return (
    <div className="toolbar-container">
      <h3>Controls</h3>

      <div className="toolbar-section">
        <p><strong>Mode:</strong> {mode}</p>
        <p><strong>Selected:</strong> {selectedNodeIds.length} nodes</p>
        {operationStartNodeId && <p><strong>Start Node:</strong> {operationStartNodeId}</p>}
      </div>

      <div className="toolbar-section">
        <h4>Edit Mode</h4>
        <button className={getButtonClass('select')} onClick={() => setMode('select')}>Select</button>
        <button className={getButtonClass('draw')} onClick={() => setMode('draw')}>Draw</button>
      </div>

      <div className="toolbar-section">
        <h4>Path Operations</h4>
        <p className="instructions">Select a start and end node for path operations.</p>
        <button className={getButtonClass('connect')} onClick={() => setMode('connect')}>Connect</button>
        <button className={getButtonClass('smooth')} onClick={() => setMode('smooth')}>Smooth</button>

        {mode === 'smooth' && (
          <div className="slider-container">
            <label>Smoothness: {smoothness.toFixed(1)}</label>
            <input
              type="range"
              min="0.1"
              max="30"
              step="0.1"
              value={smoothness}
              onChange={(e) => setSmoothness(parseFloat(e.target.value))}
            />
            <label>Weight: {weight.toFixed(0)}</label>
            <input
              type="range"
              min="1"
              max="100"
              step="1"
              value={weight}
              onChange={(e) => setWeight(parseFloat(e.target.value))}
            />
          </div>
        )}

        {mode === 'smooth' && smoothingPreview && (
          <button className="toolbar-button confirm" onClick={applySmooth}>Apply Smooth</button>
        )}

        <button className={getButtonClass('remove_between')} onClick={() => setMode('remove_between')}>Remove Between</button>
        <button className={getButtonClass('reverse_path')} onClick={() => setMode('reverse_path')}>Reverse Path</button>
      </div>

      <div className="toolbar-section">
        <h4>History</h4>
        <button className="toolbar-button" onClick={handleUndo}>Undo</button>
        <button className="toolbar-button" onClick={handleRedo}>Redo</button>
      </div>

      <div className="toolbar-section">
        <h4>Data</h4>
        <button className="toolbar-button" onClick={saveData}>Save to Server</button>
      </div>
    </div>
  );
};

export default Toolbar;