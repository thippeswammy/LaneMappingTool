import React from 'react';
import { useStore } from '../store';
import './Toolbar.css'; // Reusing Toolbar styles

const BottomBar = ({ onHome, onZoom, onPan }) => {
    const smoothness = useStore(state => state.smoothness);
    const weight = useStore(state => state.weight);
    const pointSize = useStore(state => state.pointSize);
    const plotWidth = useStore(state => state.plotWidth);
    const setSmoothness = useStore(state => state.setSmoothness);
    const setWeight = useStore(state => state.setWeight);
    const setPointSize = useStore(state => state.setPointSize);
    const setPlotWidth = useStore(state => state.setPlotWidth);

    return (
        <div className="bottom-bar-container" style={{ display: 'flex', flexDirection: 'column', padding: '10px', background: '#f0f0f0', borderTop: '1px solid #ccc' }}>
            {/* Sliders Row */}
            <div style={{ display: 'flex', gap: '20px', alignItems: 'center', marginBottom: '10px' }}>
                <div style={{ display: 'flex', alignItems: 'center', gap: '5px' }}>
                    <label>Smoothness: {smoothness.toFixed(1)}</label>
                    <input
                        type="range"
                        min="0.1"
                        max="30"
                        step="0.1"
                        value={smoothness}
                        onChange={(e) => setSmoothness(parseFloat(e.target.value))}
                    />
                </div>
                <div style={{ display: 'flex', alignItems: 'center', gap: '5px' }}>
                    <label>Smoothing Weight: {weight.toFixed(0)}</label>
                    <input
                        type="range"
                        min="1"
                        max="100"
                        step="1"
                        value={weight}
                        onChange={(e) => setWeight(parseFloat(e.target.value))}
                    />
                </div>
                <div style={{ display: 'flex', alignItems: 'center', gap: '5px' }}>
                    <label>Point Size: {pointSize}</label>
                    <input
                        type="range"
                        min="1"
                        max="20"
                        step="1"
                        value={pointSize}
                        onChange={(e) => setPointSize(parseInt(e.target.value))}
                    />
                </div>
                <div style={{ display: 'flex', alignItems: 'center', gap: '5px' }}>
                    <label>Plot Width: {plotWidth}%</label>
                    <input
                        type="range"
                        min="95"
                        max="105"
                        step="1"
                        value={plotWidth}
                        onChange={(e) => setPlotWidth(parseInt(e.target.value))}
                    />
                </div>
            </div>

            {/* Navigation Controls Row */}
            <div style={{ display: 'flex', gap: '10px' }}>
                <button className="toolbar-button" onClick={onHome} title="Reset Zoom">Home</button>
                <button className="toolbar-button" disabled title="Back">Back</button>
                <button className="toolbar-button" disabled title="Forward">Forward</button>
                <button className="toolbar-button" onClick={onPan} title="Pan Mode">Pan</button>
                <button className="toolbar-button" onClick={onZoom} title="Zoom Mode">Zoom</button>
                <button className="toolbar-button" disabled title="Subplots">Subplots</button>
                <button className="toolbar-button" disabled title="Save Figure">Save</button>
            </div>
        </div>
    );
};

export default BottomBar;
