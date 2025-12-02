import React, { useRef, useEffect, useImperativeHandle, forwardRef, useCallback, useMemo } from 'react';
import { Chart, registerables } from 'chart.js';
import { Line } from 'react-chartjs-2';
import zoomPlugin from 'chartjs-plugin-zoom';
import { useStore } from '../store';

// Register Chart.js components
Chart.register(...registerables, zoomPlugin);

const Plot = forwardRef(({ nodes, edges, width, height }, ref) => {
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

  // Refs for state access in callbacks to avoid re-creating options
  const nodesRef = useRef(nodes);
  const modeRef = useRef(mode);
  const selectedNodeIdsRef = useRef(selectedNodeIds);
  const performOperationRef = useRef(performOperation);
  const handleNodeClickRef = useRef(handleNodeClick);
  const addDrawPointRef = useRef(addDrawPoint);

  // Persistent bounds to prevent axis shrinking
  const boundsRef = useRef({ minX: Infinity, maxX: -Infinity, minY: Infinity, maxY: -Infinity });

  // Synchronously update bounds based on current nodes to ensure options are stable
  if (nodes && nodes.length > 0) {
    let { minX, maxX, minY, maxY } = boundsRef.current;
    let updated = false;

    nodes.forEach(node => {
      if (node[1] < minX) { minX = node[1]; updated = true; }
      if (node[1] > maxX) { maxX = node[1]; updated = true; }
      if (node[2] < minY) { minY = node[2]; updated = true; }
      if (node[2] > maxY) { maxY = node[2]; updated = true; }
    });

    if (updated) {
      boundsRef.current = { minX, maxX, minY, maxY };
    }
  }

  // Extract current bounds for useMemo dependencies
  const { minX, maxX, minY, maxY } = boundsRef.current;

  // Update refs on render
  useEffect(() => {
    nodesRef.current = nodes;
    modeRef.current = mode;
    selectedNodeIdsRef.current = selectedNodeIds;
    performOperationRef.current = performOperation;
    handleNodeClickRef.current = handleNodeClick;
    addDrawPointRef.current = addDrawPoint;
  }, [nodes, mode, selectedNodeIds, performOperation, handleNodeClick, addDrawPoint]);

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
      console.log("Pan toggled (placeholder)");
    },
    toggleZoom: () => {
      console.log("Zoom toggled (placeholder)");
    }
  }));

  useEffect(() => {
    if (mode !== 'draw') {
      lastDrawnNodeId.current = null;
    }
  }, [mode]);

  // Imperatively update chart bounds
  useEffect(() => {
    const chart = chartRef.current;
    if (chart) {
      chart.options.scales.x.suggestedMin = minX !== Infinity ? minX : undefined;
      chart.options.scales.x.suggestedMax = maxX !== -Infinity ? maxX : undefined;
      chart.options.scales.y.suggestedMin = minY !== Infinity ? minY : undefined;
      chart.options.scales.y.suggestedMax = maxY !== -Infinity ? maxY : undefined;
      chart.update('none');
    }
  }, [minX, maxX, minY, maxY]);

  // Performance Optimization: Prepare edge data
  const chartData = useMemo(() => {
    const edgeData = [];
    if (nodes && edges) {
      const nodeMap = new Map(nodes.map(n => [n[0], n]));
      edges.forEach(edge => {
        const fromNode = nodeMap.get(edge[0]);
        const toNode = nodeMap.get(edge[1]);
        if (fromNode && toNode) {
          edgeData.push({ x: fromNode[1], y: fromNode[2] });
          edgeData.push({ x: toNode[1], y: toNode[2] });
          edgeData.push({ x: NaN, y: NaN });
        }
      });
    }

    return {
      datasets: [
        {
          label: 'Edges',
          data: edgeData,
          borderColor: 'rgba(200, 200, 200, 0.8)',
          borderWidth: 1,
          pointRadius: 0,
          showLine: true,
          type: 'line',
          spanGaps: false,
        },
        {
          label: 'Nodes',
          data: nodes ? nodes.map(node => ({ x: node[1], y: node[2], id: node[0] })) : [],
          backgroundColor: nodes ? nodes.map(node => {
            if (selectedNodeIds.includes(node[0])) return 'red';
            if (operationStartNodeId === node[0]) return 'blue';
            return 'rgba(0,255,255,1)';
          }) : [],
          pointRadius: pointSize,
          pointHitRadius: 10,
          type: 'scatter',
        },
        ...(smoothingPreview ? [{
          label: 'Smooth Preview',
          data: smoothingPreview.map(p => ({ x: p[1], y: p[2] })),
          borderColor: 'rgba(255, 0, 0, 1)',
          borderWidth: 2,
          borderDash: [10, 3],
          pointRadius: 0,
          showLine: true,
          type: 'line',
          spanGaps: false,
        }] : []),
        ...(drawPoints && drawPoints.length > 0 ? [{
          label: 'Draw Preview',
          data: drawPoints,
          borderColor: 'rgba(255, 255, 255, 0.8)',
          borderWidth: 2,
          pointRadius: 3,
          pointBackgroundColor: 'rgba(255, 255, 255, 0.8)',
          showLine: true,
          type: 'line',
          spanGaps: false,
        }] : []),
      ]
    };
  }, [nodes, edges, selectedNodeIds, operationStartNodeId, smoothingPreview, drawPoints, pointSize]);

  const handleCanvasContextMenu = useCallback((event) => {
    event.preventDefault();
    const chart = chartRef.current;
    if (!chart) return;

    const elements = chart.getElementsAtEventForMode(event, 'nearest', { intersect: true }, true);

    if (elements.length > 0) {
      const element = elements[0];
      if (element.datasetIndex === 1) { // Nodes dataset
        const currentNodes = nodesRef.current;
        const nodeId = currentNodes[element.index][0];

        if (event.ctrlKey || event.metaKey) {
          performOperationRef.current('delete_points', { point_ids: [nodeId] });
        } else {
          performOperationRef.current('break_links', { point_id: nodeId });
        }
      }
    }
  }, []);

  const findNearestNode = useCallback((x, y) => {
    const currentNodes = nodesRef.current;
    if (!currentNodes || currentNodes.length === 0) return null;
    let minDist = Infinity;
    let nearestNode = null;

    currentNodes.forEach(node => {
      const dx = node[1] - x;
      const dy = node[2] - y;
      const dist = Math.sqrt(dx * dx + dy * dy);
      if (dist < minDist) {
        minDist = dist;
        nearestNode = node;
      }
    });
    return { node: nearestNode, dist: minDist };
  }, []);

  // Native Click Handler passed to the Line component (which renders the canvas)
  const handleCanvasClick = useCallback((event) => {
    const chart = chartRef.current;
    if (!chart) return;

    // We use the native event or the React synthetic event.
    // React synthetic event has .nativeEvent, but properties like clientX are on the synthetic event too.
    // event.button === 0 is Left Click.

    const rect = chart.canvas.getBoundingClientRect();
    const x = event.clientX - rect.left;
    const y = event.clientY - rect.top;

    const xScale = chart.scales.x;
    const yScale = chart.scales.y;
    const xData = xScale.getValueForPixel(x);
    const yData = yScale.getValueForPixel(y);

    const currentMode = modeRef.current;

    console.log("Canvas Click (Native):", {
      button: event.button,
      ctrlKey: event.ctrlKey,
      metaKey: event.metaKey,
      xData, yData,
      mode: currentMode
    });

    if (currentMode === 'draw') {
      addDrawPointRef.current({ x: xData, y: yData });
    } else {
      // Check if we clicked on an existing element using Chart.js helper
      // We need to use the native event for getElementsAtEventForMode if possible, 
      // or just pass the synthetic event which Chart.js handles.
      const elements = chart.getElementsAtEventForMode(event.nativeEvent || event, 'nearest', { intersect: true }, true);

      if (elements.length > 0) {
        const element = elements[0];
        if (element.datasetIndex === 1) { // Nodes dataset
          const currentNodes = nodesRef.current;
          const nodeId = currentNodes[element.index][0];
          // Normal click on node -> Select
          // Shift + Click -> Multi-select (handled in handleNodeClick)
          handleNodeClickRef.current(nodeId, event.shiftKey);
          return;
        }
      }

      // If no element clicked, check for Ctrl + Click (Add Node)
      // Explicitly check for Left Click (button 0) and Ctrl key
      if (event.button === 0 && (event.ctrlKey || event.metaKey)) {
        const result = findNearestNode(xData, yData);
        const CONNECTION_THRESHOLD = 5.0;

        if (result && result.node && result.dist < CONNECTION_THRESHOLD) {
          const nearestNode = result.node;
          const nearestNodeId = nearestNode[0];
          const zone = nearestNode[4];
          performOperationRef.current('add_node', { x: xData, y: yData, lane_id: zone, connect_to: nearestNodeId });
        } else {
          performOperationRef.current('add_node', { x: xData, y: yData, lane_id: 0, connect_to: null });
        }
      }
    }
  }, [findNearestNode]);

  const options = useMemo(() => ({
    responsive: true,
    animation: false,
    maintainAspectRatio: false,
    // We handle onClick natively on the canvas now
    events: ['mousemove', 'mouseout', 'click', 'touchstart', 'touchmove'], // Ensure click is listened to by Chart.js for tooltips etc if needed, but we have our own handler
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
      x: {
        type: 'linear',
        position: 'bottom',
        grid: { color: '#444' },
        ticks: { color: '#aaa' }
      },
      y: {
        type: 'linear',
        position: 'left',
        grid: { color: '#444' },
        ticks: { color: '#aaa' }
      }
    }
  }), []);

  return (
    <div
      className="plot-container"
      style={{ position: 'relative', height: height, width: width }}
      onContextMenu={handleCanvasContextMenu}
    >
      <Line
        ref={chartRef}
        data={chartData}
        options={options}
        onClick={handleCanvasClick}
      />
    </div>
  );
});

export default Plot;
