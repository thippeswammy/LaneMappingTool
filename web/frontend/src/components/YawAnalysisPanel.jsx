
import React, { useMemo, useState } from 'react';
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
import { IconCheck, IconGraph } from './Icons';

ChartJS.register(
    CategoryScale,
    LinearScale,
    PointElement,
    LineElement,
    Title,
    Tooltip,
    Legend
);

const YawAnalysisPanel = () => {
    const analyzeYaw = useStore(state => state.analyzeYaw);
    const applyYawFix = useStore(state => state.applyYawFix);
    const result = useStore(state => state.yawAnalysisResult);
    const isAnalyzing = useStore(state => state.isAnalyzingYaw);
    const focusOnNode = useStore(state => state.focusOnNode);

    // Multi-chart layout
    // We want three charts stacked: Yaw, Curvature, Diff

    // Helper to generate chart data
    const getChartData = (label, dataPoints, color) => {
        if (!result || !result.profile) return null;
        const { ids } = result.profile;

        let labels = ids;
        let data = dataPoints;

        // Decimate if too many points for performance
        if (ids.length > 3000) {
            labels = ids.filter((_, i) => i % 5 === 0);
            data = dataPoints.filter((_, i) => i % 5 === 0);
        }

        return {
            labels: labels,
            datasets: [
                {
                    label: label,
                    data: data,
                    borderColor: color,
                    backgroundColor: color.replace('rgb', 'rgba').replace(')', ', 0.5)'),
                    pointRadius: 0, // Hide points for clean line
                    borderWidth: 1.5,
                    tension: 0.1, // Slight curve
                },
            ],
        };
    };

    const yawData = useMemo(() => result ? getChartData('Yaw (rad)', result.profile.yaws, 'rgb(53, 162, 235)') : null, [result]);
    const curvData = useMemo(() => result ? getChartData('Curvature', result.profile.curvatures, 'rgb(255, 99, 132)') : null, [result]);
    const diffData = useMemo(() => result ? getChartData('Yaw Diff', result.profile.diffs, 'rgb(75, 192, 192)') : null, [result]);

    const commonOptions = {
        responsive: true,
        plugins: {
            legend: { position: 'top', labels: { boxWidth: 10, font: { size: 10 } } },
            title: { display: false },
            tooltip: {
                mode: 'index',
                intersect: false,
            }
        },
        scales: {
            x: { display: false }, // Hide X axis for cleanliness
            y: {
                grid: { color: 'rgba(255, 255, 255, 0.1)' },
                ticks: { color: '#aaa', font: { size: 9 } }
            }
        },
        maintainAspectRatio: false,
        element: {
            point: { radius: 0 }
        }
    };

    return (
        <div className="yaw-analysis-panel" style={{
            height: '100%',
            display: 'flex',
            flexDirection: 'column',
            background: '#1e1e1e', // Darker background for contrast
            color: '#eee',
            borderLeft: '1px solid var(--border-color)'
        }}>
            {/* Header / Controls */}
            <div style={{ padding: '15px', borderBottom: '1px solid var(--border-color)', display: 'flex', alignItems: 'center', justifyContent: 'space-between', background: 'var(--bg-secondary)' }}>
                <h3 style={{ margin: 0, display: 'flex', alignItems: 'center', gap: '10px' }}>
                    <IconGraph size={20} /> Yaw Analysis
                </h3>
                <div style={{ display: 'flex', gap: '10px' }}>
                    <button
                        onClick={analyzeYaw}
                        disabled={isAnalyzing}
                        className="toolbar-button"
                        style={{ padding: '6px 12px' }}
                    >
                        {isAnalyzing ? 'Analyzing...' : 'Run Analysis'}
                    </button>
                    {result && result.anomalies.length > 0 && (
                        <button
                            onClick={applyYawFix}
                            disabled={isAnalyzing}
                            className="toolbar-button confirm"
                            style={{ padding: '6px 12px' }}
                        >
                            <IconCheck size={14} style={{ marginRight: '5px' }} />
                            Fix {result.anomalies.length} Issues
                        </button>
                    )}
                </div>
            </div>

            {/* Content Area */}
            <div style={{ flex: 1, overflowY: 'auto', padding: '15px', display: 'flex', flexDirection: 'column', gap: '20px' }}>

                {/* Stats */}
                {result && (
                    <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '10px' }}>
                        <div style={{ background: 'var(--bg-tertiary)', padding: '10px', borderRadius: '4px', textAlign: 'center' }}>
                            <div style={{ fontSize: '0.8rem', color: '#aaa' }}>Total Nodes</div>
                            <div style={{ fontSize: '1.2rem', fontWeight: 'bold' }}>{result.total_nodes}</div>
                        </div>
                        <div style={{ background: 'var(--bg-tertiary)', padding: '10px', borderRadius: '4px', textAlign: 'center' }}>
                            <div style={{ fontSize: '0.8rem', color: '#aaa' }}>Anomalies</div>
                            <div style={{ fontSize: '1.2rem', fontWeight: 'bold', color: result.anomalies.length > 0 ? '#ff6b6b' : '#51cf66' }}>
                                {result.anomalies.length}
                            </div>
                        </div>
                    </div>
                )}

                {/* Charts */}
                {result && (
                    <div style={{ display: 'flex', flexDirection: 'column', gap: '10px', minHeight: '400px' }}>
                        <div style={{ flex: 1, minHeight: '120px', background: 'var(--bg-tertiary)', borderRadius: '4px', padding: '5px' }}>
                            <Line options={commonOptions} data={yawData} />
                        </div>
                        <div style={{ flex: 1, minHeight: '120px', background: 'var(--bg-tertiary)', borderRadius: '4px', padding: '5px' }}>
                            <Line options={commonOptions} data={curvData} />
                        </div>
                        <div style={{ flex: 1, minHeight: '120px', background: 'var(--bg-tertiary)', borderRadius: '4px', padding: '5px' }}>
                            <Line options={commonOptions} data={diffData} />
                        </div>
                    </div>
                )}

                {/* Anomalies List */}
                {result && result.anomalies.length > 0 && (
                    <div style={{ flex: 1, minHeight: '200px', display: 'flex', flexDirection: 'column' }}>
                        <h4 style={{ marginTop: 0, marginBottom: '10px', color: '#aaa' }}>Anomalies</h4>
                        <div style={{
                            flex: 1,
                            maxHeight: '300px', // Limit height but allow scroll
                            overflowY: 'auto',
                            background: 'var(--bg-tertiary)',
                            borderRadius: '4px',
                            border: '1px solid var(--border-color)'
                        }}>
                            <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: '0.85rem' }}>
                                <thead style={{ background: 'var(--bg-secondary)', position: 'sticky', top: 0 }}>
                                    <tr>
                                        <th style={{ padding: '8px', textAlign: 'left' }}>ID</th>
                                        <th style={{ padding: '8px', textAlign: 'left' }}>Type</th>
                                        <th style={{ padding: '8px', textAlign: 'left' }}>Info</th>
                                    </tr>
                                </thead>
                                <tbody>
                                    {result.anomalies.map((a, i) => (
                                        <tr
                                            key={i}
                                            onClick={() => focusOnNode(a.id)}
                                            style={{ cursor: 'pointer', borderBottom: '1px solid var(--border-color)', transition: 'background 0.2s' }}
                                            className="anomaly-row"
                                        >
                                            <td style={{ padding: '8px', color: '#4dabf7' }}>#{a.id}</td>
                                            <td style={{ padding: '8px', color: a.type === 'ZERO_DIFF' ? '#ff922b' : '#ff6b6b' }}>{a.type}</td>
                                            <td style={{ padding: '8px', color: '#aaa' }}>{a.info}</td>
                                        </tr>
                                    ))}
                                </tbody>
                            </table>
                        </div>
                    </div>
                )}

                {!result && (
                    <div style={{ flex: 1, display: 'flex', alignItems: 'center', justifyContent: 'center', color: '#666', flexDirection: 'column', gap: '15px' }}>
                        <IconGraph size={48} style={{ opacity: 0.2 }} />
                        <div>Click "Run Analysis" to begin.</div>
                    </div>
                )}
            </div>

            <style jsx>{`
                .anomaly-row:hover {
                    background-color: rgba(255, 255, 255, 0.05);
                }
            `}</style>
        </div>
    );
};

export default YawAnalysisPanel;
