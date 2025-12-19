import React, { useState, useEffect } from 'react';
import { useStore } from '../store';
import './Toolbar.css';
import {
    IconDraw, IconSmooth, IconConnect, IconRemove, IconReverse, IconSave, IconCheck, IconCancel
} from './Icons';

/**
 * Renders the sidebar component for tool and operation selection.
 *
 * The Sidebar component utilizes various state values and functions from the store, including mode management,
 * selection handling, and data saving. It provides buttons for drawing, selecting, connecting, and smoothing paths,
 * along with adjustable parameters for smoothness and weight when in smooth mode. The layout is responsive and
 * styled for usability, ensuring that user interactions are intuitive and efficient.
 */
const Sidebar = () => {
    // Store State
    const mode = useStore(state => state.mode);
    const setMode = useStore(state => state.setMode);

    // Sidebar Mode (New)
    const sidebarMode = useStore(state => state.sidebarMode);
    const setSidebarMode = useStore(state => state.setSidebarMode);

    const performOperation = useStore(state => state.performOperation);
    const saveData = useStore(state => state.saveData);
    const smoothingPreview = useStore(state => state.smoothingPreview);
    const applySmooth = useStore(state => state.applySmooth);
    const cancelSmooth = useStore(state => state.cancelSmooth);
    const verifyYaw = useStore(state => state.verifyYaw);
    const clearVerification = useStore(state => state.clearVerification);
    const yawVerificationResults = useStore(state => state.yawVerificationResults);

    const smoothness = useStore(state => state.smoothness);
    const weight = useStore(state => state.weight);
    const setSmoothness = useStore(state => state.setSmoothness);
    const setWeight = useStore(state => state.setWeight);
    const selectedNodeIds = useStore(state => state.selectedNodeIds);
    const setSelectedNodeIds = useStore(state => state.setSelectedNodeIds);
    const showYaw = useStore(state => state.showYaw);
    const toggleShowYaw = useStore(state => state.toggleShowYaw);

    const nodes = useStore(state => state.nodes);
    const updateNodeProperties = useStore(state => state.updateNodeProperties);

    // Local State for Control Mode
    const [zoneVal, setZoneVal] = useState('');
    const [indicatorVal, setIndicatorVal] = useState('1');

    // Sync Control Mode inputs with selection
    useEffect(() => {
        if (selectedNodeIds.length > 0) {
            // Filter nodes that are currently selected
            const selectedNodes = nodes.filter(n => selectedNodeIds.includes(n[0]));

            if (selectedNodes.length === 0) return;

            // Check Zone Uniformity (index 4)
            const firstZone = selectedNodes[0][4];
            const allZonesSame = selectedNodes.every(n => n[4] === firstZone);
            setZoneVal(allZonesSame ? firstZone : '-');

            // Check Indicator Uniformity (index 6)
            const getInd = (n) => (n.length > 6 && n[6] !== undefined && n[6] !== 0) ? n[6] : 1;

            const firstInd = getInd(selectedNodes[0]);
            const allIndsSame = selectedNodes.every(n => getInd(n) === firstInd);
            setIndicatorVal(allIndsSame ? firstInd.toString() : '-');
        } else {
            setZoneVal('');
            setIndicatorVal('1');
        }
    }, [selectedNodeIds, nodes]);

    const handleApplyControls = () => {
        if (selectedNodeIds.length === 0) return;

        // If mixed ('-'), don't update unless changed.
        // If empty (''), default to 0.
        let newZone = null;
        if (zoneVal === '-') {
            newZone = null; // No change
        } else if (zoneVal === '') {
            newZone = 0; // Default to 0
        } else {
            newZone = parseInt(zoneVal);
            if (isNaN(newZone)) newZone = 0; // Safe default
        }

        updateNodeProperties(selectedNodeIds, {
            zone: newZone,
            indicator: parseInt(indicatorVal)
        });

        // Clear selection after applying
        setSelectedNodeIds([]);
    };

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
            {/* Mode Switcher */}
            <div style={{ display: 'flex', gap: '10px' }}>
                <button
                    className={`toolbar-button ${sidebarMode === 'edit' ? 'active' : ''}`}
                    onClick={() => setSidebarMode('edit')}
                    style={{ flex: 1, justifyContent: 'center' }}
                >
                    Edit
                </button>
                <button
                    className={`toolbar-button ${sidebarMode === 'control' ? 'active' : ''}`}
                    onClick={() => setSidebarMode('control')}
                    style={{ flex: 1, justifyContent: 'center' }}
                >
                    Config
                </button>
            </div>

            <hr style={{ border: '0', borderTop: '1px solid var(--border-color)', width: '100%', margin: '0' }} />

            {sidebarMode === 'edit' && (
                <>
                    <div className="sidebar-section">
                        <h4 style={{ margin: '0 0 10px 0', fontSize: '0.9rem', textTransform: 'uppercase', color: 'var(--text-secondary)' }}>Tools</h4>
                        <button className={getButtonClass('draw')} onClick={() => setMode('draw')}>
                            <IconDraw /> Draw Path
                        </button>
                        <button className={getButtonClass('box_select')} onClick={() => setMode('box_select')}>
                            <IconDraw /> Select Points
                        </button>
                        <button className={getButtonClass('select_path')} onClick={() => setMode('select_path')}>
                            <IconDraw /> Select Path
                        </button>
                        <button className="toolbar-button" onClick={() => setMode('select')} disabled={mode === 'select' && selectedNodeIds.length === 0}>
                            <IconCancel /> Cancel Operation
                        </button>
                        <button className="toolbar-button" onClick={() => setSelectedNodeIds([])} disabled={selectedNodeIds.length === 0}>
                            <IconCancel /> Clear Selection ({selectedNodeIds.length})
                        </button>
                    </div>

                    {selectedNodeIds.length > 0 && (
                        <div className="sidebar-section">
                            <h4 style={{ margin: '0 0 10px 0', fontSize: '0.9rem', textTransform: 'uppercase', color: 'var(--text-secondary)' }}>Batch Operations</h4>
                            <button className="toolbar-button" onClick={() => performOperation('delete_points', { point_ids: selectedNodeIds })}>
                                <IconRemove /> Delete Selected ({selectedNodeIds.length})
                            </button>
                            <button className="toolbar-button" onClick={() => performOperation('copy_points', { point_ids: selectedNodeIds })}>
                                <IconSave /> Copy Selected ({selectedNodeIds.length})
                            </button>
                        </div>
                    )}

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
                                border: '1px solid var(--border-color)',
                                color: 'var(--text-primary)'
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

                        <label className="toolbar-button" style={{ justifyContent: 'flex-start', cursor: 'pointer' }}>
                            <input
                                type="checkbox"
                                checked={showYaw}
                                onChange={toggleShowYaw}
                                style={{ marginRight: '10px' }}
                            />
                            Show Yaw
                        </label>
                    </div>
                </>
            )}

            {sidebarMode === 'control' && (
                <div className="sidebar-section">
                    <h4 style={{ margin: '0 0 10px 0', fontSize: '0.9rem', textTransform: 'uppercase', color: 'var(--text-secondary)' }}>
                        Node Inspector ({selectedNodeIds.length})
                    </h4>
                    {selectedNodeIds.length > 0 ? (
                        <div style={{
                            maxHeight: '300px',
                            overflowY: 'auto',
                            background: 'var(--bg-tertiary)',
                            borderRadius: '4px',
                            border: '1px solid var(--border-color)',
                            marginBottom: '15px'
                        }}>
                            {selectedNodeIds.slice(0, 100).map(id => {
                                const node = nodes.find(n => n[0] === id);
                                if (!node) return null;
                                return (
                                    <div key={id} style={{
                                        padding: '8px',
                                        borderBottom: '1px solid var(--border-color)',
                                        fontSize: '0.8rem',
                                        display: 'flex',
                                        flexDirection: 'column',
                                        gap: '2px'
                                    }}>
                                        <div style={{ fontWeight: 'bold', color: 'var(--accent-color)' }}>ID: {node[0]}</div>
                                        <div style={{ display: 'flex', justifyContent: 'space-between' }}>
                                            <span>x: {node[1].toFixed(1)}</span>
                                            <span>y: {node[2].toFixed(1)}</span>
                                        </div>
                                        <div style={{ display: 'flex', justifyContent: 'space-between', color: 'var(--text-secondary)' }}>
                                            <span>yaw: {node[3].toFixed(2)}</span>
                                            <span>w: {node.length > 5 ? node[5].toFixed(1) : '-'}</span>
                                        </div>
                                        <div style={{ display: 'flex', justifyContent: 'space-between', color: '#aaa' }}>
                                            <span>Zn: {node[4]}</span>
                                            <span>Ind: {node.length > 6 ? node[6] : '-'}</span>
                                        </div>
                                    </div>
                                );
                            })}
                            {selectedNodeIds.length > 100 && (
                                <div style={{ padding: '8px', textAlign: 'center', color: 'var(--text-secondary)', fontSize: '0.8rem' }}>
                                    ...and {selectedNodeIds.length - 100} more selected
                                </div>
                            )}
                        </div>
                    ) : (
                        <div style={{ color: 'var(--text-secondary)', fontSize: '0.85rem', fontStyle: 'italic', marginBottom: '15px' }}>
                            Select nodes (Brush/Path) to view details.
                        </div>
                    )}

                    {/* Selection Tools in Control Mode */}
                    <h4 style={{ margin: '0 0 10px 0', fontSize: '0.9rem', textTransform: 'uppercase', color: 'var(--text-secondary)' }}>Selection Tools</h4>
                    <div className="sidebar-section" style={{ display: 'flex', gap: '5px', flexWrap: 'wrap', padding: '0 0 15px 0' }}>
                        <button className={getButtonClass('box_select')} onClick={() => setMode('box_select')} style={{ flex: 1, minWidth: '45%' }}>
                            <IconDraw /> Select Points
                        </button>
                        <button className={getButtonClass('select_path')} onClick={() => setMode('select_path')} style={{ flex: 1, minWidth: '90%' }}>
                            <IconDraw /> Select Path
                        </button>
                    </div>

                    <h4 style={{ margin: '0 0 10px 0', fontSize: '0.9rem', textTransform: 'uppercase', color: 'var(--text-secondary)' }}>Settings</h4>

                    <div style={{ display: 'flex', flexDirection: 'column', gap: '15px' }}>
                        {/* Zone Setting */}
                        <div>
                            <label style={{ display: 'block', marginBottom: '5px', fontSize: '0.9rem' }}>
                                Zone (Lane ID) {zoneVal === '-' && <span style={{ color: 'var(--text-secondary)', fontSize: '0.8rem' }}>(mixed)</span>}
                            </label>
                            <input
                                type="text"
                                value={zoneVal}
                                onChange={(e) => setZoneVal(e.target.value)}
                                onKeyDown={(e) => e.key === 'Enter' && handleApplyControls()}
                                placeholder={zoneVal === '-' ? '-' : ''}
                                style={{
                                    width: '100%',
                                    padding: '8px',
                                    background: 'var(--input-bg)',
                                    border: '1px solid var(--border-color)',
                                    color: 'var(--text-primary)',
                                    borderRadius: '4px'
                                }}
                            />
                        </div>

                        {/* Indicator Setting */}
                        <div>
                            <label style={{ display: 'block', marginBottom: '8px', fontSize: '0.9rem' }}>
                                Indicator {indicatorVal === '-' && <span style={{ color: 'var(--text-secondary)', fontSize: '0.8rem' }}>(mixed)</span>}
                            </label>
                            <div style={{ display: 'flex', flexDirection: 'column', gap: '8px' }}>
                                <label style={{ display: 'flex', alignItems: 'center', gap: '8px', cursor: 'pointer' }}>
                                    <input
                                        type="radio"
                                        name="indicator"
                                        value="1"
                                        checked={indicatorVal === '1'}
                                        onChange={(e) => setIndicatorVal(e.target.value)}
                                    />
                                    1. No Indicator
                                </label>
                                <label style={{ display: 'flex', alignItems: 'center', gap: '8px', cursor: 'pointer' }}>
                                    <input
                                        type="radio"
                                        name="indicator"
                                        value="2"
                                        checked={indicatorVal === '2'}
                                        onChange={(e) => setIndicatorVal(e.target.value)}
                                    />
                                    2. Right
                                </label>
                                <label style={{ display: 'flex', alignItems: 'center', gap: '8px', cursor: 'pointer' }}>
                                    <input
                                        type="radio"
                                        name="indicator"
                                        value="3"
                                        checked={indicatorVal === '3'}
                                        onChange={(e) => setIndicatorVal(e.target.value)}
                                    />
                                    3. Left
                                </label>
                                <label style={{ display: 'flex', alignItems: 'center', gap: '8px', cursor: 'pointer' }}>
                                    <input
                                        type="radio"
                                        name="indicator"
                                        value="4"
                                        checked={indicatorVal === '4'}
                                        onChange={(e) => setIndicatorVal(e.target.value)}
                                    />
                                    4. Both Indicators
                                </label>
                            </div>
                        </div>

                        <button
                            className="toolbar-button confirm"
                            onClick={handleApplyControls}
                            disabled={selectedNodeIds.length === 0}
                            style={{ justifyContent: 'center', marginTop: '10px' }}
                        >
                            <IconCheck /> Apply to Selected ({selectedNodeIds.length})
                        </button>

                        {selectedNodeIds.length === 0 && (
                            <div style={{ fontSize: '0.8rem', color: 'var(--text-secondary)', marginTop: '5px', textAlign: 'center' }}>
                                Select nodes to apply settings.
                            </div>
                        )}
                    </div>
                </div>
            )}

            <div style={{ flex: 1 }}></div>

            <div className="sidebar-section">
                <button className="toolbar-button" onClick={() => useStore.getState().setFileLoaderOpen(true)}>
                    <IconSave /> Load Data
                </button>
                <button className="toolbar-button" onClick={saveData} style={{ marginTop: '10px' }}>
                    <IconSave /> Save Data
                </button>
            </div>
        </div>
    );
};

export default Sidebar;
