import React, { useState, useEffect } from 'react';
import { IconCancel } from './Icons';

const DirectoryBrowser = ({ initialPath, onSelect, onClose }) => {
    const [currentPath, setCurrentPath] = useState(initialPath || 'C:\\');
    const [items, setItems] = useState({ directories: [], files: [], parent: '' });
    const [error, setError] = useState(null);

    useEffect(() => {
        // Initial fetch
        if (currentPath) fetchPath(currentPath);
    }, []); // Only on mount

    // Debounced fetch or manual fetch could be better, but for now simple effect on path change
    // We separate the effect to avoid fetching on every keystroke if we were using it for input
    useEffect(() => {
        fetchPath(currentPath);
    }, [currentPath]);

    const fetchPath = async (path) => {
        try {
            // Use relative path to avoid CORS issues
            const response = await fetch('/api/list_dirs', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ path })
            });

            if (!response.ok) {
                const errData = await response.json().catch(() => ({}));
                throw new Error(errData.error || `Error ${response.status}: Failed to list directory`);
            }

            const data = await response.json();
            setItems(data);
            setError(null);
        } catch (err) {
            setError(err.message);
        }
    };

    const handleDirClick = (dirName) => {
        // Handle root paths like C:\ correctly
        let newPath = currentPath;
        if (!newPath.endsWith('\\')) newPath += '\\';
        newPath += dirName;
        setCurrentPath(newPath);
    };

    const handleUpClick = () => {
        if (items.parent) {
            setCurrentPath(items.parent);
        }
    };

    const handlePathSubmit = (e) => {
        if (e.key === 'Enter') {
            fetchPath(currentPath);
        }
    };

    const handleDriveClick = (drive) => {
        setCurrentPath(`${drive}:\\`);
    };

    return (
        <div style={{
            position: 'absolute',
            top: 0, left: 0, right: 0, bottom: 0,
            background: 'rgba(0,0,0,0.85)',
            display: 'flex', justifyContent: 'center', alignItems: 'center',
            zIndex: 1100
        }}>
            <div style={{
                background: 'var(--bg-secondary)',
                padding: '24px',
                borderRadius: '12px',
                width: '700px',
                height: '80vh',
                display: 'flex', flexDirection: 'column',
                boxShadow: '0 8px 32px rgba(0,0,0,0.5)',
                border: '1px solid var(--border-color)',
                color: 'var(--text-primary)'
            }}>
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '16px' }}>
                    <h3 style={{ margin: 0, fontSize: '1.2rem' }}>Browse Directories</h3>
                    <button onClick={onClose} style={{ background: 'none', border: 'none', color: 'var(--text-secondary)', cursor: 'pointer', padding: '4px' }}>
                        <IconCancel size={20} />
                    </button>
                </div>

                {/* Drive Shortcuts */}
                <div style={{ display: 'flex', gap: '8px', marginBottom: '12px' }}>
                    <span style={{ display: 'flex', alignItems: 'center', color: 'var(--text-secondary)', fontSize: '0.9rem', marginRight: '5px' }}>Drives:</span>
                    {['C', 'D', 'E', 'F', 'G'].map(drive => (
                        <button
                            key={drive}
                            onClick={() => handleDriveClick(drive)}
                            style={{
                                padding: '4px 10px',
                                background: 'var(--bg-tertiary)',
                                border: '1px solid var(--border-color)',
                                borderRadius: '4px',
                                color: 'var(--text-primary)',
                                cursor: 'pointer',
                                fontSize: '0.9rem',
                                fontWeight: 'bold'
                            }}
                            title={`Go to ${drive}:\\`}
                        >
                            {drive}
                        </button>
                    ))}
                </div>

                <div style={{ display: 'flex', gap: '8px', marginBottom: '12px' }}>
                    <button
                        onClick={handleUpClick}
                        disabled={!items.parent}
                        style={{ padding: '8px 12px', cursor: 'pointer', borderRadius: '4px', border: '1px solid var(--border-color)', background: 'var(--bg-tertiary)', color: 'var(--text-primary)' }}
                        title="Go Up Level"
                    >
                        ⬆ Up
                    </button>
                    <div style={{ flex: 1, display: 'flex' }}>
                        <input
                            type="text"
                            value={currentPath}
                            onChange={(e) => setCurrentPath(e.target.value)}
                            onKeyDown={handlePathSubmit}
                            placeholder="Type path and press Enter..."
                            style={{
                                flex: 1,
                                padding: '8px',
                                background: 'var(--bg-tertiary)',
                                border: '1px solid var(--border-color)',
                                borderRight: 'none',
                                borderTopLeftRadius: '4px',
                                borderBottomLeftRadius: '4px',
                                color: 'var(--text-primary)'
                            }}
                        />
                        <button
                            onClick={() => fetchPath(currentPath)}
                            style={{
                                padding: '8px 12px',
                                border: '1px solid var(--border-color)',
                                borderLeft: 'none',
                                borderTopRightRadius: '4px',
                                borderBottomRightRadius: '4px',
                                background: 'var(--accent-color)',
                                color: 'white',
                                cursor: 'pointer'
                            }}
                        >
                            Go
                        </button>
                    </div>
                </div>

                {error && (
                    <div style={{
                        background: 'rgba(255, 0, 0, 0.1)',
                        border: '1px solid rgba(255, 0, 0, 0.3)',
                        color: '#ff6b6b',
                        padding: '10px',
                        borderRadius: '4px',
                        marginBottom: '12px',
                        fontSize: '0.9rem'
                    }}>
                        ⚠️ {error}
                    </div>
                )}

                <div style={{
                    flex: 1,
                    overflowY: 'auto',
                    border: '1px solid var(--border-color)',
                    borderRadius: '8px',
                    background: 'var(--bg-primary)',
                    padding: '8px'
                }}>
                    {items.directories.length === 0 && items.files.length === 0 && !error && (
                        <div style={{ padding: '20px', textAlign: 'center', color: 'var(--text-secondary)' }}>This folder is empty</div>
                    )}

                    {items.directories.map(dir => (
                        <div
                            key={dir}
                            onClick={() => handleDirClick(dir)}
                            style={{
                                padding: '8px 12px',
                                cursor: 'pointer',
                                color: 'var(--accent-color)',
                                display: 'flex', alignItems: 'center', gap: '8px',
                                borderRadius: '4px',
                                transition: 'background 0.2s',
                                marginBottom: '2px'
                            }}
                            onMouseEnter={(e) => e.target.style.background = 'var(--bg-tertiary)'}
                            onMouseLeave={(e) => e.target.style.background = 'transparent'}
                        >
                            <span style={{ fontSize: '1.2rem' }}>📁</span> {dir}
                        </div>
                    ))}
                    {items.files.map(file => (
                        <div key={file} style={{
                            padding: '6px 12px 6px 42px',
                            color: 'var(--text-secondary)',
                            fontSize: '0.9rem'
                        }}>
                            📄 {file}
                        </div>
                    ))}
                </div>

                <div style={{ marginTop: '20px', display: 'flex', justifyContent: 'flex-end', gap: '12px' }}>
                    <button
                        onClick={onClose}
                        style={{
                            padding: '10px 20px',
                            borderRadius: '6px',
                            border: '1px solid var(--border-color)',
                            background: 'transparent',
                            color: 'var(--text-primary)',
                            cursor: 'pointer'
                        }}
                    >
                        Cancel
                    </button>
                    <button
                        onClick={() => onSelect(currentPath)}
                        style={{
                            padding: '10px 20px',
                            borderRadius: '6px',
                            border: 'none',
                            background: 'var(--accent-color)',
                            color: 'white',
                            cursor: 'pointer',
                            fontWeight: 'bold'
                        }}
                    >
                        Select This Folder
                    </button>
                </div>
            </div>
        </div>
    );
};

export default DirectoryBrowser;
