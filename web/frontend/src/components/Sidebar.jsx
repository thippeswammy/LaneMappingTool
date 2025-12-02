import React from 'react';
import { useStore } from '../store';
import './Toolbar.css';
import {
    IconDraw, IconSmooth, IconConnect, IconRemove, IconReverse, IconSave, IconCheck, IconCancel
} from './Icons';

const Sidebar = () => {
    const mode = useStore(state => state.mode);
    const setMode = useStore(state => state.setMode);
    const performOperation = useStore(state => state.performOperation);
    const saveData = useStore(state => state.saveData);
    const smoothingPreview = useStore(state => state.smoothingPreview);
    const applySmooth = useStore(state => state.applySmooth);
    const cancelSmooth = useStore(state => state.cancelSmooth); // Assuming we might want a cancel specific to smooth, or just general cancel

    const smoothness = useStore(state => state.smoothness);
    const weight = useStore(state => state.weight);
    const setSmoothness = useStore(state => state.setSmoothness);
    const setWeight = useStore(state => state.setWeight);
    const selectedNodeIds = useStore(state => state.selectedNodeIds);
    const setSelectedNodeIds = useStore(state => state.setSelectedNodeIds);

    const getButtonClass = (buttonMode) => {
        return mode === buttonMode ? 'toolbar-button active' : 'toolbar-button';
    };

    return (
        <div className="sidebar-container" style={{
            display: 'flex',
            flexDirection: 'column',
            gap: '15px',
            padding: '15px',
            background: 'var(--bg-secondary)',
            borderRight: '1px solid var(--border-color)',
            height: '100%',
            overflowY: 'auto'
        }}>
            <div className="sidebar-section">
                <h4 style={{ margin: '0 0 10px 0', fontSize: '0.9rem', textTransform: 'uppercase', color: 'var(--text-secondary)' }}>Tools</h4>
                <button className={getButtonClass('draw')} onClick={() => setMode('draw')}>
                    <IconDraw /> Draw Path
                </button>
                <button className="toolbar-button" onClick={() => setMode('select')} disabled={mode === 'select' && selectedNodeIds.length === 0}>
                    <IconCancel /> Cancel / Select
                </button>
                <button className="toolbar-button" onClick={() => setSelectedNodeIds([])} disabled={selectedNodeIds.length === 0}>
                    <IconCancel /> Clear Selection ({selectedNodeIds.length})
                </button>
            </div>

            <div className="sidebar-section">
                <h4 style={{ margin: '0 0 10px 0', fontSize: '0.9rem', textTransform: 'uppercase', color: 'var(--text-secondary)' }}>Operations</h4>

                <button className={getButtonClass('connect')} onClick={() => setMode('connect')}>
                    <IconConnect /> Connect Nodes
                </button>
                <button className={getButtonClass('remove_between')} onClick={() => setMode('remove_between')}>
                    <IconRemove /> Remove Between
                </button>

                <button className={getButtonClass('smooth')} onClick={() => setMode('smooth')}>
                    <IconSmooth /> Smooth Path
                </button>

                {mode === 'smooth' && (
                    <div style={{
                        display: 'flex',
                        flexDirection: 'column',
                        gap: '10px',
                        padding: '10px',
                        background: 'var(--bg-tertiary)',
                        borderRadius: '4px',
                        marginBottom: '10px',
                        border: '1px solid var(--border-color)'
                    }}>
                        <div style={{ display: 'flex', flexDirection: 'column', gap: '5px' }}>
                            <label style={{ fontSize: '0.8rem' }}>Smoothness: {smoothness}</label>
                            <input
                                type="range"
                                min="0.01" max="10" step="0.1"
                                value={smoothness}
                                onChange={(e) => setSmoothness(parseFloat(e.target.value))}
                                style={{ width: '100%' }}
                            />
                        </div>
                        <div style={{ display: 'flex', flexDirection: 'column', gap: '5px' }}>
                            <label style={{ fontSize: '0.8rem' }}>Weight: {weight}</label>
                            <input
                                type="range"
                                min="0.1" max="10" step="0.1"
                                value={weight}
                                onChange={(e) => setWeight(parseFloat(e.target.value))}
                                style={{ width: '100%' }}
                            />
                        </div>
                        {smoothingPreview && (
                            <button className="toolbar-button confirm" onClick={applySmooth} style={{ justifyContent: 'center', marginTop: '5px' }}>
                                <IconCheck size={16} /> Apply
                            </button>
                        )}
                    </div>
                )}

                <button className={getButtonClass('reverse_path')} onClick={() => setMode('reverse_path')}>
                    <IconReverse /> Reverse Path
                </button>
            </div>

            <div style={{ flex: 1 }}></div>

            <div className="sidebar-section">
                <button className="toolbar-button" onClick={saveData} style={{ marginTop: 'auto' }}>
                    <IconSave /> Save Data
                </button>
            </div>
        </div>
    );
};

export default Sidebar;
