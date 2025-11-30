import React, { useRef, useEffect, useImperativeHandle, forwardRef } from 'react';
import { Chart, registerables } from 'chart.js';
import { Line } from 'react-chartjs-2';
import zoomPlugin from 'chartjs-plugin-zoom';
import { useStore } from '../store';

// Register Chart.js components
Chart.register(...registerables, zoomPlugin);

const Plot = forwardRef(({ nodes, edges }, ref) => {
  console.log("Plot component rendering", { nodesCount: nodes?.length, edgesCount: edges?.length });
  const mode = useStore(state => state.mode);
  const handleNodeClick = useStore(state => state.handleNodeClick);
  const performOperation = useStore(state => state.performOperation);
  const selectedNodeIds = useStore(state => state.selectedNodeIds);
  const operationStartNodeId = useStore(state => state.operationStartNodeId);
  const smoothingPreview = useStore(state => state.smoothingPreview);
  const drawPoints = useStore(state => state.drawPoints);
  const addDrawPoint = useStore(state => state.addDrawPoint);
  const pointSize = useStore(state => state.pointSize);

  const chartRef = useRef(null);
  const lastDrawnNodeId = useRef(null);

  // Expose methods to parent
  useImperativeHandle(ref, () => ({
    resetZoom: () => {
      if (chartRef.current) {
        chartRef.current.resetZoom();
      }
    },
    togglePan: () => {
      // Implementation depends on how we want to toggle. 
      // For now, we might just rely on default behavior or toggle plugin options if needed.
      // Chart.js zoom plugin usually has pan enabled by default if configured.
      console.log("Pan toggled (placeholder)");
    },
    toggleZoom: () => {
      console.log("Zoom toggled (placeholder)");
    }
  }));

  useEffect(() => {
    // Reset last drawn node when switching out of draw mode
    if (mode !== 'draw') {
      lastDrawnNodeId.current = null;
    }
  }, [mode]);

  // Performance Optimization: Prepare edge data for a single dataset
  const edgeData = [];
  if (nodes && edges) {
    const nodeMap = new Map(nodes.map(n => [n[0], n]));
    edges.forEach(edge => {
      const fromNode = nodeMap.get(edge[0]);
      const toNode = nodeMap.get(edge[1]);
      if (fromNode && toNode) {
        edgeData.push({ x: fromNode[1], y: fromNode[2] });
        edgeData.push({ x: toNode[1], y: toNode[2] });
        // Add a break in the line using NaN
        edgeData.push({ x: NaN, y: NaN });
      }
    });
  }

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
        data: nodes ? nodes.map(node => ({ x: node[1], y: node[2], id: node[0] })) : [],
        backgroundColor: nodes ? nodes.map(node => {
          if (selectedNodeIds.includes(node[0])) return 'red';
          if (operationStartNodeId === node[0]) return 'blue';
          return 'rgba(75,192,192,1)';
        }) : [],
        pointRadius: pointSize, // Use dynamic point size
        pointHitRadius: 15, // Increased hit radius for easier selection
        type: 'scatter',
      },

      // Smoothing Preview
      ...(smoothingPreview ? [{
        label: 'Smooth Preview',
        data: smoothingPreview.points.map(p => ({ x: p[0], y: p[1] })),
        borderColor: 'rgba(0, 0, 255, 0.7)',
        borderWidth: 2,
        borderDash: [5, 5],
        pointRadius: 0,
        showLine: true,
        type: 'line',
        spanGaps: false,
      }] : []),

      // Draw Preview (Temporary Points)
      ...(drawPoints && drawPoints.length > 0 ? [{
        label: 'Draw Preview',
        data: drawPoints,
        borderColor: 'rgba(0, 0, 0, 0.5)', // Semi-transparent black
        borderWidth: 2,
        pointRadius: 3,
        pointBackgroundColor: 'rgba(0, 0, 0, 0.5)',
        showLine: true,
        type: 'line',
        spanGaps: false,
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
          // Ctrl + Right Click = Delete Points
          performOperation('delete_points', { point_ids: [nodeId] });
        } else {
          // Right Click = Break Links
          performOperation('break_links', { point_id: nodeId });
        }
      }
    }
  };

  const findNearestNode = (x, y) => {
    if (!nodes || nodes.length === 0) return null;
    let minDist = Infinity;
    let nearestNodeId = null;

    nodes.forEach(node => {
      const dx = node[1] - x;
      const dy = node[2] - y;
      const dist = Math.sqrt(dx * dx + dy * dy);
      if (dist < minDist) {
        minDist = dist;
        nearestNodeId = node[0];
      }
    });
    return nearestNodeId;
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
        addDrawPoint({ x: xData, y: yData });
      } else {
        if (elements.length > 0) {
          const element = elements[0];
          if (element.datasetIndex === 1) { // Nodes dataset
            const nodeId = nodes[element.index][0];
            handleNodeClick(nodeId);
          }
        } else if (event.ctrlKey || event.metaKey) {
          // Quick Action: Add Node and Connect to Nearest
          const nearestNodeId = findNearestNode(xData, yData);
          if (nearestNodeId !== null) {
            performOperation('add_node', { x: xData, y: yData, lane_id: 0, connect_to: nearestNodeId });
          }
        }
      }
    },
    plugins: {
      legend: { display: false },
      tooltip: {
        callbacks: {
          label: function (context) {
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
});

export default Plot;