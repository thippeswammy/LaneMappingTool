import React from 'react';

const Toolbar = ({
    onDelete,
    onUndo,
    onRedo,
    onSave,
    onAddEdge,
    selectionCount,
    pointSize,
    setPointSize,
    smoothness,
    setSmoothness
}) => {
    return (
        <>
            <div className="section">
                <h4>History</h4>
                <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '10px' }}>
                    <button onClick={onUndo}>Undo</button>
                    <button onClick={onRedo}>Redo</button>
                </div>
            </div>

            <div className="section">
                <h4>File</h4>
                <button className="primary" onClick={onSave}>Save Changes</button>
            </div>

            <div className="section">
                <h4>Edit</h4>
                <button
                    className="danger"
                    onClick={onDelete}
                    disabled={selectionCount === 0}
                >
                    Delete Selected ({selectionCount})
                </button>

                <button
                    onClick={onAddEdge}
                    disabled={selectionCount !== 2}
                    title="Select exactly 2 nodes to connect"
                >
                    Add Edge ({selectionCount === 2 ? 'Ready' : 'Select 2'})
                </button>
            </div>

            <div className="section">
                <h4>View Settings</h4>
                <div className="slider-container">
                    <label>
                        Point Size
                        <span>{pointSize}px</span>
                    </label>
                    <input
                        type="range"
                        min="1"
                        max="20"
                        value={pointSize}
                        onChange={(e) => setPointSize(parseInt(e.target.value))}
                    />
                </div>
                <div className="slider-container">
                    <label>
                        Smoothness
                        <span>{smoothness}</span>
                    </label>
                    <input
                        type="range"
                        min="0.1"
                        max="5.0"
                        step="0.1"
                        value={smoothness}
                        onChange={(e) => setSmoothness(parseFloat(e.target.value))}
                    />
                </div>
            </div>

            <div className="section">
                <h4>Instructions</h4>
                <div className="instructions">
                    <div><b>Pan:</b> Click & Drag</div>
                    <div><b>Zoom:</b> Scroll</div>
                    <div><b>Select:</b> Click node</div>
                    <div><b>Multi-Select:</b> Shift+Click</div>
                    <div><b>Add Node:</b> Click empty space</div>
                    <div><b>Delete:</b> Del / Backspace</div>
                </div>
            </div>
        </>
    );
};

export default Toolbar;
