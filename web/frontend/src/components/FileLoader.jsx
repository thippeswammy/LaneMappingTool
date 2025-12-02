import React, { useEffect, useState } from 'react';
import { useStore } from '../store';
import { IconSave, IconCheck, IconCancel } from './Icons';

const FileLoader = ({ onClose }) => {
    const availableFiles = useStore(state => state.availableFiles);
    const fetchFiles = useStore(state => state.fetchFiles);
    const loadData = useStore(state => state.loadData);

    const [selectedRawFiles, setSelectedRawFiles] = useState([]);
    const [selectedSavedNodes, setSelectedSavedNodes] = useState(null);
    const [selectedSavedEdges, setSelectedSavedEdges] = useState(null);
    const [activeTab, setActiveTab] = useState('raw'); // 'raw' or 'saved'

    useEffect(() => {
        fetchFiles();
    }, [fetchFiles]);

    const handleRawFileToggle = (fileName) => {
        setSelectedRawFiles(prev => {
            if (prev.includes(fileName)) {
                return prev.filter(f => f !== fileName);
            } else {
                return [...prev, fileName];
            }
        });
    };

    const handleLoad = () => {
        loadData(selectedRawFiles, selectedSavedNodes, selectedSavedEdges);
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
                            <p style={{ margin: '0 0 10px 0', fontSize: '0.8rem', color: 'var(--text-secondary)' }}>
                                Location: {availableFiles.raw_path}
                            </p>
                            {availableFiles.raw_files.length === 0 ? (
                                <p style={{ color: 'var(--text-secondary)' }}>No raw data files found.</p>
                            ) : (
                                availableFiles.raw_files.map(file => (
                                    <div key={file} style={{ display: 'flex', alignItems: 'center', gap: '10px', padding: '5px 0' }}>
                                        <input
                                            type="checkbox"
                                            checked={selectedRawFiles.includes(file)}
                                            onChange={() => handleRawFileToggle(file)}
                                            id={`raw-${file}`}
                                        />
                                        <label htmlFor={`raw-${file}`} style={{ color: 'var(--text-primary)', cursor: 'pointer', flex: 1 }}>{file}</label>
                                    </div>
                                ))
                            )}
                        </div>
                    )}

                    {activeTab === 'saved' && (
                        <div>
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
