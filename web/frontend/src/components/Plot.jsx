import React, { useRef, useEffect } from 'react';
import { Chart, registerables } from 'chart.js';
import { Line } from 'react-chartjs-2';
import zoomPlugin from 'chartjs-plugin-zoom';
import { useStore } from '../store';

// Register Chart.js components
Chart.register(...registerables, zoomPlugin);

const Plot = ({ nodes, edges }) => {
  const {
    mode,
    handleNodeClick,
    performOperation,
    selectedNodeIds,
    operationStartNodeId,
    smoothingPreview
  } = useStore(state => ({
    mode: state.mode,
    handleNodeClick: state.handleNodeClick,
    performOperation: state.performOperation,
    selectedNodeIds: state.selectedNodeIds,
    operationStartNodeId: state.operationStartNodeId,
    smoothingPreview: state.smoothingPreview
  }));

  const chartRef = useRef(null);
  const lastDrawnNodeId = useRef(null);

  useEffect(() => {
    // Reset last drawn node when switching out of draw mode
    if (mode !== 'draw') {
      lastDrawnNodeId.current = null;
    }
  }, [mode]);

  // Performance Optimization: Prepare edge data for a single dataset
  const edgeData = [];
  const nodeMap = new Map(nodes.map(n => [n[0], n]));
  edges.forEach(edge => {
    const fromNode = nodeMap.get(edge[0]);
    const toNode = nodeMap.get(edge[1]);
    if (fromNode && toNode) {
      edgeData.push({ x: fromNode[1], y: fromNode[2] });
      edgeData.push({ x: toNode[1], y: toNode[2] });
      // Add a null data point to create a break in the line
      edgeData.push(null);
    }
  });

  const chartData = {
    datasets: [
      // Edges (single dataset for performance)
      {
        label: 'Edges',
        data: edgeData,
        borderColor: 'rgba(0, 0, 0, 0.2)',
        borderWidth: 1,
        pointRadius: 0,
        showLine: true,
        type: 'line',
        spanGaps: false, // Important for showing breaks
      },

      // Nodes
      {
        label: 'Nodes',
        data: nodes.map(node => ({ x: node[1], y: node[2], id: node[0] })),
        backgroundColor: nodes.map(node => {
          if (selectedNodeIds.includes(node[0])) return 'red';
          if (operationStartNodeId === node[0]) return 'blue';
          return 'rgba(75,192,192,1)';
        }),
        pointRadius: 5,
        type: 'scatter',
      },

      // Smoothing Preview
      ...(smoothingPreview ? [{
        label: 'Smooth Preview',
        data: smoothingPreview.points.map(p => ({x: p[0], y: p[1]})),
        borderColor: 'rgba(0, 0, 255, 0.7)',
        borderWidth: 2,
        borderDash: [5, 5],
        pointRadius: 0,
        showLine: true,
        type: 'line',
      }] : []),
    ]
  };

  const handleCanvasContextMenu = (event) => {
    event.preventDefault();
    const chart = chartRef.current;
    if (!chart) return;

    const elements = chart.getElementsAtEventForMode(event, 'nearest', { intersect: true }, true);

    if (elements.length > 0) {
      const element = elements[0];
      if (element.datasetIndex === 1) { // Nodes dataset
        const nodeId = nodes[element.index][0];

        if (event.ctrlKey || event.metaKey) {
          performOperation('break_links', { point_id: nodeId });
        } else {
          performOperation('delete_points', { point_ids: [nodeId] });
        }
      }
    }
  };

  const options = {
    responsive: true,
    maintainAspectRatio: false,
    onClick: async (event, elements) => {
      const chart = chartRef.current;
      if (!chart) return;

      const canvas = chart.canvas;
      const rect = canvas.getBoundingClientRect();
      const x = event.clientX - rect.left;
      const y = event.clientY - rect.top;
      const xScale = chart.scales.x;
      const yScale = chart.scales.y;
      const xData = xScale.getValueForPixel(x);
      const yData = yScale.getValueForPixel(y);

      if (mode === 'draw') {
        const connectToId = lastDrawnNodeId.current;
        await performOperation('add_node', {
          x: xData,
          y: yData,
          lane_id: 0, // Default lane_id for now
          connect_to: connectToId
        });
        const newNodes = useStore.getState().nodes;
        if (newNodes.length > nodes.length) {
          const newNode = newNodes.reduce((latest, current) => (current[0] > latest[0] ? current : latest), newNodes[0]);
          lastDrawnNodeId.current = newNode[0];
        }
      } else {
        if (elements.length > 0) {
          const element = elements[0];
          if (element.datasetIndex === 1) { // Nodes dataset
            const nodeId = nodes[element.index][0];
            handleNodeClick(nodeId);
          }
        }
      }
    },
    plugins: {
      legend: { display: false },
      tooltip: {
        callbacks: {
          label: function(context) {
            if (context.dataset.label === 'Nodes') {
              const point = context.raw;
              return `Node ID: ${point.id} (X: ${point.x.toFixed(2)}, Y: ${point.y.toFixed(2)})`;
            }
            return null;
          }
        }
      },
      zoom: {
        pan: {
          enabled: true,
          mode: 'xy',
        },
        zoom: {
          wheel: { enabled: true },
          pinch: { enabled: true },
          mode: 'xy',
        }
      }
    },
    scales: {
      x: { type: 'linear', position: 'bottom' },
      y: { type: 'linear' }
    }
  };

  return (
    <div
      className="plot-container"
      style={{ position: 'relative', height: '100%', width: '100%' }}
      onContextMenu={handleCanvasContextMenu}
    >
      <Line ref={chartRef} data={chartData} options={options} />
    </div>
  );
};

export default Plot;