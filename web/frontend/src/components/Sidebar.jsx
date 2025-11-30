import React from 'react';
import { useStore } from '../store';
import './Toolbar.css'; // Reusing Toolbar styles for now

const Sidebar = () => {
    const mode = useStore(state => state.mode);
    const setMode = useStore(state => state.setMode);
    const performOperation = useStore(state => state.performOperation);
    const saveData = useStore(state => state.saveData);
    const smoothingPreview = useStore(state => state.smoothingPreview);
    const applySmooth = useStore(state => state.applySmooth);

    const getButtonClass = (buttonMode) => {
        return mode === buttonMode ? 'toolbar-button active' : 'toolbar-button';
    };

    return (
        <div className="sidebar-container" style={{ display: 'flex', flexDirection: 'column', gap: '10px', padding: '10px', background: '#f0f0f0', borderRight: '1px solid #ccc', height: '100%' }}>
            <button className={getButtonClass('draw')} onClick={() => setMode('draw')}>Draw</button>
            <button className="toolbar-button" disabled>Line</button> {/* Placeholder for Line if needed */}
            <button className={getButtonClass('smooth')} onClick={() => setMode('smooth')}>Smooth</button>

            {mode === 'smooth' && smoothingPreview && (
                <button className="toolbar-button confirm" onClick={applySmooth}>Apply Smooth</button>
            )}

            <div style={{ height: '20px' }}></div> {/* Spacer */}

            <button className="toolbar-button" onClick={() => setMode('select')}>Cancel Operation</button>
            <button className="toolbar-button" onClick={() => useStore.getState().setSelectedNodeIds([])}>Clear Selection</button>
            <button className="toolbar-button" onClick={saveData}>Save</button>
            <button className={getButtonClass('connect')} onClick={() => setMode('connect')}>Connect Nodes</button>
            <button className="toolbar-button" disabled>Export Selected</button>
            <button className="toolbar-button" disabled>Toggle Grid</button>
            <button className={getButtonClass('remove_between')} onClick={() => setMode('remove_between')}>Remove Between</button>
            <button className={getButtonClass('reverse_path')} onClick={() => setMode('reverse_path')}>Reverse Path</button>
        </div>
    );
};

export default Sidebar;
