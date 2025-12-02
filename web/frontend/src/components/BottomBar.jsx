import React from 'react';
import { useStore } from '../store';
import './Toolbar.css';
import { IconHome, IconZoom, IconPan } from './Icons';

/**
 * Renders the bottom bar with point size controls and navigation buttons.
 */
const BottomBar = ({ onHome }) => {
    const pointSize = useStore(state => state.pointSize);
    const setPointSize = useStore(state => state.setPointSize);
    const mode = useStore(state => state.mode);
    const setMode = useStore(state => state.setMode);

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
                    <label
                        style={{
                            fontSize: '0.9rem',
                            color: 'var(--text-secondary)'
                        }}
                    >
                        Point Size: {pointSize}
                    </label>
                    <input
                        type="range"
                        min="0.1"
                        max="5"
                        step="0.1"
                        value={pointSize}
                        onChange={(e) => setPointSize(parseFloat(e.target.value))}
                        style={{ width: '100px' }}
                    />
                </div>
            </div>
            {/* Navigation Controls */}
            <div style={{ display: 'flex', gap: '10px' }}>
                <button className="toolbar-button" onClick={onHome} title="Reset Zoom" style={{ width: 'auto', padding: '8px 12px' }}>
                    <IconHome size={18} /> Home
                </button>
                <button
                    className={`toolbar-button ${mode === 'zoom' ? 'active' : ''}`}
                    onClick={() => setMode(mode === 'zoom' ? 'select' : 'zoom')}
                    title="Zoom Disabled"
                    style={{ width: 'auto', padding: '8px 12px' }}
                    disabled={true}
                >
                    <IconZoom size={18} /> Zoom
                </button>
            </div>
        </div>
    );
};

export default BottomBar;
