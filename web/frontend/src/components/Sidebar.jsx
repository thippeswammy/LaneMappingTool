import React, { useState, useEffect } from 'react';
import { useStore } from '../store';
import './Toolbar.css';
import {
    IconDraw, IconSmooth, IconConnect, IconRemove, IconReverse, IconSave, IconCheck, IconCancel, IconZoom, IconTwoWay, IconCar, IconGraph
} from './Icons';
// import YawAnalysisTool from './YawAnalysisTool'; // Moved to main panel

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
    const selectedNodeIds = useStore(state => state.selectedNodeIds) || [];
    const setSelectedNodeIds = useStore(state => state.setSelectedNodeIds);
    const showYaw = useStore(state => state.showYaw);
    const toggleShowYaw = useStore(state => state.toggleShowYaw);

    const nodes = useStore(state => state.nodes);
    const updateNodeProperties = useStore(state => state.updateNodeProperties);

    const showSavedGraph = useStore(state => state.showSavedGraph);
    const toggleShowSavedGraph = useStore(state => state.toggleShowSavedGraph);

    // Simulation State & Actions
    const simulationFiles = useStore(state => state.simulationFiles);
    const fetchSimulationFiles = useStore(state => state.fetchSimulationFiles);
    const loadSimulationPoints = useStore(state => state.loadSimulationPoints);
    const simulationPoints = useStore(state => state.simulationPoints);
    const activeSimulationPath = useStore(state => state.activeSimulationPath);
    const isSimulating = useStore(state => state.isSimulating);
    const startSimulation = useStore(state => state.startSimulation);
    const stopSimulation = useStore(state => state.stopSimulation);
    const computeSimulationPath = useStore(state => state.computeSimulationPath);
    const setCarPosition = useStore(state => state.setCarPosition);
    const simStartPose = useStore(state => state.simStartPose);
    const setSimStartPose = useStore(state => state.setSimStartPose);
    const simEndPose = useStore(state => state.simEndPose);
    const setSimEndPose = useStore(state => state.setSimEndPose);

    // Initial Fetch for Sim Files
    useEffect(() => {
        if (sidebarMode === 'simulation') {
            fetchSimulationFiles();
        }
    }, [sidebarMode, fetchSimulationFiles]);

    const [selectedSimFile, setSelectedSimFile] = useState('');

    const handleLoadSimFile = () => {
        if (selectedSimFile) {
            loadSimulationPoints(selectedSimFile);
        }
    };

    const handlePlayPath = async () => {
        const start = simStartPose;
        const end = simEndPose;
        if (start && end) {
            const path = await computeSimulationPath(start, end);
            if (path && path.length > 0) {
                startSimulation();

                // Animation Logic
                let step = 0;

                const animate = () => {
                    // Check if simulation was stopped by user or component unmount
                    // access fresh state via useStore.getState() if needed, or rely on closure if isSimulating isn't toggled externally
                    // But here 'isSimulating' is from render scope. 
                    // Better to check store directly or use a ref.
                    if (!useStore.getState().isSimulating) return;

                    if (step < path.length) {
                        setCarPosition(path[step]);
                        step++;
                        setTimeout(() => requestAnimationFrame(animate), 50); // 50ms per step (faster)
                    } else {
                        stopSimulation();
                    }
                };

                requestAnimationFrame(animate);
            }
        }
    };

    // Auto Test Logic (Simple iteration)
    const [autoTestRunning, setAutoTestRunning] = useState(false);
    const [autoTestLog, setAutoTestLog] = useState([]);

    const handleAutoTest = async () => {
        if (simulationPoints.length < 2) return;
        setAutoTestRunning(true);
        setAutoTestLog([]);

        let logs = [];
        for (let i = 0; i < simulationPoints.length; i++) {
            for (let j = 0; j < simulationPoints.length; j++) {
                if (i === j) continue;
                const start = simulationPoints[i];
                const end = simulationPoints[j];

                // Update Log
                logs.push(`Testing ${start.name} -> ${end.name}...`);
                setAutoTestLog([...logs]);

                // Compute path
                const path = await computeSimulationPath(start.name, end.name);

                if (path) {
                    logs[logs.length - 1] += " OK";
                    startSimulation();
                    // Wait for simulation to finish? 
                    // For now just wait a few seconds then move to next?
                    // Or just check path existence. 
                    // User said "while running i need to see the car moving".
                    // So we should probably wait.
                    await new Promise(r => setTimeout(r, 5000)); // Wait 5s for animation
                    stopSimulation();
                } else {
                    logs[logs.length - 1] += " FAILED";
                }
                setAutoTestLog([...logs]);
            }
        }
        setAutoTestRunning(false);
    };

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

    const handleReverseIndicators = () => {
        if (selectedNodeIds.length === 0) return;
        performOperation('reverse_indicators', { point_ids: selectedNodeIds });
        // Optional: Can keep selection or clear it. Let's keep it to see results if we refresh, 
        // but performOperation usually triggers a refresh which might update our local node data.
        // The store handles updates.
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
            {/* Mode Switcher */}
            <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '10px' }}>
                <button
                    className={`toolbar-button ${sidebarMode === 'edit' ? 'active' : ''}`}
                    onClick={() => setSidebarMode('edit')}
                    style={{ justifyContent: 'center' }}
                >
                    Edit
                </button>
                <button
                    className={`toolbar-button ${sidebarMode === 'control' ? 'active' : ''}`}
                    onClick={() => setSidebarMode('control')}
                    style={{ justifyContent: 'center' }}
                >
                    Config
                </button>
                <button
                    className={`toolbar-button ${sidebarMode === 'simulation' ? 'active' : ''}`}
                    onClick={() => setSidebarMode('simulation')}
                    style={{ justifyContent: 'center' }}
                >
                    Sim
                </button>
                <button
                    className={`toolbar-button ${sidebarMode === 'analysis' ? 'active' : ''}`}
                    onClick={() => setSidebarMode('analysis')}
                    style={{ justifyContent: 'center' }}
                >
                    Graph
                </button>
            </div>

            <hr style={{ border: '0', borderTop: '1px solid var(--border-color)', width: '100%', margin: '0' }} />

            {
                sidebarMode === 'edit' && (
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



                        {selectedNodeIds.length > 1 && (
                            <div className="sidebar-section">
                                <h4 style={{ margin: '0 0 10px 0', fontSize: '0.9rem', textTransform: 'uppercase', color: 'var(--text-secondary)' }}>Path Validation</h4>
                                <button className="toolbar-button" onClick={() => useStore.getState().checkPathDirection(selectedNodeIds[0], selectedNodeIds[selectedNodeIds.length - 1])}>
                                    <IconCheck /> Check Direction
                                </button>
                                {useStore(state => state.pathDirectionStatus) && (
                                    <div style={{
                                        marginTop: '10px',
                                        padding: '8px',
                                        background: 'var(--bg-tertiary)',
                                        borderRadius: '4px',
                                        border: '1px solid var(--border-color)',
                                        fontSize: '0.85rem'
                                    }}>
                                        <div style={{ fontWeight: 'bold', marginBottom: '5px' }}>
                                            {useStore.getState().pathDirectionStatus.overall_status}
                                        </div>
                                        {useStore.getState().pathDirectionStatus.details.some(d => d.status === 'mismatch') && (
                                            <div style={{ color: '#ff6b6b' }}>
                                                mismatches found!
                                            </div>
                                        )}
                                        <button style={{ marginTop: '5px', width: '100%', padding: '4px', background: '#444', border: 'none', color: 'white', borderRadius: '2px', cursor: 'pointer' }} onClick={() => useStore.getState().clearPathDirectionStatus()}>
                                            Clear
                                        </button>
                                    </div>
                                )}
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

                            <button className={getButtonClass('two_way_road')} onClick={() => setMode('two_way_road')}>
                                <IconTwoWay /> Two-Way Road
                            </button>

                            <div style={{ display: 'flex', gap: '5px' }}>
                                <label className="toolbar-button" style={{ justifyContent: 'center', cursor: 'pointer', flex: 1, fontSize: '0.8rem', padding: '5px' }}>
                                    <input
                                        type="checkbox"
                                        checked={showYaw}
                                        onChange={toggleShowYaw}
                                        style={{ marginRight: '5px' }}
                                    />
                                    Show Yaw
                                </label>

                                <label className="toolbar-button" style={{ justifyContent: 'center', cursor: 'pointer', flex: 1, fontSize: '0.8rem', padding: '5px' }}>
                                    <input
                                        type="checkbox"
                                        checked={showSavedGraph}
                                        onChange={toggleShowSavedGraph}
                                        style={{ marginRight: '5px' }}
                                    />
                                    Show Saved
                                </label>
                            </div>
                        </div>
                    </>
                )
            }

            {
                sidebarMode === 'control' && (
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
                                        2. Left
                                    </label>
                                    <label style={{ display: 'flex', alignItems: 'center', gap: '8px', cursor: 'pointer' }}>
                                        <input
                                            type="radio"
                                            name="indicator"
                                            value="3"
                                            checked={indicatorVal === '3'}
                                            onChange={(e) => setIndicatorVal(e.target.value)}
                                        />
                                        3. Right
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

                            <button
                                className="toolbar-button"
                                onClick={handleReverseIndicators}
                                disabled={selectedNodeIds.length === 0}
                                style={{ justifyContent: 'center', marginTop: '10px' }}
                            >
                                <IconReverse /> Reverse Indicators (2↔3)
                            </button>

                            {selectedNodeIds.length === 0 && (
                                <div style={{ fontSize: '0.8rem', color: 'var(--text-secondary)', marginTop: '5px', textAlign: 'center' }}>
                                    Select nodes to apply settings.
                                </div>
                            )}
                        </div>
                    </div>
                )
            }

            {
                sidebarMode === 'simulation' && (
                    <div className="sidebar-section">
                        <h4 style={{ margin: '0 0 10px 0', fontSize: '0.9rem', textTransform: 'uppercase', color: 'var(--text-secondary)' }}>Simulation Control</h4>

                        {/* File Selection */}
                        <div style={{ marginBottom: '15px' }}>
                            <label style={{ display: 'block', marginBottom: '5px', fontSize: '0.9rem' }}>Select Simulation File:</label>
                            <div style={{ display: 'flex', gap: '5px' }}>
                                <select
                                    value={selectedSimFile}
                                    onChange={(e) => setSelectedSimFile(e.target.value)}
                                    style={{ flex: 1, padding: '5px', borderRadius: '4px', background: 'var(--bg-tertiary)', color: 'var(--text-primary)', border: '1px solid var(--border-color)' }}
                                >
                                    <option value="">Select File...</option>
                                    {simulationFiles.map(f => <option key={f} value={f}>{f}</option>)}
                                </select>
                                <button className="toolbar-button" onClick={handleLoadSimFile} disabled={!selectedSimFile} style={{ padding: '5px 10px' }}>
                                    Load
                                </button>
                            </div>
                        </div>

                        {/* Simulation Points loaded */}
                        {simulationPoints.length > 0 && (
                            <>
                                <div style={{ padding: '8px', background: 'var(--bg-tertiary)', borderRadius: '4px', marginBottom: '15px', border: '1px solid var(--border-color)' }}>
                                    <div style={{ fontWeight: 'bold', marginBottom: '5px' }}>Loaded Points: {simulationPoints.length}</div>
                                    <div style={{ maxHeight: '100px', overflowY: 'auto', fontSize: '0.8rem', color: 'var(--text-secondary)' }}>
                                        {simulationPoints.map((p, i) => (
                                            <div key={i}>{p.name} ({p.x.toFixed(1)}, {p.y.toFixed(1)})</div>
                                        ))}
                                    </div>
                                </div>

                                <hr style={{ border: '0', borderTop: '1px solid var(--border-color)', margin: '15px 0' }} />

                                {/* Manual Test */}
                                <h5 style={{ margin: '0 0 10px 0', color: 'var(--text-secondary)' }}>Manual Test</h5>
                                <div style={{ display: 'flex', flexDirection: 'column', gap: '10px', marginBottom: '15px' }}>
                                    {/* Start Pose */}
                                    <div style={{ display: 'flex', gap: '5px' }}>
                                        <select
                                            value={simStartPose?.name || ''}
                                            onChange={(e) => {
                                                if (e.target.value.startsWith('Manual_')) return;
                                                const p = simulationPoints.find(pt => pt.name === e.target.value);
                                                if (p) setSimStartPose(p);
                                            }}
                                            style={{ flex: 1, padding: '5px', borderRadius: '4px', background: 'var(--bg-tertiary)', color: 'var(--text-primary)', border: '1px solid var(--border-color)' }}
                                        >
                                            <option value="">Start Point...</option>
                                            {simStartPose?.name?.startsWith('Manual_') && (
                                                <option value={simStartPose.name}>{simStartPose.name}</option>
                                            )}
                                            {simulationPoints.map(p => <option key={p.name} value={p.name}>{p.name}</option>)}
                                        </select>
                                        <button
                                            className={`toolbar-button ${mode === 'set_sim_start' ? 'active' : ''}`}
                                            onClick={() => setMode('set_sim_start')}
                                            title="Set Start Pose by Click & Drag"
                                            style={{ padding: '5px' }}
                                        >
                                            <IconCar size={16} />
                                        </button>
                                    </div>

                                    {/* End Pose */}
                                    <div style={{ display: 'flex', gap: '5px' }}>
                                        <select
                                            value={simEndPose?.name || ''}
                                            onChange={(e) => {
                                                if (e.target.value.startsWith('Manual_')) return;
                                                const p = simulationPoints.find(pt => pt.name === e.target.value);
                                                if (p) setSimEndPose(p);
                                            }}
                                            style={{ flex: 1, padding: '5px', borderRadius: '4px', background: 'var(--bg-tertiary)', color: 'var(--text-primary)', border: '1px solid var(--border-color)' }}
                                        >
                                            <option value="">End Point...</option>
                                            {simEndPose?.name?.startsWith('Manual_') && (
                                                <option value={simEndPose.name}>{simEndPose.name}</option>
                                            )}
                                            {simulationPoints.map(p => <option key={p.name} value={p.name}>{p.name}</option>)}
                                        </select>
                                        <button
                                            className={`toolbar-button ${mode === 'set_sim_end' ? 'active' : ''}`}
                                            onClick={() => setMode('set_sim_end')}
                                            title="Set End Pose by Click & Drag"
                                            style={{ padding: '5px' }}
                                        >
                                            <IconCar size={16} />
                                        </button>
                                    </div>

                                    <div style={{ display: 'flex', gap: '5px' }}>
                                        <button
                                            className="toolbar-button confirm"
                                            onClick={handlePlayPath}
                                            disabled={!simStartPose || !simEndPose || isSimulating}
                                            style={{ justifyContent: 'center', flex: 1 }}
                                        >
                                            <IconCar /> Play Path
                                        </button>
                                        {isSimulating && (
                                            <button className="toolbar-button" onClick={stopSimulation} style={{ justifyContent: 'center', background: '#d32f2f' }}>
                                                Stop
                                            </button>
                                        )}
                                    </div>
                                </div>

                                <hr style={{ border: '0', borderTop: '1px solid var(--border-color)', margin: '15px 0' }} />

                                {/* Auto Test */}
                                <h5 style={{ margin: '0 0 10px 0', color: 'var(--text-secondary)' }}>Auto Test</h5>
                                <button
                                    className="toolbar-button"
                                    onClick={handleAutoTest}
                                    disabled={autoTestRunning}
                                    style={{ justifyContent: 'center', marginBottom: '10px' }}
                                >
                                    {autoTestRunning ? 'Running Test...' : 'Run Full AutoTest'}
                                </button>

                                {autoTestLog.length > 0 && (
                                    <div style={{
                                        maxHeight: '150px',
                                        overflowY: 'auto',
                                        background: 'black',
                                        color: '#0f0',
                                        padding: '5px',
                                        fontSize: '0.75rem',
                                        fontFamily: 'monospace',
                                        borderRadius: '4px'
                                    }}>
                                        {autoTestLog.map((log, i) => <div key={i}>{log}</div>)}
                                    </div>
                                )}
                            </>
                        )}
                    </div>
                )}

            {
                sidebarMode === 'analysis' && (
                    <div className="sidebar-section">
                        <div style={{ padding: '10px', color: '#aaa', fontSize: '0.9rem', textAlign: 'center' }}>
                            <IconGraph size={32} style={{ marginBottom: '10px', opacity: 0.5 }} />
                            <p>Graph Analysis Mode Active</p>
                            <p style={{ fontSize: '0.8rem' }}>Detailed analysis is now shown in the right panel.</p>
                        </div>
                    </div>
                )
            }

            <div style={{ flex: 1 }}></div>

            <div className="sidebar-section">
                <div style={{ display: 'flex', gap: '10px' }}>
                    <button className="toolbar-button" onClick={() => useStore.getState().setFileLoaderOpen(true)} style={{ flex: 1 }}>
                        <IconSave /> Load Data
                    </button>
                    <button
                        className="toolbar-button"
                        onClick={() => {
                            if (window.confirm("Are you sure you want to unload all graph data? Unsaved changes will be lost.")) {
                                useStore.getState().unloadGraph();
                            }
                        }}
                        style={{ background: '#d32f2f', color: 'white', flex: 1 }}
                        title="Unload all data from the graph"
                    >
                        Unload Data
                    </button>
                </div>
                <button className="toolbar-button" onClick={saveData} style={{ marginTop: '10px' }}>
                    <IconSave /> Save Data
                </button>
            </div>
        </div>
    );
};
export default Sidebar;
