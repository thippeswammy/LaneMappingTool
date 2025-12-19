import React, { useEffect, useState } from 'react';
import { useStore } from '../store';
import { IconSave, IconCheck, IconCancel, IconRefresh } from './Icons';

/**
 * Component for loading files and managing data directories.
 *
 * This component fetches available files and allows users to select raw or saved data files for loading.
 * It manages custom directory paths and handles the loading and unloading of data based on user interactions.
 * The component also provides a user interface for toggling between raw and saved data views, and for confirming file selections.
 *
 * @param {Object} props - The component properties.
 * @param {Function} props.onClose - Callback function to close the file loader.
 */
const FileLoader = ({ onClose }) => {
    const availableFiles = useStore(state => state.availableFiles);
    const fetchFiles = useStore(state => state.fetchFiles);
    const loadData = useStore(state => state.loadData);
    const unloadData = useStore(state => state.unloadData);
    const refreshLane = useStore(state => state.refreshLane);
    const loadedFileNames = useStore(state => state.fileNames);
    const currentRawDir = useStore(state => state.currentRawDir);
    const currentSavedDir = useStore(state => state.currentSavedDir);

    const [selectedRawFiles, setSelectedRawFiles] = useState([]);
    const [selectedSavedNodes, setSelectedSavedNodes] = useState(null);
    const [selectedSavedEdges, setSelectedSavedEdges] = useState(null);
    const [activeTab, setActiveTab] = useState('raw'); // 'raw' or 'saved'

    // Raw Dir State
    const [isCustomDir, setIsCustomDir] = useState(false);
    const [customPath, setCustomPath] = useState('');

    // Saved Dir State
    const [isCustomSavedDir, setIsCustomSavedDir] = useState(false);
    const [customSavedPath, setCustomSavedPath] = useState('');

    useEffect(() => {
        fetchFiles();
    }, [fetchFiles]);

    // Update local custom dir state when store updates
    useEffect(() => {
        if (availableFiles.subdirs) {
            const isKnownSubdir = availableFiles.subdirs.includes(currentRawDir);
            if (!isKnownSubdir && currentRawDir) {
                setIsCustomDir(true);
                setCustomPath(currentRawDir);
            }
        }
    }, [currentRawDir, availableFiles.subdirs]);

    // Update local custom saved dir state
    useEffect(() => {
        if (currentSavedDir && currentSavedDir !== "CUSTOM") {
            setIsCustomSavedDir(true);
            setCustomSavedPath(currentSavedDir);
        }
    }, [currentSavedDir]);

    // Raw Dir Handlers
    const handleDirChange = (e) => {
        const value = e.target.value;
        if (value === 'CUSTOM') {
            setIsCustomDir(true);
            setCustomPath('');
        } else {
            setIsCustomDir(false);
            fetchFiles(value, currentSavedDir);
        }
    };

    const handleCustomPathSubmit = () => {
        if (customPath) {
            fetchFiles(customPath, currentSavedDir);
        }
    };

    // Saved Dir Handlers
    const handleSavedDirChange = (e) => {
        const value = e.target.value;
        if (value === 'CUSTOM') {
            setIsCustomSavedDir(true);
            setCustomSavedPath('');
        } else {
            setIsCustomSavedDir(false);
            fetchFiles(currentRawDir, value);
        }
    };

    const handleCustomSavedPathSubmit = () => {
        if (customSavedPath) {
            fetchFiles(currentRawDir, customSavedPath);
        }
    };

    const handleRawFileToggle = (fileName) => {
        if (loadedFileNames.includes(fileName)) {
            unloadData(fileName);
        } else {
            setSelectedRawFiles(prev => {
                if (prev.includes(fileName)) {
                    return prev.filter(f => f !== fileName);
                } else {
                    return [...prev, fileName];
                }
            });
        }
    };

    const handleLoad = () => {
        loadData(selectedRawFiles, selectedSavedNodes, selectedSavedEdges, currentRawDir, currentSavedDir);
        onClose();
    };

    return (
        <div className="file-loader-overlay" style={{
            position: 'absolute',
            top: 0,
            left: 0,
            right: 0,
            bottom: 0,
            background: 'rgba(0, 0, 0, 0.7)',
            display: 'flex',
            justifyContent: 'center',
            alignItems: 'center',
            zIndex: 1000
        }}>
            <div className="file-loader-modal" style={{
                background: 'var(--bg-secondary)',
                padding: '20px',
                borderRadius: '8px',
                width: '500px',
                maxHeight: '80vh',
                display: 'flex',
                flexDirection: 'column',
                gap: '15px',
                boxShadow: '0 4px 6px rgba(0,0,0,0.3)',
                border: '1px solid var(--border-color)'
            }}>
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                    <h3 style={{ margin: 0, color: 'var(--text-primary)' }}>Load Data</h3>
                    <button onClick={onClose} style={{ background: 'none', border: 'none', color: 'var(--text-secondary)', cursor: 'pointer' }}>
                        <IconCancel />
                    </button>
                </div>

                <div className="tabs" style={{ display: 'flex', gap: '10px', borderBottom: '1px solid var(--border-color)', paddingBottom: '10px' }}>
                    <button
                        onClick={() => setActiveTab('raw')}
                        style={{
                            background: 'none',
                            border: 'none',
                            color: activeTab === 'raw' ? 'var(--accent-color)' : 'var(--text-secondary)',
                            fontWeight: activeTab === 'raw' ? 'bold' : 'normal',
                            cursor: 'pointer',
                            padding: '5px 10px'
                        }}
                    >
                        Raw Data (.npy)
                    </button>
                    <button
                        onClick={() => setActiveTab('saved')}
                        style={{
                            background: 'none',
                            border: 'none',
                            color: activeTab === 'saved' ? 'var(--accent-color)' : 'var(--text-secondary)',
                            fontWeight: activeTab === 'saved' ? 'bold' : 'normal',
                            cursor: 'pointer',
                            padding: '5px 10px'
                        }}
                    >
                        Saved Graphs
                    </button>
                </div>

                <div className="file-list" style={{ flex: 1, overflowY: 'auto', minHeight: '200px', border: '1px solid var(--border-color)', borderRadius: '4px', padding: '10px', background: 'var(--bg-primary)' }}>
                    {activeTab === 'raw' && (
                        <div>
                            <div style={{ marginBottom: '10px', display: 'flex', alignItems: 'center', gap: '10px' }}>
                                <label style={{ color: 'var(--text-secondary)' }}>Directory:</label>
                                <select
                                    value={isCustomDir ? 'CUSTOM' : currentRawDir}
                                    onChange={handleDirChange}
                                    style={{ padding: '5px', borderRadius: '4px', background: 'var(--bg-tertiary)', color: 'var(--text-primary)', border: '1px solid var(--border-color)' }}
                                >
                                    {availableFiles.subdirs && availableFiles.subdirs.map(subdir => (
                                        <option key={subdir} value={subdir}>{subdir}</option>
                                    ))}
                                    <option value="CUSTOM">Custom Path...</option>
                                </select>
                            </div>
                            {isCustomDir && (
                                <div style={{ marginBottom: '10px', display: 'flex', gap: '5px' }}>
                                    <input
                                        type="text"
                                        value={customPath}
                                        onChange={(e) => setCustomPath(e.target.value)}
                                        placeholder="Enter full path (e.g. F:\Projects\Data)"
                                        style={{ flex: 1, padding: '5px', borderRadius: '4px', background: 'var(--bg-tertiary)', color: 'var(--text-primary)', border: '1px solid var(--border-color)' }}
                                    />
                                    <button
                                        onClick={handleCustomPathSubmit}
                                        style={{ padding: '5px 10px', borderRadius: '4px', background: 'var(--accent-color)', color: 'white', border: 'none', cursor: 'pointer' }}
                                    >
                                        Go
                                    </button>
                                </div>
                            )}
                            <p style={{ margin: '0 0 10px 0', fontSize: '0.8rem', color: 'var(--text-secondary)' }}>
                                Location: {availableFiles.raw_path}
                            </p>
                            {availableFiles.raw_files.length === 0 ? (
                                <p style={{ color: 'var(--text-secondary)' }}>No raw data files found.</p>
                            ) : (
                                availableFiles.raw_files.map(file => {
                                    const isLoaded = loadedFileNames.includes(file);
                                    return (
                                        <div key={file} style={{ display: 'flex', alignItems: 'center', gap: '10px', padding: '5px 0' }}>
                                            <input
                                                type="checkbox"
                                                checked={selectedRawFiles.includes(file) || isLoaded}
                                                onChange={() => handleRawFileToggle(file)}
                                                id={`raw-${file}`}
                                            />
                                            <label
                                                htmlFor={`raw-${file}`}
                                                style={{
                                                    color: 'var(--text-primary)',
                                                    cursor: 'pointer',
                                                    flex: 1
                                                }}
                                            >
                                                {file} {isLoaded && "(Loaded)"}
                                            </label>
                                            {isLoaded && (
                                                <button
                                                    onClick={(e) => {
                                                        e.stopPropagation();
                                                        if (window.confirm(`Are you sure you want to refresh ${file}? This will unload the file and discard unsaved edits.`)) {
                                                            refreshLane(file);
                                                            setSelectedRawFiles(prev => prev.filter(f => f !== file));
                                                        }
                                                    }}
                                                    title="Refresh (Discard edits and reload original)"
                                                    style={{
                                                        background: 'none',
                                                        border: 'none',
                                                        color: 'var(--text-secondary)',
                                                        cursor: 'pointer',
                                                        padding: '2px'
                                                    }}
                                                >
                                                    <IconRefresh size={14} />
                                                </button>
                                            )}
                                        </div>
                                    );
                                })
                            )}
                        </div>
                    )}

                    {activeTab === 'saved' && (
                        <div>
                            <div style={{ marginBottom: '10px', display: 'flex', alignItems: 'center', gap: '10px' }}>
                                <label style={{ color: 'var(--text-secondary)' }}>Directory:</label>
                                <select
                                    value={isCustomSavedDir ? 'CUSTOM' : currentSavedDir}
                                    onChange={handleSavedDirChange}
                                    style={{ padding: '5px', borderRadius: '4px', background: 'var(--bg-tertiary)', color: 'var(--text-primary)', border: '1px solid var(--border-color)' }}
                                >
                                    <option value="">Default (files)</option>
                                    <option value="CUSTOM">Custom Path...</option>
                                </select>
                            </div>
                            {isCustomSavedDir && (
                                <div style={{ marginBottom: '10px', display: 'flex', gap: '5px' }}>
                                    <input
                                        type="text"
                                        value={customSavedPath}
                                        onChange={(e) => setCustomSavedPath(e.target.value)}
                                        placeholder="Enter full path (e.g. F:\Projects\Saved)"
                                        style={{ flex: 1, padding: '5px', borderRadius: '4px', background: 'var(--bg-tertiary)', color: 'var(--text-primary)', border: '1px solid var(--border-color)' }}
                                    />
                                    <button
                                        onClick={handleCustomSavedPathSubmit}
                                        style={{ padding: '5px 10px', borderRadius: '4px', background: 'var(--accent-color)', color: 'white', border: 'none', cursor: 'pointer' }}
                                    >
                                        Go
                                    </button>
                                </div>
                            )}
                            <p style={{ margin: '0 0 10px 0', fontSize: '0.8rem', color: 'var(--text-secondary)' }}>
                                Location: {availableFiles.saved_path}
                            </p>
                            <div style={{ marginBottom: '15px' }}>
                                <h5 style={{ margin: '0 0 5px 0', color: 'var(--text-secondary)' }}>Nodes File</h5>
                                <select
                                    value={selectedSavedNodes || ''}
                                    onChange={(e) => setSelectedSavedNodes(e.target.value)}
                                    style={{ width: '100%', padding: '5px', background: 'var(--bg-tertiary)', color: 'var(--text-primary)', border: '1px solid var(--border-color)' }}
                                >
                                    <option value="">Select Nodes File</option>
                                    {availableFiles.saved_files.filter(f => f.includes('nodes')).map(file => (
                                        <option key={file} value={file}>{file}</option>
                                    ))}
                                </select>
                            </div>
                            <div>
                                <h5 style={{ margin: '0 0 5px 0', color: 'var(--text-secondary)' }}>Edges File</h5>
                                <select
                                    value={selectedSavedEdges || ''}
                                    onChange={(e) => setSelectedSavedEdges(e.target.value)}
                                    style={{ width: '100%', padding: '5px', background: 'var(--bg-tertiary)', color: 'var(--text-primary)', border: '1px solid var(--border-color)' }}
                                >
                                    <option value="">Select Edges File</option>
                                    {availableFiles.saved_files.filter(f => f.includes('edges')).map(file => (
                                        <option key={file} value={file}>{file}</option>
                                    ))}
                                </select>
                            </div>
                            <div style={{ marginTop: '15px', display: 'flex', justifyContent: 'flex-end' }}>
                                <button
                                    onClick={() => {
                                        useStore.getState().unloadGraph();
                                    }}
                                    style={{
                                        padding: '5px 10px',
                                        borderRadius: '4px',
                                        background: '#d32f2f',
                                        color: 'white',
                                        border: 'none',
                                        cursor: 'pointer',
                                        display: 'flex',
                                        alignItems: 'center',
                                        gap: '5px',
                                        fontSize: '0.8rem'
                                    }}
                                >
                                    <IconCancel size={14} /> Unload Graph Data
                                </button>
                            </div>
                        </div>
                    )}
                </div>

                <div className="actions" style={{ display: 'flex', justifyContent: 'flex-end', gap: '10px' }}>
                    <button onClick={onClose} className="toolbar-button" style={{ width: 'auto', padding: '8px 15px' }}>
                        Cancel
                    </button>
                    <button onClick={handleLoad} className="toolbar-button confirm" style={{ width: 'auto', padding: '8px 15px' }}>
                        <IconCheck /> Load Selected
                    </button>
                </div>
            </div>
        </div>
    );
};

export default FileLoader;
