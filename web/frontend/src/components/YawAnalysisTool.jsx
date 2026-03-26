import React, { useEffect, useMemo, useState } from 'react';
import { useStore } from '../store';
import {
    Chart as ChartJS,
    CategoryScale,
    LinearScale,
    PointElement,
    LineElement,
    Title,
    Tooltip,
    Legend,
} from 'chart.js';
import { Line } from 'react-chartjs-2';

ChartJS.register(
    CategoryScale,
    LinearScale,
    PointElement,
    LineElement,
    Title,
    Tooltip,
    Legend
);

const YawAnalysisTool = () => {
    const analyzeYaw = useStore(state => state.analyzeYaw);
    const applyYawFix = useStore(state => state.applyYawFix);
    const result = useStore(state => state.yawAnalysisResult);
    const isAnalyzing = useStore(state => state.isAnalyzingYaw);
    const focusOnNode = useStore(state => state.focusOnNode);

    // 'yaw', 'curvature', 'diff'
    const [chartMode, setChartMode] = useState('yaw');

    const chartData = useMemo(() => {
        if (!result || !result.profile) return null;

        const { ids, yaws, curvatures, diffs } = result.profile;

        let labels = ids;
        let data = [];
        let label = '';
        let color = '';

        // Simple decimation
        if (ids.length > 2000) {
            labels = ids.filter((_, i) => i % 5 === 0);
        }

        if (chartMode === 'yaw') {
            data = ids.length > 2000 ? yaws.filter((_, i) => i % 5 === 0) : yaws;
            label = 'Yaw (rad)';
            color = 'rgb(53, 162, 235)';
        } else if (chartMode === 'curvature') {
            data = ids.length > 2000 ? curvatures.filter((_, i) => i % 5 === 0) : curvatures;
            label = 'Curvature';
            color = 'rgb(255, 99, 132)';
        } else if (chartMode === 'diff') {
            data = ids.length > 2000 ? diffs.filter((_, i) => i % 5 === 0) : diffs;
            label = 'Yaw Diff';
            color = 'rgb(75, 192, 192)';
        }

        return {
            labels: labels,
            datasets: [
                {
                    label: label,
                    data: data,
                    borderColor: color,
                    backgroundColor: color.replace('rgb', 'rgba').replace(')', ', 0.5)'),
                    pointRadius: 1,
                    borderWidth: 1,
                },
            ],
        };
    }, [result, chartMode]);

    const options = {
        responsive: true,
        plugins: {
            legend: {
                position: 'top',
            },
            title: {
                display: true,
                text: chartMode.charAt(0).toUpperCase() + chartMode.slice(1) + ' Profile',
            },
        },
        scales: {
            x: {
                display: false
            }
        },
        maintainAspectRatio: false
    };

    return (
        <div style={{ padding: '10px', height: '100%', display: 'flex', flexDirection: 'column' }}>
            <h3 style={{ marginTop: 0, marginBottom: '10px' }}>Yaw Analysis</h3>

            <div style={{ marginBottom: '15px', display: 'flex', gap: '10px' }}>
                <button
                    onClick={analyzeYaw}
                    disabled={isAnalyzing}
                    className="toolbar-button"
                    style={{ flex: 1, justifyContent: 'center' }}
                >
                    {isAnalyzing ? 'Analyzing...' : 'Run Analysis'}
                </button>

                {result && result.anomalies.length > 0 && (
                    <button
                        onClick={applyYawFix}
                        disabled={isAnalyzing}
                        className="toolbar-button confirm"
                        style={{ flex: 1, justifyContent: 'center' }}
                    >
                        Fix {result.anomalies.length} Issues
                    </button>
                )}
            </div>

            {result && (
                <div style={{ marginBottom: '10px', fontSize: '0.9rem', flex: 1, display: 'flex', flexDirection: 'column', minHeight: 0 }}>
                    <div><strong>Total Nodes:</strong> {result.total_nodes}</div>
                    <div style={{ color: result.anomalies.length > 0 ? '#ff6b6b' : '#51cf66' }}>
                        <strong>Anomalies:</strong> {result.anomalies.length}
                    </div>

                    {result.anomalies.length > 0 && (
                        <div style={{
                            marginTop: '5px',
                            flex: 1,
                            overflowY: 'auto',
                            background: 'rgba(0,0,0,0.2)',
                            borderRadius: '4px',
                            marginBottom: '10px'
                        }}>
                            {result.anomalies.map((a, i) => (
                                <div
                                    key={i}
                                    style={{
                                        padding: '5px',
                                        borderBottom: '1px solid rgba(255,255,255,0.1)',
                                        cursor: 'pointer',
                                        fontSize: '0.8rem'
                                    }}
                                    className="anomaly-item"
                                    onClick={() => focusOnNode(a.id)}
                                    title="Click to jump to node"
                                >
                                    <span style={{ color: '#4dabf7', fontWeight: 'bold' }}>#{a.id}</span>
                                    <span style={{ marginLeft: '5px', color: a.type === 'ZERO_DIFF' ? '#ff922b' : '#ff6b6b' }}>
                                        {a.type}
                                    </span>
                                    <div style={{ fontSize: '0.7em', opacity: 0.7 }}>{a.info}</div>
                                </div>
                            ))}
                        </div>
                    )}
                </div>
            )}

            {result && (
                <div style={{ display: 'flex', gap: '5px', marginBottom: '5px' }}>
                    {['yaw', 'curvature', 'diff'].map(m => (
                        <button
                            key={m}
                            onClick={() => setChartMode(m)}
                            className={`toolbar-button ${chartMode === m ? 'active' : ''}`}
                            style={{ padding: '2px 8px', fontSize: '0.8rem' }}
                        >
                            {m.charAt(0).toUpperCase() + m.slice(1)}
                        </button>
                    ))}
                </div>
            )}

            {chartData && (
                <div style={{ height: '200px', background: 'white', borderRadius: '4px', padding: '5px', flexShrink: 0 }}>
                    <Line options={options} data={chartData} />
                </div>
            )}

            <div style={{ marginTop: '10px', fontSize: '0.8rem', color: '#aaa', fontStyle: 'italic' }}>
                Note: Fixes key is in-memory. <strong>Save Data</strong> to persist.
            </div>

            <style jsx>{`
                .anomaly-item:hover {
                    background-color: rgba(255, 255, 255, 0.1);
                }
            `}</style>
        </div>
    );
};

export default YawAnalysisTool;
