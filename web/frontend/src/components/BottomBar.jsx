import React from 'react';
import { useStore } from '../store';
import './Toolbar.css';
import { IconHome, IconZoom, IconPan } from './Icons';

/**
 * Renders the bottom bar with point size and plot width controls, and navigation buttons.
 */
const BottomBar = ({ onHome, onZoom, onPan }) => {
    const pointSize = useStore(state => state.pointSize);
    const plotWidth = useStore(state => state.plotWidth);
    const setPointSize = useStore(state => state.setPointSize);
    const setPlotWidth = useStore(state => state.setPlotWidth);

    return (
        <div className="bottom-bar-container" style={{
            display: 'flex',
            justifyContent: 'space-between',
            alignItems: 'center',
            padding: '10px 20px',
            background: 'var(--bg-secondary)',
            borderTop: '1px solid var(--border-color)'
        }}>
            {/* View Settings */}
            <div style={{ display: 'flex', gap: '20px', alignItems: 'center' }}>
                <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
                    <label style={{ fontSize: '0.9rem', color: 'var(--text-secondary)' }}>Point Size: {pointSize}</label>
                    <input
                        type="range"
                        min="1"
                        max="20"
                        step="1"
                        value={pointSize}
                        onChange={(e) => setPointSize(parseInt(e.target.value))}
                        style={{ width: '100px' }}
                    />
                </div>
                <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
                    <label style={{ fontSize: '0.9rem', color: 'var(--text-secondary)' }}>Plot Width: {plotWidth}%</label>
                    <input
                        type="range"
                        min="95"
                        max="200"
                        step="1"
                        value={plotWidth}
                        onChange={(e) => setPlotWidth(parseInt(e.target.value))}
                        style={{ width: '100px' }}
                    />
                </div>
            </div>

            {/* Navigation Controls */}
            <div style={{ display: 'flex', gap: '10px' }}>
                <button className="toolbar-button" onClick={onHome} title="Reset Zoom" style={{ width: 'auto', padding: '8px 12px' }}>
                    <IconHome size={18} /> Home
                </button>
                <button className="toolbar-button" onClick={onPan} title="Pan Mode" style={{ width: 'auto', padding: '8px 12px' }}>
                    <IconPan size={18} /> Pan
                </button>
                <button className="toolbar-button" onClick={onZoom} title="Zoom Mode" style={{ width: 'auto', padding: '8px 12px' }}>
                    <IconZoom size={18} /> Zoom
                </button>
            </div>
        </div>
    );
};

export default BottomBar;
